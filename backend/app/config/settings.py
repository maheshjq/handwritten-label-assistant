"""
Configuration settings for the Handwritten Label AI Assistant.
Uses environment variables with sensible defaults.
"""

import os
from functools import lru_cache
from typing import Dict, Any, List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # LLM Provider URLs
    OLLAMA_BASE_URL: str = Field("http://localhost:11434", description="Ollama API base URL")
    GROQ_BASE_URL: str = Field("https://api.groq.com/v1", description="Groq API base URL")
    CLAUDE_BASE_URL: str = Field("https://api.anthropic.com/v1", description="Claude API base URL")
    OPENAI_BASE_URL: str = Field("https://api.openai.com/v1", description="OpenAI API base URL")
    
    # API Keys
    GROQ_API_KEY: Optional[str] = Field(None, description="Groq API key")
    CLAUDE_API_KEY: Optional[str] = Field(None, description="Claude API key")
    OPENAI_API_KEY: Optional[str] = Field(None, description="OpenAI API key")
    
    # Model settings
    DEFAULT_MODEL: str = Field("llava:latest", description="Default model to use for recognition")
    DEFAULT_REVIEW_MODEL: str = Field("gpt-4o", description="Default model to use for review")
    SUPPORTED_MODELS: List[str] = Field(
        ["llava:latest", "bakllava:latest", "llava:13b", "llava:7b", "cogvlm-lite:latest"],
        description="List of supported models"
    )
    
    # Recognition settings
    CONFIDENCE_THRESHOLD: float = Field(0.7, description="Threshold for confidence to avoid review")
    RECOGNITION_TIMEOUT: int = Field(30, description="Timeout for recognition requests in seconds")
    
    # Cache settings
    ENABLE_CACHE: bool = Field(True, description="Enable caching of results")
    CACHE_EXPIRY: int = Field(3600, description="Cache expiry time in seconds")
    
    # Storage settings
    STORAGE_PATH: str = Field("./storage", description="Path to store processed images and results")
    ENABLE_STORAGE: bool = Field(True, description="Enable storage of processed images and results")
    
    # Recognition prompt
    RECOGNITION_PROMPT: str = Field(
        """
        1. **Extract all handwritten text** from the image.  
        2. **Identify structured fields** such as:
            - Customer Name  
            - Customer ID  
            - Division ID  
            - Department ID  
            - Record Code  
            - SKP Box Number  
            - Reference  
            - Major Description  
            - Preparer's Name  
            - Date  
            - Telephone  
            - Floor  
        3. Provide your confidence level (0-100%) in your transcription
        4. **Format your response as JSON** with the following keys:  
            - `"text"` → The extracted text  
            - `"confidence"` → Your confidence score (0-100%) in text accuracy  
            - `"structured_data"` → A dictionary with identified fields  
        """,
        description="Prompt for recognition"
    )
    
    # Review prompt
    REVIEW_PROMPT: str = Field(
        """
        You are a review agent for handwritten text recognition. Your task is to:
        
        1. Carefully examine the extracted text and structured data.
        2. Identify any potential errors or ambiguities.
        3. Suggest corrections if confidence is low or errors are detected.
        4. Determine if human review is necessary.
        
        Original extracted text: {extracted_text}
        Confidence score: {confidence}
        Structured data: {structured_data}
        
        Please provide your assessment as JSON with the following fields:
        - "needs_human_review": boolean indicating if human review is needed
        - "suggestions": a list of suggested corrections
        - "explanation": reasoning behind your assessment
        - "corrected_text": your corrected version of the text
        - "corrected_structured_data": your corrected version of the structured data
        """,
        description="Prompt for review"
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # This will ignore extra fields

@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings to avoid reloading from environment each time.
    
    Returns:
        Settings: Application settings
    """
    return Settings()