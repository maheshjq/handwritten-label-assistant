# Default Ollama model to use
DEFAULT_MODEL = "llava:latest"

# Ollama API endpoint
OLLAMA_API_URL = "http://localhost:11434/api/generate"

# Recognition prompt template
RECOGNITION_PROMPT = """
This image contains handwritten text. Please:
1. Transcribe exactly what's written in the image, preserving capitalization and punctuation
2. Provide your confidence level (0-100%) in your transcription
3. Format your response as a JSON with keys 'text' and 'confidence'
4. If you can identify structured data like Item IDs or Locations, include them as additional fields
"""