"""
Agent orchestrator for coordinating the workflow between agents.
Implements the agent workflow using functional programming principles.
"""

from typing import Dict, Any, Optional, List, Tuple
import logging
import time

from app.services import llm_service, image_service, cache_service, storage_service 
from app.agents import recognition_agent, review_agent
from app.config.settings import get_settings

# Initialize logger
logger = logging.getLogger(__name__)

def process_image_workflow(
    image_data: bytes,
    recognition_model: Optional[str] = None,
    review_model: Optional[str] = None,
    preprocess: bool = True,
    skip_review: bool = False
) -> Dict[str, Any]:
    """
    Process an image through the full recognition and review workflow.
    
    Args:
        image_data: The image data
        recognition_model: Name of the model to use for recognition, or None for default
        review_model: Name of the model to use for review, or None for default
        preprocess: Whether to preprocess the image
        skip_review: Whether to skip the review step
        
    Returns:
        Dict: Result of the workflow
    """
    # Generate image hash for caching
    image_hash = image_service.hash_image(image_data)
    
    # Try to get from cache first
    cache_key = f"workflow_{image_hash}_{recognition_model or 'default'}_{review_model or 'default'}"
    cached_result = cache_service.cache_get(cache_key)
    if cached_result:
        logger.info(f"Using cached workflow result for image {image_hash}")
        return cached_result
    
    # Step 1: Recognition
    try:
        recognition_start_time = time.time()
        recognition_result = recognition_agent.process_image(
            image_data=image_data,
            model_name=recognition_model,
            preprocess=preprocess
        )
        recognition_time = time.time() - recognition_start_time
        
        # Extract the actual recognition data from the result
        recognition_data = recognition_result.get("recognition", {})
        
        # Step 2: Review (if not skipped)
        if not skip_review and recognition_result.get("quality", {}).get("needs_review", False):
            review_start_time = time.time()
            review_result = review_agent.process_recognition_result(
                recognition_result=recognition_data,
                model_name=review_model
            )
            review_time = time.time() - review_start_time
            
            # Combine results
            workflow_result = {
                "recognition": recognition_result,
                "review": review_result,
                "final_result": review_result.get("corrected_recognition", recognition_data),
                "next_step": review_result.get("next_step", "approve"),
                "processing_times": {
                    "recognition": recognition_time,
                    "review": review_time,
                    "total": recognition_time + review_time
                },
                "models_used": {
                    "recognition": recognition_model or get_settings().DEFAULT_MODEL,
                    "review": review_model or get_settings().DEFAULT_REVIEW_MODEL
                },
                "timestamp": time.time()
            }
        else:
            # Skip review step
            workflow_result = {
                "recognition": recognition_result,
                "final_result": recognition_data,
                "next_step": "approve",
                "processing_times": {
                    "recognition": recognition_time,
                    "total": recognition_time
                },
                "models_used": {
                    "recognition": recognition_model or get_settings().DEFAULT_MODEL
                },
                "timestamp": time.time()
            }
        
        # Save to cache
        cache_service.cache_set(cache_key, workflow_result)
        
        return workflow_result
    
    except Exception as e:
        logger.error(f"Error in workflow processing: {str(e)}")
        return {
            "error": str(e),
            "timestamp": time.time()
        }

def human_review_workflow(
    workflow_result: Dict[str, Any],
    human_corrections: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Apply human corrections to a workflow result.
    
    Args:
        workflow_result: The original workflow result
        human_corrections: Human-provided corrections
        
    Returns:
        Dict: Updated workflow result with human corrections
    """
    # Extract the current final result
    current_final = workflow_result.get("final_result", {})
    
    # Create an updated final result with human corrections
    updated_final = {
        **current_final,
        **human_corrections,
        "human_reviewed": True,
        "human_review_timestamp": time.time()
    }
    
    # Update the workflow result
    updated_workflow = {
        **workflow_result,
        "final_result": updated_final,
        "next_step": "complete",
        "human_review_applied": True
    }
    
    # If there was a review, update it to reflect human intervention
    if "review" in workflow_result:
        updated_workflow["review"] = {
            **workflow_result["review"],
            "human_review_applied": True
        }
    
# Save the updated workflow result to cache
    if "recognition" in workflow_result:
        recognition_data = workflow_result["recognition"].get("recognition", {})
        image_hash = recognition_data.get("metadata", {}).get("image_hash")
        if image_hash:
            cache_key = f"workflow_{image_hash}_human_reviewed"
            cache_service.cache_set(cache_key, updated_workflow)
            
            # Also save to storage if enabled
            try:
                if get_settings().ENABLE_STORAGE:
                    storage_service.save_result(
                        result=updated_workflow,
                        image_hash=image_hash,
                        model_name="human_reviewed"
                    )
            except Exception as e:
                logger.error(f"Error saving human reviewed result: {str(e)}")
    
    return updated_workflow