# Handwritten Label AI Assistant

A FastAPI application that recognizes and extracts structured data from handwritten labels using a Transformer-based OCR model.

## Features

- 📝 Handwritten text recognition using the Microsoft TrOCR model
- 🔍 Structure extraction from recognized text (e.g., ItemID, Location)
- 🌐 Simple API endpoints for integration with inventory systems
- 💻 Local processing capability for testing

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

## Usage

### Starting the API Server

Run the following command to start the FastAPI server:
```
uvicorn main:app --reload
```

The server will be available at `http://127.0.0.1:8000`.

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
Accepts an image file and returns structured data extracted from the handwritten text.

**Example using curl:**
```
curl -X POST "http://127.0.0.1:8000/recognize" -F "file=@path/to/your/image.jpg"
```

**Example Response:**
```json
{
  "ItemID": "ABC123",
  "Location": "Shelf 5"
}
```

#### Validation
```
POST /validate
```
Validates the transcription text format.

#### Integration
```
POST /integrate
```
Integrates validated data into an inventory system (placeholder endpoint).

### API Documentation

FastAPI automatically generates interactive API documentation. After starting the server, visit:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Local Testing

You can also test the handwritten label recognition locally without using the API by modifying the `sample_image_path` in the main script:

```python
if __name__ == "__main__":
    sample_image_path = "path/to/your/label_image.png"
    result = handwritten_label_assistant(sample_image_path)
```

Then run:
```
python main.py
```

## License

[MIT License](LICENSE)

## Acknowledgements

- This project uses the [Microsoft TrOCR model](https://huggingface.co/microsoft/trocr-base-handwritten) for handwritten text recognition.
- Built with [FastAPI](https://fastapi.tiangolo.com/) and [HuggingFace Transformers](https://huggingface.co/transformers/).