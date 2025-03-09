from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from PIL import Image, ImageOps, ImageEnhance, ImageFilter
import torch
import numpy as np
import re
import os
import tempfile
import cv2
import io
import logging
from typing import Optional, List
from enum import Enum


# Define a ModelSize enum class
class ModelSize(str, Enum):
    small = "small"
    base = "base"
    large = "large"
    
    
# Setup logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize the FastAPI app
app = FastAPI(title="Handwritten Label AI Assistant",
              description="An API for recognizing handwritten text in images",
              version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define OCR model options
MODEL_OPTIONS = {
    "base": "microsoft/trocr-base-handwritten",
    "large": "microsoft/trocr-large-handwritten",
    "small": "microsoft/trocr-small-handwritten"
}

# Default to the large model for better accuracy
DEFAULT_MODEL = "large"

# Initialize processor and model (lazy loading on first request)
processor = None
model = None

def load_model(model_size="large"):
    """
    Lazy-load the TrOCR model and processor.
    Args:
        model_size (str): Size of the model to load ("base", "large", or "small")
    """
    global processor, model
    
    if model_size not in MODEL_OPTIONS:
        model_size = DEFAULT_MODEL
        
    model_name = MODEL_OPTIONS[model_size]
    logger.info(f"Loading model: {model_name}")
    
    try:
        processor = TrOCRProcessor.from_pretrained(model_name, use_fast=True)
        model = VisionEncoderDecoderModel.from_pretrained(model_name)
        
        # Move model to GPU if available
        if torch.cuda.is_available():
            model = model.to("cuda")
            logger.info("Model loaded on GPU")
        else:
            logger.info("Model loaded on CPU")
    except Exception as e:
        logger.error(f"Error loading model: {str(e)}")
        raise Exception(f"Failed to load OCR model: {str(e)}")

# Pydantic models for request bodies
class Transcription(BaseModel):
    text: str

class IntegrationData(BaseModel):
    transcription: str

class OCRResult(BaseModel):
    full_text: str
    structured_data: dict
    confidence_score: float = 0.0
    preprocessing_applied: List[str] = []

# Image preprocessing functions
def preprocess_image(image, preprocessing_options=None):
    """
    Apply various preprocessing techniques to improve OCR accuracy.
    
    Args:
        image (PIL.Image): The input image.
        preprocessing_options (dict): Options for preprocessing.
    
    Returns:
        (PIL.Image, list): Preprocessed image and list of applied techniques.
    """
    if preprocessing_options is None:
        preprocessing_options = {
            "resize": True,
            "contrast_enhancement": True,
            "grayscale": True,
            "binarization": True,
            "noise_reduction": True,
            "deskew": True
        }
    
    applied_techniques = []
    
    # Convert to grayscale if requested
    if preprocessing_options.get("grayscale", True):
        image = ImageOps.grayscale(image)
        applied_techniques.append("grayscale")
    
    # Apply contrast enhancement if requested
    if preprocessing_options.get("contrast_enhancement", True):
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)  # Increase contrast
        applied_techniques.append("contrast_enhancement")
    
    # Resize the image if requested (helps with model input requirements)
    if preprocessing_options.get("resize", True):
        # Resize while maintaining aspect ratio
        max_size = 1000
        ratio = max_size / max(image.size)
        new_size = tuple([int(x * ratio) for x in image.size])
        image = image.resize(new_size, Image.LANCZOS)
        applied_techniques.append("resize")
    
    # Apply binarization if requested
    if preprocessing_options.get("binarization", True):
        # Convert PIL image to OpenCV format
        opencv_image = np.array(image)
        
        # Apply adaptive thresholding
        if len(opencv_image.shape) == 2:  # Grayscale
            _, binary_image = cv2.threshold(
                opencv_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
            )
        else:  # Color
            gray = cv2.cvtColor(opencv_image, cv2.COLOR_RGB2GRAY)
            _, binary_image = cv2.threshold(
                gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
            )
        
        # Convert back to PIL
        image = Image.fromarray(binary_image)
        applied_techniques.append("binarization")
    
    # Apply noise reduction if requested
    if preprocessing_options.get("noise_reduction", True):
        image = image.filter(ImageFilter.MedianFilter(size=3))
        applied_techniques.append("noise_reduction")
    
    # Apply deskewing if requested
    if preprocessing_options.get("deskew", True):
        # Convert PIL image to OpenCV format
        opencv_image = np.array(image)
        
        # OpenCV expects a grayscale image for deskewing
        if len(opencv_image.shape) == 3:
            opencv_image = cv2.cvtColor(opencv_image, cv2.COLOR_RGB2GRAY)
        
        # Calculate skew angle
        coords = np.column_stack(np.where(opencv_image > 0))
        angle = cv2.minAreaRect(coords)[-1]
        
        # Adjust the angle
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
        
        # Only deskew if angle is significant
        if abs(angle) > 0.5:
            (h, w) = opencv_image.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            rotated = cv2.warpAffine(
                opencv_image, M, (w, h), 
                flags=cv2.INTER_CUBIC, 
                borderMode=cv2.BORDER_REPLICATE
            )
            
            # Convert back to PIL
            image = Image.fromarray(rotated)
            applied_techniques.append("deskew")
    
    return image, applied_techniques

