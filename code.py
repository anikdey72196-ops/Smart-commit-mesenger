import subprocess
import sys
import argparse
import os
from google import genai

# Load environment variables if dotenv is installed
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def is_git_repo():
    """Check if current directory is inside a git repo."""
    result = subprocess.run(["git", "rev-parse", "--git-dir"],
                            capture_output=True, text=True)
    return result.returncode == 0

def get_diff(staged=True):
    """Return git diff as string."""
    if staged:
        cmd = ["git", "diff", "--cached"]
    else:
        cmd = ["git", "diff"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout

def get_diff_stats():
    """Return short stats of changes (files changed, insertions, deletions)."""
    result = subprocess.run(["git", "diff", "--cached", "--stat"],
                            capture_output=True, text=True)
    if not result.stdout.strip():
        result = subprocess.run(["git", "diff", "--stat"],
                                capture_output=True, text=True)
    return result.stdout.strip()

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

    # Generate commit message using Gemini
    try:
        client = genai.Client()  # expects GOOGLE_API_KEY env var
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f'Generate a short, one-line commit message for this git diff. '
                     f'Use Conventional Commits format (feat:, fix:, docs:, etc.). '
                     f'Only output the message, no extra text.\n\nDiff:\n{diff_text}'
        )
        commit_msg = response.text.strip()
    except Exception as e:
        print(f"Error generating commit message: {e}")
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
    else:
        print("Commit cancelled.")

if __name__ == "__main__":
    main()
    