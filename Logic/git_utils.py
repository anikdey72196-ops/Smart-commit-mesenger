import subprocess
from ui_utils import print_success, print_warning, print_error

def is_git_repo():
    """Check if current directory is inside a git repo."""
    result = subprocess.run(["git", "rev-parse", "--git-dir"],
                            capture_output=True, text=True, encoding='utf-8', errors='replace')
    return result.returncode == 0

def get_current_branch():
    """Returns active git branch name."""
    result = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"],
                            capture_output=True, text=True, encoding='utf-8', errors='replace')
    return result.stdout.strip()

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

def commit_and_push(commit_msg, used_unstaged):
    if used_unstaged:
        subprocess.run(["git", "commit", "-a", "-m", commit_msg], check=True)
    else:
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
    print_success("Committed locally!")
    
    # Automatically push to remote
    try:
        print("🚀 Pushing to remote repository...")
        subprocess.run(["git", "push"], check=True)
        print_success("Pushed to remote successfully!")
    except subprocess.CalledProcessError as e:
        if e.returncode == 128:
            branch_name = get_current_branch()
            print_warning(f"First push detected for branch '{branch_name}'. Attempting auto-upstream setup...")
            try:
                subprocess.run(["git", "push", "-u", "origin", branch_name], check=True)
                print_success(f"Pushed and linked upstream for 'origin/{branch_name}'!")
            except Exception as push_err:
                print_error(f"Failed to push upstream: {push_err}")
        else:
            print_error(f"Failed to push to remote: {e}")
    except Exception as e:
        print_error(f"Failed to push to remote: {e}")

