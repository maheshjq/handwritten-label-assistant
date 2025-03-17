# Default Ollama model to use
DEFAULT_MODEL = "llava:latest"

# Ollama API endpoint
OLLAMA_API_URL = "http://localhost:11434/api/generate"

# Recognition prompt template
RECOGNITION_PROMPT = """
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
    - Preparer’s Name  
    - Date  
    - Telephone  
    - Floor  
3. Provide your confidence level (0-100%) in your transcription
4. **Format your response as JSON** with the following keys:  
    - `"text"` → The extracted text  
    - `"confidence"` → Your confidence score (0-100%) in text accuracy  
    - `"structured_data"` → A dictionary with identified fields  
"""