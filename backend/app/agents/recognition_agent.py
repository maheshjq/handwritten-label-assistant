"""
Recognition agent for processing and analyzing handwritten labels.
Uses functional programming to maintain statelessness and predictability.
"""

from typing import Dict, Any, Optional, List, Tuple
import logging
from functools import lru_cache
import time

from app.services import llm_service, image_service, cache_service, storage_service
from app.config.settings import get_settings

# Initialize logger
logger = logging.getLogger(__name__)

def extract_structured_data_from_text(text: str) -> Dict[str, str]:
    """
    Extract structured data from recognized text.
    
    Args:
        text: The recognized text
        
    Returns:
        Dict: Extracted structured data
    """
    return llm_service.extract_structured_data(text)

def calculate_confidence(result: Dict[str, Any]) -> float:
    """
    Calculate a confidence score based on multiple factors.
    
    Args:
        result: The recognition result
        
    Returns:
        float: Calculated confidence score (0.0 to 1.0)
    """
    # Start with the base confidence from the model
    base_confidence = result.get("confidence", 0.5)
    
    # Convert percentage to decimal if needed
    if base_confidence > 1.0:
        base_confidence /= 100.0
    
    # Adjust based on amount of text extracted
    text = result.get("text", "")
    if len(text) < 10:
        base_confidence *= 0.8  # Penalize very short extractions
    
    # Adjust based on structured data extraction
    structured_data = result.get("structured_data", {})
    if structured_data:
        # More extracted fields generally means higher confidence
        field_bonus = min(len(structured_data) * 0.05, 0.2)
        base_confidence = min(base_confidence + field_bonus, 1.0)
    else:
        # Penalize if no structured data was extracted
        base_confidence *= 0.9
    
    # Ensure the confidence is in range [0.0, 1.0]
    return max(0.0, min(base_confidence, 1.0))

def recognize_handwriting_from_image(
    image_data: bytes,
    model_name: Optional[str] = None,
    preprocess: bool = True
) -> Dict[str, Any]:
    """
    Recognize handwriting from an image.
    
    Args:
        image_data: The image data
        model_name: Name of the model to use, or None for default
        preprocess: Whether to preprocess the image
        
    Returns:
        Dict: Recognition result with extracted text and structured data
    """
    settings = get_settings()
    
    # Generate image hash for caching and storage
    image_hash = image_service.hash_image(image_data)
    
    # Try to get from cache first
    cache_key = f"recognition_{image_hash}_{model_name or settings.DEFAULT_MODEL}"
    cached_result = cache_service.cache_get(cache_key)
    if cached_result:
        logger.info(f"Using cached recognition result for image {image_hash}")
        return cached_result
    
    # Preprocess the image if requested
    processed_image = image_service.preprocess_image(image_data) if preprocess else image_data
    
    # Use the LLM service to recognize handwriting
    try:
        model_to_use = model_name or settings.DEFAULT_MODEL
        result = llm_service.recognize_handwriting(processed_image, model_to_use)
        
        # Extract metadata from the image
        image_metadata = image_service.extract_image_metadata(image_data)
        
        # Ensure structured data is present
        if "structured_data" not in result or not result["structured_data"]:
            result["structured_data"] = extract_structured_data_from_text(result.get("text", ""))
        
        # Calculate and update confidence
        result["confidence"] = calculate_confidence(result)
        
        # Add metadata
        result["metadata"] = {
            "image_hash": image_hash,
            "model_name": model_to_use,
            "timestamp": time.time(),
            "image_info": image_metadata
        }
        
        # Save to cache
        cache_service.cache_set(cache_key, result)
        
        # Save to storage if enabled
        try:
            if settings.ENABLE_STORAGE:
                image_service.save_image(image_data, f"{image_hash}.jpg")
                storage_service.save_result(result, image_hash, model_to_use)
        except Exception as e:
            logger.error(f"Error saving recognition result: {str(e)}")
        
        return result
    
    except Exception as e:
        logger.error(f"Error recognizing handwriting: {str(e)}")
        raise RuntimeError(f"Failed to recognize handwriting: {str(e)}")

def evaluate_recognition_quality(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate the quality of a recognition result.
    
    Args:
        result: The recognition result
        
    Returns:
        Dict: Quality evaluation
    """
    text = result.get("text", "")
    confidence = result.get("confidence", 0.0)
    structured_data = result.get("structured_data", {})
    
    # Initialize quality metrics
    quality = {
        "overall_score": confidence,
        "needs_review": confidence < get_settings().CONFIDENCE_THRESHOLD,
        "issues": []
    }
    
    # Check for issues based on text content
    if len(text) < 10:
        quality["issues"].append("Very little text extracted")
    
    if not structured_data:
        quality["issues"].append("No structured data extracted")
    
    # Check for likely errors in the text
    if "???" in text or "..." in text:
        quality["issues"].append("Text contains uncertainty markers")
    
    # Adjust overall score based on issues
    quality["overall_score"] = max(0.0, quality["overall_score"] - (len(quality["issues"]) * 0.1))
    
    # Determine review status
    quality["needs_review"] = quality["overall_score"] < get_settings().CONFIDENCE_THRESHOLD or len(quality["issues"]) > 0
    
    return quality

def process_image(
    image_data: bytes,
    model_name: Optional[str] = None,
    preprocess: bool = True
) -> Dict[str, Any]:
    """
    Process an image and recognize handwriting.
    This is the main entry point for the recognition agent.
    
    Args:
        image_data: The image data
        model_name: Name of the model to use, or None for default
        preprocess: Whether to preprocess the image
        
    Returns:
        Dict: Processing result with recognition and quality evaluation
    """
    # Recognize handwriting
    recognition_result = recognize_handwriting_from_image(image_data, model_name, preprocess)
    
    # Evaluate the quality of the recognition
    quality_eval = evaluate_recognition_quality(recognition_result)
    
    # Return the combined result
    return {
        "recognition": recognition_result,
        "quality": quality_eval,
        "model_used": model_name or get_settings().DEFAULT_MODEL,
        "timestamp": time.time()
    }