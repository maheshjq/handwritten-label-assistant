"""
Routes for validation of recognition results.
"""

from fastapi import APIRouter, HTTPException, Depends, Body
from typing import Dict, Any, Optional
import logging

from app.config.settings import get_settings, Settings
from app.services import llm_service
from app.agents import review_agent

# Initialize router
router = APIRouter()

# Initialize logger
logger = logging.getLogger(__name__)

@router.post("/validate-text")
async def validate_text(
    text: str = Body(..., embed=True),
    settings: Settings = Depends(get_settings)
):
    """
    Validate the extracted text and extract structured data.
    """
    try:
        # Extract structured data from text
        structured_data = llm_service.extract_structured_data(text)
        
        # Check if we got any structured data
        is_valid = len(structured_data) > 0
        
        return {
            "valid": is_valid,
            "structured_data": structured_data
        }
    
    except Exception as e:
        logger.error(f"Error validating text: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/review-result")
async def review_result(
    recognition_result: Dict[str, Any] = Body(...),
    model_name: Optional[str] = Body(None),
    settings: Settings = Depends(get_settings)
):
    """
    Review a recognition result and suggest improvements.
    """
    try:
        # Review the recognition result
        review_result = review_agent.review_recognition(
            recognition_result=recognition_result,
            model_name=model_name
        )
        
        return review_result
    
    except Exception as e:
        logger.error(f"Error reviewing result: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))