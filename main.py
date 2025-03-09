from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from PIL import Image
import torch
import re
import os
import tempfile

# Initialize the FastAPI app
app = FastAPI()

# Step 1: Load the pre-trained TrOCR model and processor once at startup
# Fixed the typo in model name (troch -> trocr) and added use_fast=True parameter
processor = TrOCRProcessor.from_pretrained("microsoft/trocr-base-handwritten", use_fast=True)
model = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-base-handwritten")

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

# Pydantic models for request bodies
class Transcription(BaseModel):
    text: str

class IntegrationData(BaseModel):
    transcription: str

# Step 2: Preprocess the image
def preprocess_image(image: Image.Image):
    """
    Preprocess the image for the TrOCR model.
    Args:
        image (PIL.Image): The image to preprocess.
    Returns:
        Processed image tensor ready for the model.
    """
    pixel_values = processor(image, return_tensors="pt").pixel_values  # Shape: [1, channels, height, width]
    return pixel_values

# Step 3: Generate text from the image
def generate_text(pixel_values):
    """
    Generate text from the processed image using the TrOCR model.
    Args:
        pixel_values (torch.Tensor): Preprocessed image tensor.
    Returns:
        Generated text transcription.
    """
    # Generate text (autoregressive decoding)
    generated_ids = model.generate(pixel_values, max_length=50)
    
    # Decode the generated token IDs into text
    generated_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
    return generated_text

# Step 4: Post-process the generated text
def post_process_text(text):
    """
    Clean and structure the generated text for inventory management.
    Args:
        text (str): Raw text output from the model.
    Returns:
        Dictionary with structured data (e.g., item ID, location).
    """
    # Basic cleaning: remove extra spaces and normalize
    cleaned_text = " ".join(text.split()).strip()
    
    # Example: Assume label format is "ItemID: ABC123 Location: Shelf 5"
    structured_data = {}
    
    # Use regex to extract key information
    item_id_match = re.search(r"ItemID:\s*(\w+)", cleaned_text, re.IGNORECASE)
    location_match = re.search(r"Location:\s*([\w\s]+)", cleaned_text, re.IGNORECASE)
    
    if item_id_match:
        structured_data["ItemID"] = item_id_match.group(1)
    if location_match:
        structured_data["Location"] = location_match.group(1)
    
    return structured_data

# Image preprocessing endpoint
@app.post("/preprocess")
async def preprocess_image_endpoint(file: UploadFile = File(...)):
    """
    Accept an image file and preprocess it for handwriting recognition.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    try:
        # Save the uploaded image temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
            temp_file.write(await file.read())
            temp_file_path = temp_file.name
        
        # Open the image with PIL
        image = Image.open(temp_file_path).convert("RGB")
        
        # Preprocess the image
        pixel_values = preprocess_image(image)
        
        # Clean up the temporary file
        os.remove(temp_file_path)
        
        return {"message": "Image preprocessed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Handwriting recognition endpoint
@app.post("/recognize")
async def recognize_handwriting(file: UploadFile = File(...)):
    """
    Accept an image file, recognize handwriting using TrOCR, and return structured data.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    try:
        # Save the uploaded image temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
            temp_file.write(await file.read())
            temp_file_path = temp_file.name
        
        # Open the image with PIL
        image = Image.open(temp_file_path).convert("RGB")
        
        # Preprocess the image
        pixel_values = preprocess_image(image)
        
        # Generate text using TrOCR
        generated_text = generate_text(pixel_values)
        
        # Post-process the text to extract structured data
        structured_data = post_process_text(generated_text)
        
        # Clean up the temporary file
        os.remove(temp_file_path)
        
        return structured_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Validation endpoint (placeholder)
@app.post("/validate")
async def validate_transcription(transcription: Transcription):
    """
    Validate the transcription text (placeholder).
    """
    # Placeholder: Replace with actual validation logic (e.g., regex, rules)
    return {"valid": True}

# Integration endpoint (placeholder)
@app.post("/integrate")
async def integrate_data(data: IntegrationData):
    """
    Integrate validated data into an inventory system (placeholder).
    """
    # Placeholder: Replace with actual integration logic (e.g., database update)
    return {"message": "Integrated successfully"}

# Step 5: Main function to run the Handwritten Label AI Assistant (for local testing)
def handwritten_label_assistant(image_path):
    """
    Main function to process a handwritten label image and return structured data.
    Args:
        image_path (str): Path to the handwritten label image.
    Returns:
        Structured data dictionary with recognized information.
    """
    print(f"Processing image: {image_path}")
    
    # Open the image
    image = Image.open(image_path).convert("RGB")
    
    # Preprocess the image
    pixel_values = preprocess_image(image)
    
    # Generate text
    generated_text = generate_text(pixel_values)
    print(f"Generated text: {generated_text}")
    
    # Post-process the text
    structured_data = post_process_text(generated_text)
    print(f"Structured data: {structured_data}")
    
    return structured_data

# Example usage (runs only if the script is executed directly)
if __name__ == "__main__":
    # Replace with the path to your handwritten label image for local testing
    sample_image_path = "label_image.png"  # e.g., "label_image.jpg"
    
    # Run the assistant locally
    result = handwritten_label_assistant(sample_image_path)
    
    # Simulate integration with an inventory system (print for demo)
    if result:
        print("Integrating with inventory system:")
        print(f"Item ID: {result.get('ItemID', 'Not found')}")
        print(f"Location: {result.get('Location', 'Not found')}")