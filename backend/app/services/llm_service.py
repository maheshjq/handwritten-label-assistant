"""
LLM service for interacting with different language model providers.
Supports Ollama, Groq, Claude, and OpenAI with a unified interface.
"""

import requests
import json
import base64
from typing import Dict, Any, List, Optional, Union, Callable
import logging
from functools import lru_cache
from enum import Enum
import hashlib
import time

from app.config.settings import get_settings

# Initialize logger
logger = logging.getLogger(__name__)

class LLMProvider(str, Enum):
    """Supported LLM providers"""
    OLLAMA = "ollama"
    GROQ = "groq"
    CLAUDE = "claude"
    OPENAI = "openai"

def get_provider_for_model(model_name: str) -> LLMProvider:
    """
    Determine the provider for a given model name.
    
    Args:
        model_name: Name of the model
        
    Returns:
        LLMProvider: The provider for the model
    """
    settings = get_settings()
    
    # Explicitly check for Groq vision models first
    if "llama" in model_name and "vision" in model_name:
        return LLMProvider.GROQ
    
    # Ollama models
    if model_name in settings.SUPPORTED_MODELS or "llava" in model_name or "bakllava" in model_name:
        return LLMProvider.OLLAMA
    
    # Other Groq models
    if model_name.startswith("llama") or model_name.startswith("mixtral"):
        return LLMProvider.GROQ
    
    # Claude models
    if model_name.startswith("claude"):
        return LLMProvider.CLAUDE
    
    # OpenAI models
    if model_name.startswith("gpt") or model_name.startswith("text-"):
        return LLMProvider.OPENAI
    
    # Default to Ollama
    return LLMProvider.OLLAMA

def process_with_ollama(
    prompt: str,
    model_name: str,
    image_data: Optional[bytes] = None,
    temperature: float = 0.7,
    stream: bool = False
) -> Dict[str, Any]:
    """
    Process a prompt with Ollama.
    
    Args:
        prompt: The prompt to send to the model
        model_name: The name of the model to use
        image_data: Optional image data for multimodal models
        temperature: Temperature for generation
        stream: Whether to stream the response
        
    Returns:
        Dict: Response from Ollama
    """
    settings = get_settings()
    
    # Prepare the payload
    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": stream,
        "temperature": temperature,
        "format": "json"  # Request JSON output if the model supports it
    }
    
    # Add image data if provided
    if image_data:
        base64_image = base64.b64encode(image_data).decode("utf-8")
        payload["images"] = [base64_image]
    
    try:
        response = requests.post(
            f"{settings.OLLAMA_BASE_URL}/api/generate",
            json=payload,
            timeout=settings.RECOGNITION_TIMEOUT
        )
        response.raise_for_status()
        
        result = response.json()
        response_text = result.get("response", "{}")
        
        # Try to parse as JSON
        try:
            parsed_response = json.loads(response_text)
            return {
                "text": parsed_response.get("text", response_text),
                "confidence": parsed_response.get("confidence", 0.8),
                "structured_data": parsed_response.get("structured_data", {})
            }
        except json.JSONDecodeError:
            # If not valid JSON, return the raw text
            logger.warning("Failed to parse JSON response from Ollama")
            return {
                "text": response_text,
                "confidence": 0.8,  # Default confidence
                "structured_data": extract_structured_data(response_text)
            }
    except requests.exceptions.RequestException as e:
        logger.error(f"Error processing with Ollama: {str(e)}")
        raise RuntimeError(f"Failed to process with Ollama: {str(e)}")

