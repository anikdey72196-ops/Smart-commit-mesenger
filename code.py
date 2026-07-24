
import subprocess 
import sys
import argparse
import os
import requests
import time
import csv
import datetime


script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, ".env")
try:
    from dotenv import load_dotenv
    # Always load the .env file from the same directory as this script
    load_dotenv(dotenv_path=env_path)
except ImportError:
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ[key.strip()] = val.strip().strip("'\"")

def is_git_repo():
    """Check if current directory is inside a git repo."""
    result = subprocess.run(["git", "rev-parse", "--git-dir"],
                            capture_output=True, text=True)
    return result.returncode == 0

def get_diff(staged=True):
    """Return git diff as string."""
    if staged:
        cmd = ["git", "diff", "--staged"]# Show staged changes (what you have 'git add' ed and are about to commit)
    else:
        cmd = ["git", "diff"]   # Show unstaged changes (what you have modified but not yet run 'git add' on)

    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout

def get_diff_stats():
    """Return short stats of changes (files changed, insertions, deletions)."""
    result = subprocess.run(["git", "diff", "--cached", "--stat"],
                            capture_output=True, text=True)
    out = result.stdout.strip()
    if not out:
        result = subprocess.run(["git", "diff", "--stat"],
                                capture_output=True, text=True)
        out = result.stdout.strip()
    return out

def main():
    parser = argparse.ArgumentParser(description="Smart commit message generator")
    parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation")
    parser.add_argument("--dry-run", action="store_true", help="Only show message, don't commit")
    args = parser.parse_args()

    # Validate git repository
    if not is_git_repo():
        print("Error: Not a git repository.")
        sys.exit(1)
    # Get staged changes first, fallback to unstaged
    diff_text = get_diff(staged=True)
    used_unstaged = False
    if not diff_text.strip():
        diff_text = get_diff(staged=False)
        used_unstaged = True

    if not diff_text.strip():
        print("No changes to commit.")
        sys.exit(0)

    # Show diff stats before generating
    stats = get_diff_stats()
    print(f"\nChanges detected:\n{stats}\n")

    # Truncate diff if too long
    if len(diff_text) > 3000:
        diff_text = diff_text[:3000] + "\n... (truncated)"

    # Generate commit message using local Ollama (Gemma 4)
    
    max_retries = 3
    commit_msg = None

    for attempt in range(max_retries):
        try:
            response = requests.post('http://localhost:11434/api/generate', json={
                "model": "qwen2.5-coder:7b",
                "prompt": f'Generate a short, one-line commit message for this git diff. '
                          f'Use Conventional Commits format (feat:, fix:, docs:, etc.). '
                          f'Only output the message, no extra text.\n\nDiff:\n{diff_text}',
                "stream": False
            })
            response.raise_for_status()
            commit_msg = response.json().get('response', '').strip()
            break
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Ollama busy or error (attempt {attempt + 1}/{max_retries}). Retrying in 3 seconds...")
                time.sleep(3)
            else:
                print(f"Error generating commit message with Ollama after {max_retries} attempts: {e}")
                print("Make sure Ollama is running in the background!")
                sys.exit(1)

    print(f"Suggested message: {commit_msg}")

    # Command-line argument handling with normal if-else (no ternary)
    if args.dry_run:
        print("\n[Dry run] Not committing.")
        sys.exit(0)

    if args.yes:
        confirm = 'y'
    else:
        confirm = input("Use this message? (y/n): ").lower()

    if confirm == 'y' or confirm == 'yes':
        if used_unstaged:
            subprocess.run(["git", "commit", "-a", "-m", commit_msg], check=True)
        else:
            subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        print("Committed!")
        
        # Automatically push to remote
        try:
            print("Pushing to remote...")
            subprocess.run(["git", "push"], check=True)
            print("Pushed successfully!")
        except Exception as e:
            print(f"Failed to push to remote: {e}")
        
        # Log this commit to the global CSV file
        try:
            repo_name = os.path.basename(os.path.abspath(os.getcwd()))
            owner_name = "anikdey72196"
            commit_date = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
            
            # Save the CSV in the same directory as this script (the master folder)
            csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "commit_history.csv")
            file_exists = os.path.isfile(csv_path)
            
            with open(csv_path, "a", newline="", encoding="utf-8") as csv_file:
                writer = csv.writer(csv_file)
                if not file_exists:
                    writer.writerow(["Owner", "Repository", "Date", "Message"])
                writer.writerow([owner_name, repo_name, commit_date, commit_msg])
        except Exception as e:
            print(f"Failed to save to CSV log: {e}")
            
    else:
        print("Commit cancelled.")

if __name__ == "__main__":
    main()
    