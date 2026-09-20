import urllib.request
import urllib.error
import time
import sys
import json
import os
import re

def generate_commit_options(diff_text, recent_commits=None):
    """Generates 3 distinct commit message options from git diff using pure Python stdlib."""
    max_retries = 3
    model_name = os.getenv("OLLAMA_MODEL", "gpt-oss:20b-cloud")
    host_url = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
    num_predict = int(os.getenv("OLLAMA_NUM_PREDICT", "1024"))
    timeout_sec = int(os.getenv("OLLAMA_TIMEOUT", "60"))
    temperature = float(os.getenv("OLLAMA_TEMPERATURE", "0.4"))

    if "0.0.0.0" in host_url:
        host_url = host_url.replace("0.0.0.0", "localhost")
    if not host_url.startswith("http://") and not host_url.startswith("https://"):
        host_url = f"http://{host_url}"
    if ":" not in host_url.replace("http://", "").replace("https://", ""):
        host_url = f"{host_url}:11434"
    api_endpoint = f"{host_url}/api/generate"

    style_context = ""
    if recent_commits:
        formatted_history = "\n".join(f"- {msg}" for msg in recent_commits[:5])
        style_context = (
            "\nRecent commit messages in this repository (for style and convention reference):\n"
            f"{formatted_history}\n"
            "Align your generated messages with this repository's established tone, formatting, and naming style.\n"
        )

    prompt = (
        "Generate exactly 3 distinct, high-quality commit message options for the following git diff "
        "using Conventional Commits format (e.g., feat:, fix:, docs:, refactor:, style:).\n\n"
        "Option 1: Short and concise.\n"
        "Option 2: Scoped and descriptive (e.g. feat(auth): ...).\n"
        "Option 3: Action-oriented summary.\n"
        f"{style_context}\n"
        'Output ONLY a valid JSON array of 3 strings, e.g.: ["feat: update login UI", "feat(auth): add JWT handling", "refactor: clean up user auth"]. '
        "Do NOT include markdown formatting or extra text.\n\n"
        f"Diff:\n{diff_text}"
    )

    payload = json.dumps({
        "model": model_name,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_predict": num_predict,
            "temperature": temperature
        }
    }).encode("utf-8")

    headers = {"Content-Type": "application/json"}

    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(api_endpoint, data=payload, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=timeout_sec) as response:
                response_data = json.loads(response.read().decode("utf-8"))
                raw_text = response_data.get("response", "").strip()
                done_reason = response_data.get("done_reason")
                
                options = parse_options_from_response(raw_text)
                if options:
                    return options

                if done_reason == "length":
                    print("\n[Warning] Model reached maximum token generation limit.")
                    print("Reasoning models require more tokens. Try increasing OLLAMA_NUM_PREDICT in .env (e.g. 1500).")

        except urllib.error.HTTPError as e:
            if e.code == 404:
                print(f"\n[Error 404] Model '{model_name}' was not found on Ollama at {host_url}.")
                print(f"Please check your .env file or run 'ollama pull {model_name}'.")
                print("Run 'ollama list' in your terminal to view currently installed models.")
                sys.exit(1)
            if attempt < max_retries - 1:
                print(f"[Attempt {attempt + 1}/{max_retries}] HTTP error ({e}). Retrying in 2 seconds...")
                time.sleep(2)
            else:
                print(f"\nError communicating with Ollama: {e}")
                sys.exit(1)
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
    if not raw_text:
        return []

    # Strip thinking/reasoning tags (e.g. <think>...</think>) from reasoning models
    cleaned = re.sub(r"<think>[\s\S]*?</think>", "", raw_text).strip()

    # 1. Strip markdown code fences if wrapped in ``` or ```json
    cleaned_fences = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned_fences = re.sub(r"\s*```$", "", cleaned_fences).strip()

    # Try parsing JSON array directly
    try:
        data = json.loads(cleaned_fences)
        if isinstance(data, list) and len(data) > 0:
            return [str(item).strip() for item in data if str(item).strip()][:3]
    except Exception:
        pass

    # 2. Try regex extraction of JSON array [...] anywhere in the text
    json_match = re.search(r"\[\s*\"(?:\\.|[^\"])*\"[\s\S]*?\]", cleaned)
    if json_match:
        try:
            data = json.loads(json_match.group(0))
            if isinstance(data, list) and len(data) > 0:
                return [str(item).strip() for item in data if str(item).strip()][:3]
        except Exception:
            pass

    # 3. Fallback: Parse line-by-line (e.g. 1. msg, 2. msg, or - msg)
    lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
    parsed = []
    for line in lines:
        cleaned_line = re.sub(r"^(\d+[\.\)]|\-|\*)\s*", "", line).strip().strip('"\'')
        if cleaned_line and len(cleaned_line) > 3 and not cleaned_line.startswith("```"):
            parsed.append(cleaned_line)
    
    if parsed:
        return parsed[:3]
    
    # 4. Last fallback: return raw text as single option if non-empty
    single = cleaned.strip().strip('"\'[]')
    return [single] if single else []
