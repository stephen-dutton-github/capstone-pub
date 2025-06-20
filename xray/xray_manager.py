import os
import tensorflow as tf
from keras import layers, models
from keras.preprocessing import image
import numpy as np

class ChestXRayClassifier:
    def __init__(self, data_dir, model_save_path='/app/chest_xray_model.h5', image_size=(224, 224), batch_size=32):
        self.data_dir = data_dir
        self.model_save_path = model_save_path
        self.image_size = image_size
        self.batch_size = batch_size

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

        class_names = train_ds.class_names
        print('Classes found:', class_names)

        AUTOTUNE = tf.data.experimental.AUTOTUNE
        train_ds = train_ds.prefetch(buffer_size=AUTOTUNE)
        val_ds = val_ds.prefetch(buffer_size=AUTOTUNE)

        return train_ds, val_ds, len(class_names)

    def build_model(self, num_classes):
        model = models.Sequential([
            layers.Rescaling(1./255, input_shape=self.image_size + (3,)),
            layers.Conv2D(32, (3, 3), activation='relu'),
            layers.MaxPooling2D(),
            layers.Conv2D(64, (3, 3), activation='relu'),
            layers.MaxPooling2D(),
            layers.Conv2D(128, (3, 3), activation='relu'),
            layers.MaxPooling2D(),
            layers.Flatten(),
            layers.Dense(128, activation='relu'),
            layers.Dropout(0.4),
            layers.Dense(num_classes, activation='softmax')
        ])

        model.compile(
            optimizer='adam',
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )

        model.summary()
        return model

    def train_and_save_model(self, epochs=10):
        train_ds, val_ds, num_classes = self.load_data()
        model = self.build_model(num_classes)

        model.fit(
            train_ds,
            validation_data=val_ds,
            epochs=epochs
        )

        model.save(self.model_save_path)
        print(f'Model saved at {self.model_save_path}')
    
    
    def load_model(self, model_path):
        """Loads a full Keras model from an .h5 file."""
        self.model = tf.keras.models.load_model(model_path)
        print(f"Model loaded from {model_path}")

        # Attempt to load class names if not already set
        if not self.class_names:
            try:
                train_ds, _, _ = self.load_data()
                self.class_names = train_ds.class_names
            except:
                print("Warning: class_names not set and data_dir is unavailable.")

    def predict(self, image_path):
        """Predicts the class of a single image using the loaded model."""
        if not hasattr(self, 'model') or self.model is None:
            raise ValueError("Model not loaded. Call `load_model()` first.")

        # Load and preprocess the image
        img = tf.keras.preprocessing.image.load_img(image_path, target_size=self.image_size)
        img_array = tf.keras.preprocessing.image.img_to_array(img)
        img_array = tf.expand_dims(img_array, 0)  # Add batch dimension
        img_array = img_array / 255.0  # Normalize

        # Predict
        predictions = self.model.predict(img_array)
        predicted_class_idx = tf.argmax(predictions[0]).numpy()

        if self.class_names:
            predicted_class = self.class_names[predicted_class_idx]
        else:
            predicted_class = f"Class {predicted_class_idx}"

        confidence = predictions[0][predicted_class_idx]
        return predicted_class, confidence


# Usage Example
if __name__ == '__main__':
    import tensorflow as tf
    print(tf.__version__)
    print(tf.config.list_physical_devices('GPU'))
    data_directory = '/app/cxr/'
    classifier = ChestXRayClassifier(data_dir=data_directory)
    classifier.class_names =['Covid', 'Normal', 'Pneumonia', 'Tuberculosis']
    classifier.load_model('/app/chest_xray_model.h5')
    for item in ['./test_covid.jpg', './test_normal.jpg','./test_pneumonia.jpg','./test_tuberculosis.jpg']:
        p_class,confidence = classifier.predict(item)
        print(f"{item} is of class is a {p_class}, with a {confidence} confidence level\n")

