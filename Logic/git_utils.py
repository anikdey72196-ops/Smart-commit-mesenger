import subprocess

def is_git_repo():
    """Check if current directory is inside a git repo."""
    result = subprocess.run(["git", "rev-parse", "--git-dir"],
                            capture_output=True, text=True, encoding='utf-8', errors='replace')
    return result.returncode == 0

def has_untracked_files():
    """Returns True if there are new untracked files in the repo."""
    result = subprocess.run(["git", "ls-files", "--others", "--exclude-standard"],
                            capture_output=True, text=True, encoding='utf-8', errors='replace')
    return bool(result.stdout.strip())

def stage_all():
    """Automatically runs 'git add .' to stage all new and modified files."""
    subprocess.run(["git", "add", "."], check=True)
    print("New files detected! Automatically staged with 'git add .'")

def get_diff(staged=True):
    """Return git diff as string."""
    if staged:
        cmd = ["git", "diff", "--staged"]
    else:
        cmd = ["git", "diff"]

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

def get_current_branch():
    """Returns the current active git branch name."""
    result = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"],
                            capture_output=True, text=True, encoding='utf-8', errors='replace')
    return result.stdout.strip()

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
            branch_name = get_current_branch()
            print(f"\nFirst-time push detected for branch '{branch_name}'!")
            print(f"Automatically setting upstream and pushing to origin/{branch_name}...")
            try:
                subprocess.run(["git", "push", "-u", "origin", branch_name], check=True)
                print("Pushed and linked upstream successfully!")
            except Exception as push_err:
                print(f"Failed to auto-push upstream: {push_err}")
        else:
            print(f"Failed to push to remote: {e}")
    except Exception as e:
        print(f"Failed to push to remote: {e}")
