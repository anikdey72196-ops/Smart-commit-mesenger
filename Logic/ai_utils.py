import requests
import time
import sys
import json
import os

def generate_commit_message(diff_text):
    max_retries = 3
    commit_msg_parts = []
    model_name = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")
    host_url = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
    api_endpoint = f"{host_url}/api/generate"
    for attempt in range(max_retries):
        try:
            print("Suggested message: ", end="", flush=True)
            response = requests.post(api_endpoint,
            json={
                "model": model_name,
                "prompt": f'Generate a short, one-line commit message for this git diff. '
                          f'Use Conventional Commits format (feat:, fix:, docs:, etc.). '
                          f'Only output the message, no extra text.\n\nDiff:\n{diff_text}',
                "stream": True,
                "keep_alive": -1,
                "options": {
                    "num_predict": 50
                }
            }, stream=True, timeout=30)
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line)
                    text_chunk = chunk.get("response", "")
                    print(text_chunk, end="", flush=True)
                    commit_msg_parts.append(text_chunk)
            
            print() # Print newline at the end
            return "".join(commit_msg_parts).strip()
            
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"\n[Attempt {attempt + 1}/{max_retries}] Connection issue ({e}). Retrying in 2 seconds...")
                time.sleep(2)
            else:
                print(f"\nError generating commit message with Ollama: {e}")
                print("Please check if Ollama is running in your system tray or terminal!")
                sys.exit(1)
