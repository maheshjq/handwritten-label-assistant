"""
Image processing service for handling image preprocessing and analysis.
"""

import io
import base64
from typing import Dict, Any, Optional, Tuple
from PIL import Image, ImageOps, ImageEnhance, ImageFilter
import hashlib
import os
import logging

from app.config.settings import get_settings

# Initialize logger
logger = logging.getLogger(__name__)

def preprocess_image(
    image_data: bytes,
    enhance_contrast: bool = True,
    sharpen: bool = True,
    denoise: bool = True,
    resize_max_dimension: Optional[int] = 1024
) -> bytes:
    """
    Preprocess an image to improve recognition quality.
    
    Args:
        image_data: The raw image data
        enhance_contrast: Whether to enhance contrast
        sharpen: Whether to sharpen the image
        denoise: Whether to denoise the image
        resize_max_dimension: Maximum dimension for resizing, or None to keep original size
        
    Returns:
        bytes: Preprocessed image data
    """
    try:
        # Open the image
        with Image.open(io.BytesIO(image_data)) as img:
            # Convert to RGB mode if not already
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize if needed
            if resize_max_dimension is not None:
                # Calculate new dimensions while maintaining aspect ratio
                width, height = img.size
                if width > resize_max_dimension or height > resize_max_dimension:
                    if width > height:
                        new_width = resize_max_dimension
                        new_height = int(height * (resize_max_dimension / width))
                    else:
                        new_height = resize_max_dimension
                        new_width = int(width * (resize_max_dimension / height))
                    
                    img = img.resize((new_width, new_height), Image.LANCZOS)
            
            # Enhance contrast if requested
            if enhance_contrast:
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(1.5)  # Increase contrast by 50%
            
            # Sharpen if requested
            if sharpen:
                enhancer = ImageEnhance.Sharpness(img)
                img = enhancer.enhance(1.5)  # Increase sharpness by 50%
            
            # Denoise if requested
            if denoise:
                # Apply a slight blur to reduce noise, then sharpen to keep details
                img = img.filter(ImageFilter.GaussianBlur(0.5))
                img = img.filter(ImageFilter.SHARPEN)
            
            # Save the preprocessed image
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=95)
            return output.getvalue()
    
    except Exception as e:
        logger.error(f"Error preprocessing image: {str(e)}")
        # Return the original image if preprocessing fails
        return image_data

def extract_image_metadata(image_data: bytes) -> Dict[str, Any]:
    """
    Extract metadata from an image.
    
    Args:
        image_data: The image data
        
    Returns:
        Dict: Image metadata
    """
    try:
        with Image.open(io.BytesIO(image_data)) as img:
            metadata = {
                "format": img.format,
                "width": img.width,
                "height": img.height,
                "mode": img.mode,
                "size_kb": len(image_data) // 1024
            }
            
            # Extract EXIF data if available
            if hasattr(img, "_getexif") and img._getexif() is not None:
                exif = {}
                for tag, value in img._getexif().items():
                    exif[tag] = str(value)
                metadata["exif"] = exif
            
            return metadata
    except Exception as e:
        logger.error(f"Error extracting image metadata: {str(e)}")
        return {
            "error": str(e),
            "size_kb": len(image_data) // 1024
        }

def save_image(image_data: bytes, filename: Optional[str] = None) -> str:
    """
    Save an image to disk.
    
    Args:
        image_data: The image data
        filename: Optional filename, or None to generate one
        
    Returns:
        str: Path to the saved image
    """
    settings = get_settings()
    
    if not settings.ENABLE_STORAGE:
        raise ValueError("Storage is disabled in settings")
    
    # Create the storage directory if it doesn't exist
    images_dir = os.path.join(settings.STORAGE_PATH, "images")
    os.makedirs(images_dir, exist_ok=True)
    
    # Generate a filename if not provided
    if filename is None:
        image_hash = hashlib.md5(image_data).hexdigest()
        filename = f"{image_hash}.jpg"
    
    # Save the image
    image_path = os.path.join(images_dir, filename)
    with open(image_path, "wb") as f:
        f.write(image_data)
    
    return image_path

def load_image(image_path: str) -> bytes:
    """
    Load an image from disk.
    
    Args:
        image_path: Path to the image
        
    Returns:
        bytes: The image data
    """
    with open(image_path, "rb") as f:
        return f.read()

def hash_image(image_data: bytes) -> str:
    """
    Generate a hash for an image.
    
    Args:
        image_data: The image data
        
    Returns:
        str: Hash of the image
    """
    return hashlib.md5(image_data).hexdigest()

def encode_image_base64(image_data: bytes) -> str:
    """
    Encode an image as base64.
    
    Args:
        image_data: The image data
        
    Returns:
        str: Base64 encoded image
    """
    return base64.b64encode(image_data).decode("utf-8")

def decode_image_base64(base64_string: str) -> bytes:
    """
    Decode a base64 encoded image.
    
    Args:
        base64_string: Base64 encoded image
        
    Returns:
        bytes: The image data
    """
    return base64.b64decode(base64_string)