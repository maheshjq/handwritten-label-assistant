"""
Storage service for saving and retrieving recognition results.
"""

import os
import json
import time
from typing import Dict, Any, Optional, List
import logging

from app.config.settings import get_settings

# Initialize logger
logger = logging.getLogger(__name__)

def save_result(
    result: Dict[str, Any],
    image_hash: str,
    model_name: str
) -> str:
    """
    Save a recognition result to disk.
    
    Args:
        result: The recognition result
        image_hash: Hash of the image
        model_name: Name of the model used for recognition
        
    Returns:
        str: Path to the saved result
    """
    settings = get_settings()
    
    if not settings.ENABLE_STORAGE:
        raise ValueError("Storage is disabled in settings")
    
    # Create the results directory if it doesn't exist
    results_dir = os.path.join(settings.STORAGE_PATH, "results")
    os.makedirs(results_dir, exist_ok=True)
    
    # Generate a filename with timestamp and metadata
    timestamp = int(time.time())
    filename = f"{image_hash}_{model_name}_{timestamp}.json"
    
    # Add metadata to the result
    result_with_metadata = {
        "result": result,
        "metadata": {
            "image_hash": image_hash,
            "model_name": model_name,
            "timestamp": timestamp
        }
    }
    
    # Save the result
    result_path = os.path.join(results_dir, filename)
    with open(result_path, "w") as f:
        json.dump(result_with_metadata, f, indent=2)
    
    return result_path

def load_result(result_path: str) -> Dict[str, Any]:
    """
    Load a recognition result from disk.
    
    Args:
        result_path: Path to the result file
        
    Returns:
        Dict: The recognition result with metadata
    """
    with open(result_path, "r") as f:
        return json.load(f)

def get_results_for_image(image_hash: str) -> List[Dict[str, Any]]:
    """
    Get all results for an image.
    
    Args:
        image_hash: Hash of the image
        
    Returns:
        List[Dict]: List of recognition results with metadata
    """
    settings = get_settings()
    
    if not settings.ENABLE_STORAGE:
        raise ValueError("Storage is disabled in settings")
    
    # Get all result files for this image
    results_dir = os.path.join(settings.STORAGE_PATH, "results")
    if not os.path.exists(results_dir):
        return []
    
    results = []
    for filename in os.listdir(results_dir):
        if filename.startswith(image_hash) and filename.endswith(".json"):
            result_path = os.path.join(results_dir, filename)
            try:
                result = load_result(result_path)
                results.append(result)
            except Exception as e:
                logger.error(f"Error loading result {result_path}: {str(e)}")
    
    # Sort by timestamp (newest first)
    results.sort(key=lambda r: r["metadata"]["timestamp"], reverse=True)
    
    return results

def delete_result(result_path: str) -> bool:
    """
    Delete a recognition result from disk.
    
    Args:
        result_path: Path to the result file
        
    Returns:
        bool: True if successfully deleted, False otherwise
    """
    try:
        os.remove(result_path)
        return True
    except Exception as e:
        logger.error(f"Error deleting result {result_path}: {str(e)}")
        return False

def delete_results_for_image(image_hash: str) -> int:
    """
    Delete all results for an image.
    
    Args:
        image_hash: Hash of the image
        
    Returns:
        int: Number of results deleted
    """
    settings = get_settings()
    
    if not settings.ENABLE_STORAGE:
        raise ValueError("Storage is disabled in settings")
    
    # Get all result files for this image
    results_dir = os.path.join(settings.STORAGE_PATH, "results")
    if not os.path.exists(results_dir):
        return 0
    
    deleted_count = 0
    for filename in os.listdir(results_dir):
        if filename.startswith(image_hash) and filename.endswith(".json"):
            result_path = os.path.join(results_dir, filename)
            if delete_result(result_path):
                deleted_count += 1
    
    return deleted_count

def clear_old_results(max_age_days: int = 30) -> int:
    """
    Delete old results.
    
    Args:
        max_age_days: Maximum age of results in days
        
    Returns:
        int: Number of results deleted
    """
    settings = get_settings()
    
    if not settings.ENABLE_STORAGE:
        raise ValueError("Storage is disabled in settings")
    
    # Get all result files
    results_dir = os.path.join(settings.STORAGE_PATH, "results")
    if not os.path.exists(results_dir):
        return 0
    
    current_time = time.time()
    max_age_seconds = max_age_days * 24 * 60 * 60
    
    deleted_count = 0
    for filename in os.listdir(results_dir):
        if filename.endswith(".json"):
            result_path = os.path.join(results_dir, filename)
            try:
                # Check the file's age
                file_time = os.path.getmtime(result_path)
                if current_time - file_time > max_age_seconds:
                    if delete_result(result_path):
                        deleted_count += 1
            except Exception as e:
                logger.error(f"Error checking age of result {result_path}: {str(e)}")
    
    return deleted_count