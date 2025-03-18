To start your backend, you'll need to follow these steps:

1. First, navigate to your backend directory:
   ```bash
   cd handwritten-label-assistant/backend
   ```

2. Create and activate a virtual environment:
   ```bash
   # For macOS/Linux
   python -m venv venv
   source venv/bin/activate

   # For Windows
   python -m venv venv
   venv\Scripts\activate
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file based on the example:
   ```bash
   cp .env.example .env
   ```

5. Edit the `.env` file to add your API keys (if you have them):
   ```bash
   # Use a text editor to modify the .env file
   # For example:
   # GROQ_API_KEY=your-groq-api-key
   # CLAUDE_API_KEY=your-claude-api-key
   # OPENAI_API_KEY=your-openai-api-key
   ```

6. Make sure Ollama is running (since it's the default provider for image recognition):
   ```bash
   # In a separate terminal
   ollama serve
   ```

7. Pull the necessary models in Ollama:
   ```bash
   # In a separate terminal
   ollama pull llava:latest
   ```

8. Start the FastAPI server:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

The backend server should now be running at http://localhost:8000, and you can access the API documentation at http://localhost:8000/docs.

To test that everything is working, you can make a simple request to the health check endpoint:
```bash
curl http://localhost:8000/health
```

You should see a response like: `{"status":"healthy"}`.

To start your frontend separately, navigate to the frontend directory and run:
```bash
cd ../frontend
npm run dev
```

The frontend should be available at http://localhost:3000.