# TrOCR processing functions
def process_with_trocr(image, model_size="large"):
    """
    Process an image with TrOCR model.
    
    Args:
        image (PIL.Image): The preprocessed image.
        model_size (str): The model size to use.
    
    Returns:
        (str, float): Recognized text and confidence score.
    """
    global processor, model
    
    # Lazy loading of model
    if processor is None or model is None:
        load_model(model_size)
    
    # Make sure image is RGB
    if image.mode != "RGB":
        image = image.convert("RGB")
    
    # Process image
    pixel_values = processor(image, return_tensors="pt").pixel_values
    
    # Move to GPU if available
    if torch.cuda.is_available():
        pixel_values = pixel_values.to("cuda")
    
    # Generate text with beam search for better results
    generated_ids = model.generate(
        pixel_values,
        max_length=128,
        num_beams=5,
        early_stopping=True
    )
    
    # Decode the generated text
    generated_text = processor.batch_decode(
        generated_ids,
        skip_special_tokens=True
    )[0]
    
    # Calculate a simple confidence score based on token probabilities
    # (this is a simplified approximation)
    with torch.no_grad():
        outputs = model(pixel_values, generated_ids)
        logits = outputs.logits
        probabilities = torch.softmax(logits, dim=-1)
        token_probs = torch.max(probabilities, dim=-1).values
        confidence_score = float(torch.mean(token_probs).cpu().numpy())
    
    return generated_text, confidence_score

# Post-processing function
def post_process_text(text):
    """
    Extract structured data from recognized text.
    
    Args:
        text (str): Recognized text.
    
    Returns:
        dict: Structured data extracted from text.
    """
    # Basic cleaning
    cleaned_text = " ".join(text.split()).strip()
    
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
        match = re.search(pattern, cleaned_text, re.IGNORECASE)
        if match:
            structured_data["ItemID"] = match.group(1)
            break
    
    for pattern in location_patterns:
        match = re.search(pattern, cleaned_text, re.IGNORECASE)
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
    return {"message": "Welcome to the Handwritten Label AI Assistant!"}

# Handwriting recognition endpoint
@app.post("/recognize", response_model=OCRResult)
async def recognize_handwriting(
    file: UploadFile = File(...),
    model_size: ModelSize = Query(ModelSize.large, description="Model size to use"),
    apply_contrast: bool = Query(True, description="Apply contrast enhancement"),
    apply_binarization: bool = Query(True, description="Apply binarization"),
    apply_noise_reduction: bool = Query(True, description="Apply noise reduction"),
    apply_deskew: bool = Query(True, description="Apply deskewing")
):
    """
    Recognize handwritten text in an image.
    
    Args:
        file (UploadFile): The image file to process.
        model_size (ModelSize): The TrOCR model size to use.
        apply_* (bool): Image preprocessing options.
    
    Returns:
        OCRResult: The recognized text and structured data.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        # Read the image file
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")
        
        # Set preprocessing options
        preprocessing_options = {
            "resize": True,
            "contrast_enhancement": apply_contrast,
            "grayscale": True,
            "binarization": apply_binarization,
            "noise_reduction": apply_noise_reduction,
            "deskew": apply_deskew
        }
        
        # Preprocess the image
        preprocessed_image, applied_techniques = preprocess_image(
            image, preprocessing_options
        )
        
        # Process with TrOCR
        text, confidence_score = process_with_trocr(
            preprocessed_image, model_size
        )
        
        # Extract structured data
        structured_data = post_process_text(text)
        
        # Prepare response
        return OCRResult(
            full_text=text,
            structured_data=structured_data,
            confidence_score=confidence_score,
            preprocessing_applied=applied_techniques
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
    structured_data = post_process_text(transcription.text)
    
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
    structured_data = post_process_text(data.transcription)
    
    # In a real system, you would save this to a database
    return {
        "message": "Integration successful",
        "data": structured_data
    }

# Local testing function
def handwritten_label_assistant(image_path, model_size=DEFAULT_MODEL):
    """
    Process a handwritten label image locally.
    
    Args:
        image_path (str): Path to the image file.
        model_size (str): Size of the model to use.
    
    Returns:
        dict: Recognition results.
    """
    logger.info(f"Processing image: {image_path}")
    
    # Open and preprocess the image
    image = Image.open(image_path).convert("RGB")
    preprocessed_image, applied_techniques = preprocess_image(image)
    
    # Process with TrOCR
    text, confidence_score = process_with_trocr(preprocessed_image, model_size)
    logger.info(f"Generated text: {text} (confidence: {confidence_score:.2f})")
    
    # Extract structured data
    structured_data = post_process_text(text)
    logger.info(f"Structured data: {structured_data}")
    
    return {
        "full_text": text,
        "structured_data": structured_data,
        "confidence_score": confidence_score,
        "preprocessing_applied": applied_techniques
    }

# Run locally if executed directly
if __name__ == "__main__":
    # Specify image path for local testing
    sample_image_path = "label_image.png"
    
    # Process the image
    result = handwritten_label_assistant(sample_image_path)
    
    # Print results
    print("\nRecognition Results:")
    print(f"Text: {result['full_text']}")
    print(f"Confidence: {result['confidence_score']:.2f}")
    print(f"Preprocessing: {', '.join(result['preprocessing_applied'])}")
    
    # Print structured data
    print("\nStructured Data:")
    if result['structured_data']:
        for key, value in result['structured_data'].items():
            print(f"{key}: {value}")
    else:
        print("No structured data found")
    
    # Print full text if no structured data
    if not result['structured_data']:
        print(f"\nFull Text: {result['full_text']}")