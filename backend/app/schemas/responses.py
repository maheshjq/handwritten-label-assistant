"""
Response schemas for API endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum

class ModelProvider(str, Enum):
    """Enum for LLM providers"""
    OLLAMA = "ollama"
    GROQ = "groq"
    CLAUDE = "claude"
    OPENAI = "openai"

class RecognitionResponse(BaseModel):
    """Response model for recognition"""
    text: str = Field(..., description="Recognized text")
    confidence: float = Field(..., description="Confidence score (0.0 to 1.0)")
    structured_data: Dict[str, Any] = Field(..., description="Structured data extracted from the text")
    metadata: Dict[str, Any] = Field(..., description="Metadata about the recognition")

class QualityEvaluation(BaseModel):
    """Quality evaluation for a recognition result"""
    overall_score: float = Field(..., description="Overall quality score (0.0 to 1.0)")
    needs_review: bool = Field(..., description="Whether the result needs review")
    issues: List[str] = Field(default_factory=list, description="List of identified issues")

class RecognitionProcessResponse(BaseModel):
    """Response model for recognition process"""
    recognition: RecognitionResponse = Field(..., description="Recognition result")
    quality: QualityEvaluation = Field(..., description="Quality evaluation")
    model_used: str = Field(..., description="Model used for recognition")
    timestamp: float = Field(..., description="Timestamp of recognition")

class NextStep(str, Enum):
    """Enum for next steps after review"""
    APPROVE = "approve"
    CORRECT = "correct"
    HUMAN_REVIEW = "human_review"
    COMPLETE = "complete"

class ReviewResponse(BaseModel):
    """Response model for review"""
    needs_human_review: bool = Field(..., description="Whether human review is needed")
    suggestions: List[str] = Field(default_factory=list, description="Suggestions for improvement")
    explanation: str = Field(..., description="Explanation of the review")
    corrected_text: Optional[str] = Field(None, description="Corrected text")
    corrected_structured_data: Optional[Dict[str, Any]] = Field(None, description="Corrected structured data")
    model_used: str = Field(..., description="Model used for review")
    timestamp: float = Field(..., description="Timestamp of review")

class ReviewProcessResponse(BaseModel):
    """Response model for review process"""
    original_recognition: RecognitionResponse = Field(..., description="Original recognition result")
    review: ReviewResponse = Field(..., description="Review result")
    corrected_recognition: RecognitionResponse = Field(..., description="Corrected recognition result")
    next_step: NextStep = Field(..., description="Next step after review")
    model_used: str = Field(..., description="Model used for review")
    timestamp: float = Field(..., description="Timestamp of review process")

class WorkflowResponse(BaseModel):
    """Response model for workflow"""
    recognition: RecognitionProcessResponse = Field(..., description="Recognition process result")
    review: Optional[ReviewProcessResponse] = Field(None, description="Review process result")
    final_result: RecognitionResponse = Field(..., description="Final result after workflow")
    next_step: NextStep = Field(..., description="Next step after workflow")
    processing_times: Dict[str, float] = Field(..., description="Processing times for each step")
    models_used: Dict[str, str] = Field(..., description="Models used for each step")
    timestamp: float = Field(..., description="Timestamp of workflow")
    error: Optional[str] = Field(None, description="Error message, if any")

class AvailableModel(BaseModel):
    """Model for available model information"""
    name: str = Field(..., description="Name of the model")
    provider: ModelProvider = Field(..., description="Provider of the model")
    description: str = Field(..., description="Description of the model")
    capabilities: List[str] = Field(default_factory=list, description="Capabilities of the model")

class ModelsResponse(BaseModel):
    """Response model for available models"""
    models: List[AvailableModel] = Field(..., description="List of available models")
    default_model: str = Field(..., description="Default model for recognition")
    default_review_model: str = Field(..., description="Default model for review")