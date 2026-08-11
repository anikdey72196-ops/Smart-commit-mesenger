import requests
import time
import sys
import json
import os
import re

def generate_commit_options(diff_text):
    """Generates 3 distinct commit message options from git diff using AI."""
    max_retries = 3
    model_name = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")
    host_url = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
    api_endpoint = f"{host_url}/api/generate"

    prompt = (
        "Generate exactly 3 distinct, high-quality commit message options for the following git diff "
        "using Conventional Commits format (e.g., feat:, fix:, docs:, refactor:, style:).\n\n"
        "Option 1: Short and concise.\n"
        "Option 2: Scoped and descriptive (e.g. feat(auth): ...).\n"
        "Option 3: Action-oriented summary.\n\n"
        'Output ONLY a valid JSON array of 3 strings, e.g.: ["feat: update login UI", "feat(auth): add JWT handling", "refactor: clean up user auth"]. '
        "Do NOT include markdown formatting or extra text.\n\n"
        f"Diff:\n{diff_text}"
    )

    for attempt in range(max_retries):
        try:
            response = requests.post(api_endpoint, json={
                "model": model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": 120,
                    "temperature": 0.5
                }
            }, timeout=35)
            response.raise_for_status()

            raw_text = response.json().get("response", "").strip()
            options = parse_options_from_response(raw_text)
            if options:
                return options
            
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"[Attempt {attempt + 1}/{max_retries}] Connection issue ({e}). Retrying in 2 seconds...")
                time.sleep(2)
            else:
                print(f"\nError generating commit messages with Ollama: {e}")
                print("Please check if Ollama is running in your system tray or terminal!")
                sys.exit(1)
    
    return []

def parse_options_from_response(raw_text):
    """Parses JSON array or fallback numbered/bulleted list from LLM output."""
    # Strip markdown codeblocks if present
    cleaned = re.sub(r"^```[a-zA-Z]*\n?", "", raw_text).rstrip("`\n\r ")
    
    # 1. Try parsing JSON array directly
    try:
        data = json.loads(cleaned)
        if isinstance(data, list) and len(data) > 0:
            return [str(item).strip() for item in data if str(item).strip()][:3]
    except Exception:
        pass

    # 2. Fallback: Parse line-by-line (e.g. 1. msg, 2. msg, or - msg)
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    parsed = []
    for line in lines:
        cleaned_line = re.sub(r"^(\d+[\.\)]|\-|\*)\s*", "", line).strip().strip('"\'')
        if cleaned_line and len(cleaned_line) > 3:
            parsed.append(cleaned_line)
    
    if parsed:
        return parsed[:3]
    
    # 3. Last fallback: return raw text as single option if non-empty
    single = raw_text.strip().strip('"\'[]')
    return [single] if single else []

def generate_commit_message(diff_text):
    """Backwards compatibility helper returning first option as single string."""
    opts = generate_commit_options(diff_text)
    return opts[0] if opts else "update project files"

