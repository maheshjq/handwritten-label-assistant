"""
Routes for handwriting recognition.
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
import io
import logging
import time

from app.config.settings import get_settings, Settings
from app.schemas.requests import RecognitionRequest
from app.schemas.responses import (
    RecognitionResponse, QualityEvaluation, RecognitionProcessResponse,
    WorkflowResponse
)
from app.services import llm_service, image_service, cache_service, storage_service
from app.agents import agent_orchestrator

# Initialize router
router = APIRouter()

# Initialize logger
logger = logging.getLogger(__name__)

@router.post("/recognize", response_model=WorkflowResponse)
async def recognize_handwriting(
    file: UploadFile = File(...),
    model_name: Optional[str] = Form(None),
    review_model: Optional[str] = Form(None),  # Added review_model parameter
    preprocess: bool = Form(True),
    skip_review: bool = Form(False),
    settings: Settings = Depends(get_settings)
):
    """
    Recognize handwriting from an uploaded image.
    """
    # Check file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        # Read the file
        contents = await file.read()
        
        # Process the image through the agent workflow
        result = agent_orchestrator.process_image_workflow(
            image_data=contents,
            recognition_model=model_name,
            review_model=review_model,  # Pass review_model to the workflow
            preprocess=preprocess,
            skip_review=skip_review
        )
        
        # Check for errors
        if "error" in result and result["error"]:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
    
    except Exception as e:
        logger.error(f"Error recognizing handwriting: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/recognize/base64", response_model=WorkflowResponse)
async def recognize_handwriting_base64(
    image_base64: str,
    model_name: Optional[str] = None,
    preprocess: bool = True,
    skip_review: bool = False,
    settings: Settings = Depends(get_settings)
):
    """
    Recognize handwriting from a base64 encoded image.
    """
    try:
        # Decode the base64 image
        try:
            image_data = image_service.decode_image_base64(image_base64)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid base64 image: {str(e)}")
        
        # Process the image through the agent workflow
        result = agent_orchestrator.process_image_workflow(
            image_data=image_data,
            recognition_model=model_name,
            preprocess=preprocess,
            skip_review=skip_review
        )
        
        # Check for errors
        if "error" in result and result["error"]:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
    
    except Exception as e:
        logger.error(f"Error recognizing handwriting: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/human-review", response_model=WorkflowResponse)
async def human_review(
    workflow_id: str,
    corrected_text: Optional[str] = Form(None),
    corrected_structured_data: Optional[str] = Form(None),
    comments: Optional[str] = Form(None),
    settings: Settings = Depends(get_settings)
):
    """
    Submit human review corrections for a recognition result.
    """
    try:
        # Parse the corrected structured data
        structured_data = None
        if corrected_structured_data:
            try:
                import json
                structured_data = json.loads(corrected_structured_data)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid structured data format")
        
        # Get the workflow result
        workflow_result = cache_service.cache_get(f"workflow_{workflow_id}")
        if not workflow_result:
            raise HTTPException(status_code=404, detail="Workflow result not found")
        
        # Create the human corrections
        human_corrections = {
            "text": corrected_text if corrected_text else workflow_result.get("final_result", {}).get("text", ""),
            "structured_data": structured_data if structured_data else workflow_result.get("final_result", {}).get("structured_data", {}),
            "human_comments": comments
        }
        
        # Apply the human corrections
        updated_workflow = agent_orchestrator.human_review_workflow(
            workflow_result=workflow_result,
            human_corrections=human_corrections
        )
        
        return updated_workflow
    
    except Exception as e:
        logger.error(f"Error processing human review: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))