def process_with_groq(
    prompt: str,
    model_name: str,
    image_data: Optional[bytes] = None,
    temperature: float = 0.7
) -> Dict[str, Any]:
    """
    Process a prompt with Groq.
    
    Args:
        prompt: The prompt to send to the model
        model_name: The name of the model to use
        image_data: Optional image data for multimodal models
        temperature: Temperature for generation
        
    Returns:
        Dict: Response from Groq
    """
    settings = get_settings()
    
    if not settings.GROQ_API_KEY:
        raise ValueError("Groq API key not set")
    
    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Check if this is a vision model request with image
    if image_data and "vision" in model_name:
        # Construct content array with image and text
        base64_image = base64.b64encode(image_data).decode("utf-8")
        content = [
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}"
                }
            },
            {
                "type": "text",
                "text": prompt
            }
        ]
        
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": content}],
            "temperature": temperature
        }
    else:
        # Standard text-only request
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature
        }
    
    try:
        response = requests.post(
            f"{settings.GROQ_BASE_URL}/chat/completions",
            headers=headers,
            json=payload,
            timeout=settings.RECOGNITION_TIMEOUT
        )
        response.raise_for_status()
        
        result = response.json()
        response_text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        # Try to extract JSON from the response
        try:
            # Look for JSON pattern
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                parsed_response = json.loads(json_match.group(0))
                return {
                    "text": parsed_response.get("text", response_text),
                    "confidence": parsed_response.get("confidence", 0.8),
                    "structured_data": parsed_response.get("structured_data", {})
                }
            else:
                # If no JSON pattern found, return the raw text
                return {
                    "text": response_text,
                    "confidence": 0.8,
                    "structured_data": extract_structured_data(response_text)
                }
        except json.JSONDecodeError:
            # If invalid JSON, return the raw text
            return {
                "text": response_text,
                "confidence": 0.8,
                "structured_data": extract_structured_data(response_text)
            }
    except requests.exceptions.RequestException as e:
        logger.error(f"Error processing with Groq: {str(e)}")
        raise RuntimeError(f"Failed to process with Groq: {str(e)}")

def process_with_claude(
    prompt: str,
    model_name: str,
    temperature: float = 0.7
) -> Dict[str, Any]:
    """
    Process a prompt with Claude.
    
    Args:
        prompt: The prompt to send to the model
        model_name: The name of the model to use
        temperature: Temperature for generation
        
    Returns:
        Dict: Response from Claude
    """
    settings = get_settings()
    
    if not settings.CLAUDE_API_KEY:
        raise ValueError("Claude API key not set")
    
    headers = {
        "x-api-key": settings.CLAUDE_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": 1000
    }
    
    try:
        response = requests.post(
            f"{settings.CLAUDE_BASE_URL}/messages",
            headers=headers,
            json=payload,
            timeout=settings.RECOGNITION_TIMEOUT
        )
        response.raise_for_status()
        
        result = response.json()
        response_text = result.get("content", [{}])[0].get("text", "")
        
        # Try to extract JSON from the response
        try:
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                parsed_response = json.loads(json_match.group(0))
                return {
                    "text": parsed_response.get("text", response_text),
                    "confidence": parsed_response.get("confidence", 0.8),
                    "structured_data": parsed_response.get("structured_data", {})
                }
            else:
                return {
                    "text": response_text,
                    "confidence": 0.8,
                    "structured_data": extract_structured_data(response_text)
                }
        except json.JSONDecodeError:
            return {
                "text": response_text,
                "confidence": 0.8,
                "structured_data": extract_structured_data(response_text)
            }
    except requests.exceptions.RequestException as e:
        logger.error(f"Error processing with Claude: {str(e)}")
        raise RuntimeError(f"Failed to process with Claude: {str(e)}")

def process_with_openai(
    prompt: str,
    model_name: str,
    temperature: float = 0.7
) -> Dict[str, Any]:
    """
    Process a prompt with OpenAI.
    
    Args:
        prompt: The prompt to send to the model
        model_name: The name of the model to use
        temperature: Temperature for generation
        
    Returns:
        Dict: Response from OpenAI
    """
    settings = get_settings()
    
    if not settings.OPENAI_API_KEY:
        raise ValueError("OpenAI API key not set")
    
    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": 1000
    }
    
    try:
        response = requests.post(
            f"{settings.OPENAI_BASE_URL}/chat/completions",
            headers=headers,
            json=payload,
            timeout=settings.RECOGNITION_TIMEOUT
        )
        response.raise_for_status()
        
        result = response.json()
        response_text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        # Try to extract JSON from the response
        try:
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                parsed_response = json.loads(json_match.group(0))
                return {
                    "text": parsed_response.get("text", response_text),
                    "confidence": parsed_response.get("confidence", 0.8),
                    "structured_data": parsed_response.get("structured_data", {})
                }
            else:
                return {
                    "text": response_text,
                    "confidence": 0.8,
                    "structured_data": extract_structured_data(response_text)
                }
        except json.JSONDecodeError:
            return {
                "text": response_text,
                "confidence": 0.8,
                "structured_data": extract_structured_data(response_text)
            }
    except requests.exceptions.RequestException as e:
        logger.error(f"Error processing with OpenAI: {str(e)}")
        raise RuntimeError(f"Failed to process with OpenAI: {str(e)}")

