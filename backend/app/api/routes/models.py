"""
Routes for getting and configuring models.
"""

from fastapi import APIRouter, HTTPException, Depends, Body
from typing import List, Dict, Any, Optional
import logging

from app.config.settings import get_settings, Settings
from app.services import llm_service
from app.schemas.responses import AvailableModel, ModelsResponse, ModelProvider

# Initialize router
router = APIRouter()

# Initialize logger
logger = logging.getLogger(__name__)

@router.get("/", response_model=ModelsResponse)
async def get_available_models(
    settings: Settings = Depends(get_settings)
):
    """
    Get list of available models.
    """
    try:
        # Create model list
        models = []
        
        # Add Ollama models
        for model_name in settings.SUPPORTED_MODELS:
            models.append(
                AvailableModel(
                    name=model_name,
                    provider=ModelProvider.OLLAMA,
                    description=f"Local Ollama model: {model_name}",
                    capabilities=["image_recognition", "text_processing"]
                )
            )
        
        # Add Groq models if API key is available
        if settings.GROQ_API_KEY:
            models.append(
                AvailableModel(
                    name="llama-3-8b",
                    provider=ModelProvider.GROQ,
                    description="Groq LLaMA 3 8B model",
                    capabilities=["text_processing"]
                )
            )
            models.append(
                AvailableModel(
                    name="llama-3-70b",
                    provider=ModelProvider.GROQ,
                    description="Groq LLaMA 3 70B model",
                    capabilities=["text_processing"]
                )
            )
        
        # Add Claude models if API key is available
        if settings.CLAUDE_API_KEY:
            models.append(
                AvailableModel(
                    name="claude-3-haiku",
                    provider=ModelProvider.CLAUDE,
                    description="Claude 3 Haiku model",
                    capabilities=["text_processing"]
                )
            )
            models.append(
                AvailableModel(
                    name="claude-3-sonnet",
                    provider=ModelProvider.CLAUDE,
                    description="Claude 3 Sonnet model",
                    capabilities=["text_processing"]
                )
            )
        
        # Add OpenAI models if API key is available
        if settings.OPENAI_API_KEY:
            models.append(
                AvailableModel(
                    name="gpt-4o",
                    provider=ModelProvider.OPENAI,
                    description="GPT-4o model",
                    capabilities=["text_processing"]
                )
            )
            models.append(
                AvailableModel(
                    name="gpt-3.5-turbo",
                    provider=ModelProvider.OPENAI,
                    description="GPT-3.5 Turbo model",
                    capabilities=["text_processing"]
                )
            )
        
        return ModelsResponse(
            models=models,
            default_model=settings.DEFAULT_MODEL,
            default_review_model=settings.DEFAULT_REVIEW_MODEL
        )
    
    except Exception as e:
        logger.error(f"Error getting available models: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test")
async def test_model(
    model_name: str = Body(...),
    text: str = Body(...),
    settings: Settings = Depends(get_settings)
):
    """
    Test a model with a simple text prompt.
    """
    try:
        # Process with LLM
        result = llm_service.process_text_with_llm(
            prompt=f"Respond to this: {text}",
            model_name=model_name
        )
        
        return {
            "model": model_name,
            "input": text,
            "output": result.get("text", ""),
            "provider": llm_service.get_provider_for_model(model_name)
        }
    
    except Exception as e:
        logger.error(f"Error testing model: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))