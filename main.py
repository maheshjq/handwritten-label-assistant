from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from enum import Enum
from PIL import Image
import requests
import base64
import io
import re
import logging
import os
import json
from typing import Dict, Any, List, Optional
from config import DEFAULT_MODEL, OLLAMA_API_URL, RECOGNITION_PROMPT

# Setup logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize the FastAPI app
app = FastAPI(title="Handwritten Label AI Assistant",
              description="An API for recognizing handwritten text in images using Ollama",
              version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define Ollama model options as an Enum for Swagger dropdown
class ModelName(str, Enum):
    llava = DEFAULT_MODEL  # "llava:latest"
    bakllava = "bakllava:latest"
    llava_13b = "llava:13b"
    llava_7b = "llava:7b"

# Pydantic models for response
class OCRResult(BaseModel):
    full_text: str
    structured_data: Dict[str, Any]
    confidence_score: float = 0.0

class Transcription(BaseModel):
    text: str

class IntegrationData(BaseModel):
    transcription: str

# Prompt template for Ollama
def get_recognition_prompt():
    return RECOGNITION_PROMPT

def recognize_handwriting_with_ollama(image_data, model_name="llava:latest"):
    """
    Recognize handwritten text in an image using a multimodal LLM through Ollama
    
    Args:
        image_data: Binary image data
        model_name: Name of the multimodal model in Ollama
    
    Returns:
        dict: Recognition results with extracted text and confidence
    """
    # Encode the image to base64
    base64_image = base64.b64encode(image_data).decode("utf-8")
    
    # Get the prompt
    prompt = get_recognition_prompt()
    
    # Set up the API request
    payload = {
        "model": model_name,
        "prompt": prompt,
        "images": [base64_image],
        "stream": False,
        "format": "json"  # Request JSON output if the model supports it
    }
    
    logger.info(f"Sending request to Ollama with model: {model_name}")
    
    # Send the request to Ollama
    try:
        response = requests.post(OLLAMA_API_URL, json=payload)
        response.raise_for_status()
        
        result = response.json()
        response_text = result.get("response", "{}")
        
        # Try to parse the response as JSON
        try:
            parsed_response = json.loads(response_text)
            
            # Ensure we have the expected keys
            if "text" not in parsed_response:
                parsed_response["text"] = response_text
            
            if "confidence" not in parsed_response:
                parsed_response["confidence"] = 0.8  # Default confidence
            else:
                # Convert percentage to decimal if needed
                if isinstance(parsed_response["confidence"], (int, float)) and parsed_response["confidence"] > 1:
                    parsed_response["confidence"] /= 100
            
            if "structured_data" not in parsed_response:
                parsed_response["structured_data"] = extract_structured_data(parsed_response["text"])
                
            return parsed_response
            
        except json.JSONDecodeError:
            # If LLM doesn't return JSON, parse the text response
            logger.warning("Failed to parse JSON response, falling back to text parsing")
            
            # Extract text and confidence through simple parsing
            extracted_text = response_text
            confidence = 0.8  # Default confidence
            
            # Try to extract confidence if mentioned
            confidence_match = re.search(r"confidence.*?(\d+)", response_text, re.IGNORECASE)
            if confidence_match:
                try:
                    confidence = float(confidence_match.group(1)) / 100
                except ValueError:
                    pass
            
            # Extract structured data
            structured_data = extract_structured_data(extracted_text)
            
            return {
                "text": extracted_text,
                "confidence": confidence,
                "structured_data": structured_data
            }
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Error connecting to Ollama: {e}")
        raise HTTPException(status_code=500, detail=f"Ollama API error: {str(e)}")

def extract_structured_data(text):
    """
    Extract structured data from recognized text
    
    Args:
        text: Recognized text
    
    Returns:
        dict: Structured data extracted from text
    """
    structured_data = {}
    
    # Extract item ID if present
    item_id_patterns = [
        r"Item\s*ID:?\s*(\w+)",
        r"ItemID:?\s*(\w+)",
        r"ID:?\s*(\w+)",
        r"Item\s*Number:?\s*(\w+)"
    ]
    
    # Extract location if present
    location_patterns = [
        r"Location:?\s*([\w\s\-]+)",
        r"Loc:?\s*([\w\s\-]+)",
        r"Place:?\s*([\w\s\-]+)",
        r"Section:?\s*([\w\s\-]+)"
    ]
    
    # Try each pattern until we find a match
    for pattern in item_id_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            structured_data["ItemID"] = match.group(1)
            break
    
    for pattern in location_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            structured_data["Location"] = match.group(1).strip()
            break
    
    return structured_data

# Health check endpoint
@app.get("/health")
def health_check():
    """Verify that the server is running."""
    return {"status": "healthy"}

# Root endpoint
@app.get("/")
def read_root():
    """Welcome message for the root URL."""
    return {"message": "Welcome to the Handwritten Label AI Assistant using Ollama!"}

# Handwriting recognition endpoint
@app.post("/recognize", response_model=OCRResult)
async def recognize_handwriting(
    file: UploadFile = File(...),
    model_name: ModelName = Query(ModelName.llava, description="Ollama model to use")
):
    """
    Recognize handwritten text in an image using Ollama.
    
    Args:
        file (UploadFile): The image file to process.
        model_name (ModelName): The Ollama model to use.
    
    Returns:
        OCRResult: The recognized text and structured data.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        # Read the image file
        contents = await file.read()
        
        # Process with Ollama
        result = recognize_handwriting_with_ollama(contents, model_name)
        
        # Prepare response
        return OCRResult(
            full_text=result.get("text", ""),
            structured_data=result.get("structured_data", {}),
            confidence_score=result.get("confidence", 0.0)
        )
        
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Validation endpoint
@app.post("/validate")
async def validate_transcription(transcription: Transcription):
    """
    Validate the transcription text.
    """
    # Extract structured data
    structured_data = extract_structured_data(transcription.text)
    
    # Check if required fields are present
    is_valid = "ItemID" in structured_data
    
    return {
        "valid": is_valid,
        "structured_data": structured_data
    }

# Integration endpoint (placeholder)
@app.post("/integrate")
async def integrate_data(data: IntegrationData):
    """
    Integrate validated data into an inventory system (placeholder).
    """
    # Extract structured data
    structured_data = extract_structured_data(data.transcription)
    
    # In a real system, you would save this to a database
    return {
        "message": "Integration successful",
        "data": structured_data
    }

# Local testing function
def handwritten_label_assistant(image_path, model_name=ModelName.llava):
    """
    Process a handwritten label image locally.
    
    Args:
        image_path (str): Path to the image file.
        model_name (str): Name of the Ollama model to use.
    
    Returns:
        dict: Recognition results.
    """
    logger.info(f"Processing image: {image_path}")
    
    # Read the image file
    with open(image_path, "rb") as image_file:
        image_data = image_file.read()
    
    # Process with Ollama
    result = recognize_handwriting_with_ollama(image_data, model_name)
    
    # Log results
    logger.info(f"Generated text: {result.get('text', '')} (confidence: {result.get('confidence', 0):.2f})")
    logger.info(f"Structured data: {result.get('structured_data', {})}")
    
    return result

# Run locally if executed directly
if __name__ == "__main__":
    import json
    
    # Import missing modules
    try:
        import json
    except ImportError:
        logger.error("Missing required module: json")
        exit(1)
    
    # Specify image path for local testing
    sample_image_path = "label_image.png"
    
    # Check if the file exists
    if not os.path.exists(sample_image_path):
        logger.error(f"File not found: {sample_image_path}")
        print(f"\nError: The file '{sample_image_path}' doesn't exist.")
        print("Please specify a valid image path by editing the 'sample_image_path' variable.")
        exit(1)
    
    # Process the image
    try:
        result = handwritten_label_assistant(sample_image_path)
    
        # Print results
        print("\nRecognition Results:")
        print(f"Text: {result.get('text', '')}")
        print(f"Confidence: {result.get('confidence', 0):.2f}")
        
        # Print structured data
        print("\nStructured Data:")
        if result.get('structured_data', {}):
            for key, value in result.get('structured_data', {}).items():
                print(f"{key}: {value}")
        else:
            print("No structured data found")
            
        # Print full text if no structured data
        if not result.get('structured_data', {}):
            print(f"\nFull Text: {result.get('text', '')}")
    except Exception as e:
        logger.error(f"Error in local testing: {str(e)}")
        print(f"\nError: {str(e)}")
        print("\nTips for troubleshooting:")
        print("1. Make sure Ollama is installed and running")
        print("2. Check that you have pulled the model (e.g., 'ollama pull llava:latest')")
        print("3. Verify that the image file exists and is a supported format")