def extract_structured_data(text: str) -> Dict[str, str]:
    """
    Extract structured data from text.
    
    Args:
        text: The text to extract structured data from
        
    Returns:
        Dict: Extracted structured data
    """
    structured_data = {}
    
    # Extract fields using regular expressions
    field_patterns = [
        (r"Customer Name:?\s*([\w\s]+)", "CustomerName"),
        (r"Customer ID:?\s*(\w+)", "CustomerID"),
        (r"Division ID:?\s*(\w+)", "DivisionID"),
        (r"Department ID:?\s*(\w+)", "DepartmentID"),
        (r"Record Code:?\s*(\w+)", "RecordCode"),
        (r"SKP Box Number:?\s*(\w+)", "SKPBoxNumber"),
        (r"Reference:?\s*([\w\s]+)", "Reference"),
        (r"Major Description:?\s*([\w\s]+)", "MajorDescription"),
        (r"Preparer's Name:?\s*([\w\s]+)", "PreparerName"),
        (r"Date:?\s*([\w\s\-\/\.]+)", "Date"),
        (r"Telephone:?\s*([\w\s\-\.]+)", "Telephone"),
        (r"Floor:?\s*([\w\s\-\.]+)", "Floor"),
    ]
    
    import re
    for pattern, field_name in field_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            structured_data[field_name] = match.group(1).strip()
    
    return structured_data

def process_text_with_llm(
    prompt: str,
    model_name: str = None,
    temperature: float = 0.7
) -> Dict[str, Any]:
    """
    Process a text prompt with an LLM, automatically selecting the appropriate provider.
    
    Args:
        prompt: The prompt to send to the model
        model_name: The name of the model to use, or None for default
        temperature: Temperature for generation
        
    Returns:
        Dict: Response from the LLM
    """
    settings = get_settings()
    
    # Use default model if none specified
    if model_name is None:
        model_name = settings.DEFAULT_MODEL
    
    # Determine provider based on model name
    provider = get_provider_for_model(model_name)
    
    # Process with the appropriate provider
    if provider == LLMProvider.OLLAMA:
        return process_with_ollama(prompt, model_name, None, temperature)
    elif provider == LLMProvider.GROQ:
        return process_with_groq(prompt, model_name, None, temperature)
    elif provider == LLMProvider.CLAUDE:
        return process_with_claude(prompt, model_name, temperature)
    elif provider == LLMProvider.OPENAI:
        return process_with_openai(prompt, model_name, temperature)
    else:
        raise ValueError(f"Unsupported provider: {provider}")

def recognize_handwriting(
    image_data: bytes,
    model_name: str = None
) -> Dict[str, Any]:
    """
    Recognize handwriting in an image.
    
    Args:
        image_data: The image data
        model_name: The name of the model to use, or None for default
        
    Returns:
        Dict: Recognition results
    """
    settings = get_settings()
    
    # Use default model if none specified
    if model_name is None:
        model_name = settings.DEFAULT_MODEL
    
    # Determine provider based on model name
    provider = get_provider_for_model(model_name)
    
    # Process with the appropriate provider
    if provider == LLMProvider.OLLAMA:
        return process_with_ollama(
            prompt=settings.RECOGNITION_PROMPT,
            model_name=model_name,
            image_data=image_data
        )
    elif provider == LLMProvider.GROQ and "vision" in model_name:
        return process_with_groq(
            prompt=settings.RECOGNITION_PROMPT,
            model_name=model_name,
            image_data=image_data
        )
    else:
        raise ValueError(f"Image processing not supported by provider: {provider}")

def hash_content(content: bytes) -> str:
    """
    Generate a hash for content.
    
    Args:
        content: The content to hash
        
    Returns:
        str: Hash of the content
    """
    return hashlib.md5(content).hexdigest()