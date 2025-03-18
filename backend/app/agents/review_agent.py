"""
Review agent for evaluating and improving recognition results.
Uses a separate LLM to perform verification and suggest improvements.
"""

from typing import Dict, Any, Optional, List, Tuple
import logging
import json
import re
import time

from app.services import llm_service, cache_service, storage_service
from app.config.settings import get_settings

# Initialize logger
logger = logging.getLogger(__name__)

def format_review_prompt(recognition_result: Dict[str, Any]) -> str:
    """
    Format a prompt for the review agent.
    
    Args:
        recognition_result: The recognition result to review
        
    Returns:
        str: Formatted prompt
    """
    settings = get_settings()
    
    extracted_text = recognition_result.get("text", "")
    confidence = recognition_result.get("confidence", 0.0)
    structured_data = recognition_result.get("structured_data", {})
    
    # Format the structured data as a string
    structured_data_str = json.dumps(structured_data, indent=2) if structured_data else "None"
    
    # Format the prompt using the template from settings
    prompt = settings.REVIEW_PROMPT.format(
        extracted_text=extracted_text,
        confidence=confidence,
        structured_data=structured_data_str
    )
    
    return prompt

def parse_review_response(response_text: str) -> Dict[str, Any]:
    """
    Parse the review agent's response.
    
    Args:
        response_text: The response from the review agent
        
    Returns:
        Dict: Parsed response
    """
    # Try to extract JSON from the response
    try:
        # Look for JSON pattern
        import re
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            parsed_response = json.loads(json_match.group(0))
            return parsed_response
        else:
            # If no JSON pattern found, try to extract key info manually
            needs_human_review = "human review" in response_text.lower() and "recommended" in response_text.lower()
            suggestions = []
            
            # Extract suggestions
            suggestion_pattern = r"suggestion.*?:.*?([^\n]+)"
            for match in re.finditer(suggestion_pattern, response_text, re.IGNORECASE):
                suggestions.append(match.group(1).strip())
            
            return {
                "needs_human_review": needs_human_review,
                "suggestions": suggestions,
                "explanation": response_text,
                "corrected_text": None,
                "corrected_structured_data": None
            }
    except json.JSONDecodeError:
        # If JSON parsing fails, return a basic response
        logger.warning(f"Failed to parse JSON from review agent response: {response_text[:100]}...")
        return {
            "needs_human_review": True,
            "suggestions": [],
            "explanation": "Failed to parse review response",
            "corrected_text": None,
            "corrected_structured_data": None
        }

def review_recognition(
    recognition_result: Dict[str, Any],
    model_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Review a recognition result and suggest improvements.
    
    Args:
        recognition_result: The recognition result to review
        model_name: Name of the model to use for review, or None for default
        
    Returns:
        Dict: Review result with suggestions and corrections
    """
    settings = get_settings()
    
    # Generate a cache key
    recognition_hash = llm_service.hash_content(str(recognition_result).encode())
    cache_key = f"review_{recognition_hash}_{model_name or settings.DEFAULT_REVIEW_MODEL}"
    
    # Try to get from cache first
    cached_result = cache_service.cache_get(cache_key)
    if cached_result:
        logger.info(f"Using cached review result for recognition {recognition_hash}")
        return cached_result
    
    # Format the prompt for the review agent
    review_prompt = format_review_prompt(recognition_result)
    
    # Use a model optimized for text processing (not necessarily multimodal)
    review_model = model_name or settings.DEFAULT_REVIEW_MODEL
    
    try:
        # Process with LLM
        response = llm_service.process_text_with_llm(review_prompt, review_model)
        
        # Parse the response
        response_text = response.get("text", "")
        review_result = parse_review_response(response_text)
        
        # Add metadata
        review_result["model_used"] = review_model
        review_result["timestamp"] = time.time()
        
        # Save to cache
        cache_service.cache_set(cache_key, review_result)
        
        return review_result
    
    except Exception as e:
        logger.error(f"Error reviewing recognition: {str(e)}")
        return {
            "needs_human_review": True,
            "suggestions": [],
            "explanation": f"Error during review: {str(e)}",
            "corrected_text": None,
            "corrected_structured_data": None,
            "error": str(e)
        }

def apply_corrections(
    recognition_result: Dict[str, Any],
    review_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Apply corrections from a review to a recognition result.
    
    Args:
        recognition_result: The original recognition result
        review_result: The review result with corrections
        
    Returns:
        Dict: Updated recognition result with corrections applied
    """
    # Create a deep copy of the recognition result
    import copy
    corrected_result = copy.deepcopy(recognition_result)
    
    # Apply text correction if available
    corrected_text = review_result.get("corrected_text")
    if corrected_text:
        corrected_result["text"] = corrected_text
    
    # Apply structured data correction if available
    corrected_structured_data = review_result.get("corrected_structured_data")
    if corrected_structured_data:
        corrected_result["structured_data"] = corrected_structured_data
    
    # Adjust confidence based on review
    if review_result.get("needs_human_review", False):
        # Reduce confidence if human review is needed
        corrected_result["confidence"] = min(corrected_result.get("confidence", 0.5) * 0.8, 0.6)
    else:
        # Increase confidence slightly if no human review is needed
        corrected_result["confidence"] = min(corrected_result.get("confidence", 0.5) * 1.1, 0.95)
    
    # Add review information
    corrected_result["review_info"] = {
        "reviewed": True,
        "needs_human_review": review_result.get("needs_human_review", False),
        "suggestions": review_result.get("suggestions", []),
        "review_model": review_result.get("model_used")
    }
    
    return corrected_result

def determine_next_steps(review_result: Dict[str, Any]) -> str:
    """
    Determine the next steps based on a review result.
    
    Args:
        review_result: The review result
        
    Returns:
        str: Next step action ("approve", "correct", "human_review")
    """
    # Get whether human review is needed
    needs_human_review = review_result.get("needs_human_review", False)
    
    # Check if corrections were provided
    has_corrections = (
        review_result.get("corrected_text") is not None or
        review_result.get("corrected_structured_data") is not None
    )
    
    # Determine next step
    if needs_human_review:
        return "human_review"
    elif has_corrections:
        return "correct"
    else:
        return "approve"

def process_recognition_result(
    recognition_result: Dict[str, Any],
    model_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Process a recognition result through the review agent.
    This is the main entry point for the review agent.
    
    Args:
        recognition_result: The recognition result to review
        model_name: Name of the model to use for review, or None for default
        
    Returns:
        Dict: Processing result with review and next steps
    """
    # Review the recognition result
    review_result = review_recognition(recognition_result, model_name)
    
    # Determine next steps
    next_step = determine_next_steps(review_result)
    
    # Apply corrections if appropriate
    if next_step == "correct":
        corrected_result = apply_corrections(recognition_result, review_result)
    else:
        corrected_result = recognition_result
    
    # Return the combined result
    return {
        "original_recognition": recognition_result,
        "review": review_result,
        "corrected_recognition": corrected_result,
        "next_step": next_step,
        "model_used": model_name or get_settings().DEFAULT_REVIEW_MODEL,
        "timestamp": time.time()
    }