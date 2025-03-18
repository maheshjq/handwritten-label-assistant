"""
Request schemas for API endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class RecognitionRequest(BaseModel):
    """Request model for recognition with existing image data"""
    image_hash: str = Field(..., description="Hash of the uploaded image")
    model_name: Optional[str] = Field(None, description="Name of the model to use")
    preprocess: bool = Field(True, description="Whether to preprocess the image")
    skip_review: bool = Field(False, description="Whether to skip the review step")

class ReviewRequest(BaseModel):
    """Request model for reviewing a recognition result"""
    recognition_id: str = Field(..., description="ID of the recognition result to review")
    model_name: Optional[str] = Field(None, description="Name of the model to use for review")

class HumanReviewRequest(BaseModel):
    """Request model for human review of a recognition result"""
    workflow_id: str = Field(..., description="ID of the workflow result")
    corrected_text: Optional[str] = Field(None, description="Human-corrected text")
    corrected_structured_data: Optional[Dict[str, Any]] = Field(None, description="Human-corrected structured data")
    comments: Optional[str] = Field(None, description="Comments from the human reviewer")