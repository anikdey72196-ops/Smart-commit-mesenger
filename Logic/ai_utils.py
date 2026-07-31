import requests
import time
import sys
import json

def generate_commit_message(diff_text):
    max_retries = 3
    commit_msg_parts = []

    for attempt in range(max_retries):
        try:
            print("Suggested message: ", end="", flush=True)
            response = requests.post('http://localhost:11434/api/generate', json={
                "model": "qwen2.5-coder:7b",
                "prompt": f'Generate a short, one-line commit message for this git diff. '
                          f'Use Conventional Commits format (feat:, fix:, docs:, etc.). '
                          f'Only output the message, no extra text.\n\nDiff:\n{diff_text}',
                "stream": True,
                "keep_alive": "-1",
                "options": {
                    "num_predict": 50
                }
            }, stream=True)
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
                print(f"\nOllama busy or error (attempt {attempt + 1}/{max_retries}). Retrying in 3 seconds...")
                time.sleep(3)
            else:
                print(f"\nError generating commit message with Ollama after {max_retries} attempts: {e}")
                print("Make sure Ollama is running in the background!")
                sys.exit(1)
