import tensorflow as tf
from keras import layers, models
from keras.preprocessing import image
import numpy as np
from collections import Counter
from datetime import datetime

class ChestXRayClassifier:
    def __init__(self, data_dir, model_save_path='/app/chest_xray_model_v3.h5', image_size=(1024, 1024), batch_size=16):
        self.data_dir = data_dir
        self.model_save_path = model_save_path
        self.image_size = image_size
        self.batch_size = batch_size
        # stop the CNN killing the LLM in Ollama (big problem)
        self._setup_gpu_memory()

    def _setup_gpu_memory(self):
        gpus = tf.config.list_physical_devices('GPU')
        if gpus:
            try:
                for gpu in gpus:
                    tf.config.experimental.set_memory_growth(gpu, True)
                logical_gpus = tf.config.list_logical_devices('GPU')
                print(len(gpus), "Physical GPUs,",
                      len(logical_gpus), "Logical GPUs with memory growth enabled")
            except RuntimeError as e:
                print("Error setting GPU memory growth:", e)

    def load_data(self):
        train_ds = tf.keras.preprocessing.image_dataset_from_directory(
            self.data_dir,
            validation_split=0.2,
            subset='training',
            seed=123,
            image_size=self.image_size,
            batch_size=self.batch_size
        )
        
        val_ds = tf.keras.preprocessing.image_dataset_from_directory(
            self.data_dir,
            validation_split=0.2,
            subset='validation',
            seed=123,
            image_size=self.image_size,
            batch_size=self.batch_size
        )

        self.class_names = train_ds.class_names
        print('Classes found:', self.class_names)

        AUTOTUNE = tf.data.experimental.AUTOTUNE
        train_ds = train_ds.prefetch(buffer_size=AUTOTUNE)
        val_ds = val_ds.prefetch(buffer_size=AUTOTUNE)

        return train_ds, val_ds, len(self.class_names)

    def build_model(self, num_classes):

        tf.keras.mixed_precision.set_global_policy('mixed_float16')
        base_model = tf.keras.applications.ResNet152V2(
            weights='imagenet', include_top=False, input_shape=self.image_size + (3,)
        )
        base_model.trainable = False

        model = models.Sequential([
            layers.Rescaling(1./255, input_shape=self.image_size + (3,)),
            layers.RandomFlip('horizontal'),
            layers.RandomRotation(0.1),
            layers.RandomZoom(0.1),
            base_model,
            layers.GlobalAveragePooling2D(),
            layers.Dropout(0.5),
            layers.Dense(1024, activation='relu'),   # 1st extra dense layer
            layers.Dropout(0.3),
            layers.Dense(512, activation='relu'),   # 2nd extra dense layer
            layers.Dropout(0.2),
            layers.Dense(num_classes, activation='softmax')
        ])

        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=1e-4),
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )

        model.summary()
        return model

    def calculate_class_weights(self, dataset):
        class_counts = Counter()
        for _, labels in dataset:
            class_counts.update(labels.numpy())

        total_images = sum(class_counts.values())
        class_weights = {i: total_images / (len(class_counts) * count)
                         for i, count in class_counts.items()}
        print('Class weights:', class_weights)
        return class_weights

    def train_and_save_model(self, epochs=40):
        train_ds, val_ds, num_classes = self.load_data()
        model = self.build_model(num_classes)

        class_weights = self.calculate_class_weights(train_ds)

        early_stopping = tf.keras.callbacks.EarlyStopping(
            monitor='val_loss', patience=5, restore_best_weights=True
        )

        model.fit(
            train_ds,
            validation_data=val_ds,
            epochs=epochs,
            class_weight=class_weights,
            callbacks=[early_stopping]
        )

        model.save(self.model_save_path)
        print(f'Model saved at {self.model_save_path}')

    def load_model(self, model_path):
        self.model = tf.keras.models.load_model(model_path)
        print(f"Model loaded from {model_path}")
        if not hasattr(self, 'class_names'):
            self.load_data()

    def predict(self, image_path):
        if not hasattr(self, 'model') or self.model is None:
            raise ValueError("Model not loaded. Call `load_model()` first.")

        img = tf.keras.preprocessing.image.load_img(image_path, target_size=self.image_size)
        img_array = tf.keras.preprocessing.image.img_to_array(img)
        img_array = tf.expand_dims(img_array, 0)
        img_array /= 255.0

        predictions = self.model.predict(img_array)
        predicted_class_idx = np.argmax(predictions[0])
        predicted_class = self.class_names[predicted_class_idx]
        confidence = predictions[0][predicted_class_idx]

        return predicted_class, confidence

    def unload_model(self):
        if hasattr(self, 'model'):
            del self.model
            self.model = None
            tf.keras.backend.clear_session()
            print("Model unloaded and TensorFlow session cleared.")



# Usage Example
if __name__ == '__main__':
    data_directory = '/app/cxr/'
    classifier = ChestXRayClassifier(data_dir=data_directory)
    
    now = datetime.now()

    # Print current time
    print("Start Time:", now.strftime("%H:%M:%S"))

    # Train and save model - 10 hours work
    classifier.train_and_save_model()

    # Load model for prediction
    classifier.class_names =['Covid', 'Normal', 'Pneumonia', 'Tuberculosis']
    classifier.load_model('/app/chest_xray_model_v3.h5')

    for item in ['./test_covid.jpg', './test_normal.jpg', './test_pneumonia.jpg', './test_tuberculosis.jpg']:
        p_class, confidence = classifier.predict(item)
        print(f"{item} classified as {p_class} with {confidence:.2%} confidence.")

    classifier.unload_model()

    # Get current date and time
    now = datetime.now()

    # Print current time
    print("End Time:", now.strftime("%H:%M:%S"))