import os

def load_environment():
    """Loads environment variables from .env file using pure Python stdlib."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Since config.py is inside 'Logic', go up one level to find .env
    env_path = os.path.join(os.path.dirname(script_dir), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ[key.strip()] = val.strip().strip("'\"")
