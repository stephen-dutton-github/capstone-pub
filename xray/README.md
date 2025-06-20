# XRay Diagnostic Service

This service provides a REST API for chest x-ray image classification, supporting automated diagnosis of pulmonary conditions such as COVID-19, Pneumonia, and Tuberculosis. It is built using **FastAPI** and leverages a TensorFlow-based convolutional neural network (CNN) model.

## Service Overview

### Entry Point: `app.py`

This module initializes a FastAPI server with the following key endpoints:

- `GET /heartbeat`: Returns a health-check response with a timestamp.
- `POST /predict`: Accepts an image upload (JPEG or PNG), processes it, and returns the predicted class and confidence.

The classifier is initialized globally to avoid reloading the model on every request. Supported image classes include:
- Covid
- Normal
- Pneumonia
- Tuberculosis

Prediction results are returned in JSON format with fields:
```json
{
  "predicted_class": "Pneumonia",
  "confidence": 0.9342
}
```

### Key Logic:
- Temporary storage is used for image files via `NamedTemporaryFile`.
- File type is validated before processing.
- Model is loaded using the `ChestXRayClassifier` from `xray_manager.py`.

---

## Model Management: `xray_manager.py`

This module defines the `ChestXRayClassifier` class which encapsulates all functionality for training, loading, and running inference with a Keras CNN.

### Features

#### Initialization
```python
ChestXRayClassifier(data_dir='/app/cxr/', model_save_path='/app/chest_xray_model.h5')
```
- `data_dir`: Directory for training images organized by class.
- `model_save_path`: Path where the trained model is saved.

#### Methods

- `load_data()`: Loads training and validation datasets using `image_dataset_from_directory` with 80/20 split.
- `build_model(num_classes)`: Constructs a CNN with 3 convolution layers and dropout, compiled for classification.
- `train_and_save_model(epochs=10)`: Trains the model and saves it to disk.
- `load_model(path)`: Loads a pre-trained model from `.h5` file.
- `predict(image_path)`: Predicts the class of a given image, returning both class label and confidence.

### Model Architecture
The model includes:
- Rescaling Layer (Normalization)
- 3 Convolutional + MaxPooling layers
- Flatten + Dense layers
- Dropout Regularization
- Softmax Output for multi-class prediction

---

## Running the Service

Use the following command to run the FastAPI app:

```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

Or if the `app.py` file is run directly:

```bash
python app.py
```

Ensure that the model file `chest_xray_model_v3.h5` and image directory `/app/cxr/` are mounted properly in your container or local environment.

---

## Inputs and Constraints

- Accepts: `image/jpeg`, `image/jpg`, `image/png`
- Rejects: All other MIME types with HTTP 400
- Temporary image files are cleaned after prediction

---

## Example Files (for Testing)

You may use these samples in the root directory:
- `test_covid.jpg`
- `test_normal.jpg`
- `test_pneumonia.jpg`
- `test_tuberculosis.jpg`

These can be tested via the `predict()` method directly or sent via HTTP POST to the service.

---

## Notes

- GPU acceleration is supported via TensorFlow backend.
- Training can be done offline using `train_and_save_model()` with a labeled dataset.
- Class names are inferred from training directory or manually set.