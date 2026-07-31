import subprocess

def is_git_repo():
    """Check if current directory is inside a git repo."""
    result = subprocess.run(["git", "rev-parse", "--git-dir"],
                            capture_output=True, text=True, encoding='utf-8', errors='replace')
    return result.returncode == 0

def get_diff(staged=True):
    """Return git diff as string."""
    if staged:
        cmd = ["git", "diff", "--staged"]# Show staged changes (what you have 'git add' ed and are about to commit)
    else:
        cmd = ["git", "diff"]   # Show unstaged changes (what you have modified but not yet run 'git add' on)

    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    return result.stdout

def get_diff_stats():
    """Return short stats of changes (files changed, insertions, deletions)."""
    result = subprocess.run(["git", "diff", "--cached", "--stat"],
                            capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = result.stdout.strip()
    if not out:
        result = subprocess.run(["git", "diff", "--stat"],
                                capture_output=True, text=True, encoding='utf-8', errors='replace')
        out = result.stdout.strip()
    return out

def commit_and_push(commit_msg, used_unstaged):
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
    except subprocess.CalledProcessError as e:
        if e.returncode == 128:
            print("fatal: The current branch has no upstream branch.")
            print("For the first push of a new branch, you must manually run:")
            print("    git push -u origin <branch-name>")
        else:
            print(f"Failed to push to remote: {e}")
    except Exception as e:
        print(f"Failed to push to remote: {e}")
