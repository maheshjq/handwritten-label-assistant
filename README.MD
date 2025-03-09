# Handwritten Label AI Assistant

An advanced FastAPI application that recognizes and extracts structured data from handwritten labels using a Transformer-based OCR model with enhanced preprocessing.

## Features

- 📝 High-accuracy handwritten text recognition using Microsoft TrOCR models
- 🔍 Intelligent structure extraction from recognized text (e.g., ItemID, Location)
- 🖼️ Advanced image preprocessing pipeline with multiple techniques
- 📊 Confidence scoring for recognition results
- 🔄 Support for multiple model sizes (small, base, large)
- 🌐 RESTful API endpoints with Swagger documentation
- 💻 Local testing capability for quick verification

## Prerequisites

- Python 3.8 or higher
- Virtual environment (recommended)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/handwritten-label-assistant.git
   cd handwritten-label-assistant
   ```

2. Create and activate a virtual environment:
   ```
   # Windows
   python -m venv label_vision_env
   .\label_vision_env\Scripts\activate

   # macOS/Linux
   python -m venv label_vision_env
   source label_vision_env/bin/activate
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

   Or install them manually:
   ```
   pip install fastapi uvicorn transformers torch torchvision Pillow opencv-python python-multipart
   ```

## Usage

### Starting the API Server

Run the following command to start the FastAPI server:
```
uvicorn main:app --reload
```

The server will be available at `http://127.0.0.1:8000`.

### API Documentation (Swagger UI)

FastAPI automatically generates interactive API documentation. After starting the server, visit:
```
http://127.0.0.1:8000/docs
```

This opens the Swagger UI where you can:
1. Explore all available endpoints
2. Test the API by uploading images
3. Adjust preprocessing parameters
4. View detailed response data

### API Endpoints

#### Health Check
```
GET /health
```
Verifies that the server is running properly.

#### Recognize Handwriting
```
POST /recognize
```
Accepts an image file and returns recognized text with structured data.

**Parameters:**
- `file`: The image file containing handwritten text
- `model_size`: Model size to use ("small", "base", or "large")
- `apply_contrast`: Whether to apply contrast enhancement
- `apply_binarization`: Whether to apply binarization
- `apply_noise_reduction`: Whether to apply noise reduction
- `apply_deskew`: Whether to automatically correct rotated text

**Example using curl:**
```
curl -X POST "http://127.0.0.1:8000/recognize" \
  -F "file=@path/to/your/image.jpg" \
  -F "model_size=large" \
  -F "apply_contrast=true"
```

**Example Response:**
```json
{
  "full_text": "This is a handwritten example. Write as good as you can.",
  "structured_data": {},
  "confidence_score": 0.92,
  "preprocessing_applied": ["grayscale", "contrast_enhancement", "resize", "noise_reduction"]
}
```

#### Other Endpoints
- `POST /validate`: Validates the transcription text format
- `POST /integrate`: Integrates validated data into an inventory system (placeholder)

### Local Testing

You can test the handwritten text recognition locally without using the API:

```
python main.py
```

This will:
1. Process the image specified in `sample_image_path` (default: "label_image.png")
2. Apply preprocessing techniques
3. Recognize text using the TrOCR model
4. Extract any structured data
5. Print detailed results

To test with a different image, edit the `sample_image_path` variable in `main.py`.

### Model Cache Location

The TrOCR models are downloaded from HuggingFace Transformers and cached locally. Default cache locations:

- **Windows**: `C:\Users\<username>\.cache\huggingface\hub`
- **macOS**: `/Users/<username>/.cache/huggingface/hub`
- **Linux**: `/home/<username>/.cache/huggingface/hub`

To specify a custom cache directory:

```
# Windows
set HF_HOME=D:\my_custom_models_directory
python main.py

# macOS/Linux
export HF_HOME=/path/to/custom/directory
python main.py
```

## Customization

### Adding New Preprocessing Techniques

Add new preprocessing methods to the `preprocess_image` function in `main.py`.

### Supporting Additional Structured Data

Extend the `post_process_text` function to extract more structured fields from recognized text.

### Using Different Models

You can add new models to the `MODEL_OPTIONS` dictionary in `main.py`.

## Performance Notes

- Using the "large" model provides the best accuracy but requires more memory
- GPU acceleration is automatically used if available
- For production use, consider deploying with multiple workers using Gunicorn or similar

## License

[MIT License](LICENSE)

## Acknowledgements

- This project uses the [Microsoft TrOCR models](https://huggingface.co/microsoft/trocr-base-handwritten) for handwritten text recognition
- Built with [FastAPI](https://fastapi.tiangolo.com/) and [HuggingFace Transformers](https://huggingface.co/transformers/)
- Image preprocessing powered by [OpenCV](https://opencv.org/) and [Pillow](https://python-pillow.org/)