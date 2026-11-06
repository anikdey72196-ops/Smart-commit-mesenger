import subprocess
import os
from ui_utils import print_success, print_warning, print_error

def is_git_repo():
    """Check if current directory is inside a git repo."""
    result = subprocess.run(
        ["git", "rev-parse", "--git-dir"],
        capture_output=True, text=True, encoding='utf-8', errors='replace'
    )
    return result.returncode == 0

def get_current_branch():
    """Returns active git branch name."""
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True, text=True, encoding='utf-8', errors='replace'
    )
    return result.stdout.strip()

def get_default_remote():
    """Returns default git remote (usually 'origin')."""
    result = subprocess.run(
        ["git", "remote"],
        capture_output=True, text=True, encoding='utf-8', errors='replace'
    )
    remotes = [r.strip() for r in result.stdout.splitlines() if r.strip()]
    if remotes:
        return "origin" if "origin" in remotes else remotes[0]
    return "origin"

def get_upstream_branch(remote=None):
    """Returns upstream tracking branch name if configured, e.g. 'origin/main', or None."""
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"],
        capture_output=True, text=True, encoding='utf-8', errors='replace'
    )
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()
    return None

def get_local_branches():
    """Returns a list of local branch names."""
    result = subprocess.run(
        ["git", "branch", "--format=%(refname:short)"],
        capture_output=True, text=True, encoding='utf-8', errors='replace'
    )
    if result.returncode != 0:
        return []
    return [b.strip() for b in result.stdout.splitlines() if b.strip()]

def get_remote_branches(remote="origin"):
    """Returns a list of remote branch names, excluding HEAD pointers."""
    if not remote:
        remote = get_default_remote()
    result = subprocess.run(
        ["git", "branch", "-r", "--format=%(refname:short)"],
        capture_output=True, text=True, encoding='utf-8', errors='replace'
    )
    if result.returncode != 0:
        return []
    branches = []
    for line in result.stdout.splitlines():
        b = line.strip()
        if b and b != remote and not b.endswith("/HEAD"):
            branches.append(b)
    return branches

def switch_branch(branch_name, create=False):
    """
    Switches to branch_name. If create=True, creates a new branch via checkout -b.
    Returns (success: bool, message: str)
    """
    branch_name = branch_name.strip()
    if not branch_name:
        return False, "Branch name cannot be empty."

    cmd = ["git", "checkout", "-b", branch_name] if create else ["git", "checkout", branch_name]
    result = subprocess.run(
        cmd,
        capture_output=True, text=True, encoding='utf-8', errors='replace'
    )
    if result.returncode == 0:
        return True, result.stdout.strip() or f"Switched to branch '{branch_name}'."
    return False, (result.stderr or result.stdout).strip()

def fetch_remote(remote=None, timeout=12):
    """
    Fetches latest updates from remote repository.
    Returns True if fetch succeeded, False if remote is unreachable or network is offline.
    """
    if not remote:
        remote = get_default_remote()
    try:
        result = subprocess.run(
            ["git", "fetch", remote, "--prune"],
            capture_output=True, text=True, encoding='utf-8', errors='replace',
            timeout=timeout
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, Exception):
        return False

def get_incoming_commits(branch_name=None, remote=None):
    """
    Returns list of commits pushed to remote by teammates that are not in local branch.
    Each item: {"hash": str, "author": str, "time": str, "message": str}
    """
    if not remote:
        remote = get_default_remote()
    active_branch = branch_name or get_current_branch()

    upstream = get_upstream_branch()
    target_ref = upstream if (upstream and not branch_name) else f"{remote}/{active_branch}"

    cmd = ["git", "log", f"HEAD..{target_ref}", "--pretty=format:%h|%an|%cr|%s"]
    result = subprocess.run(
        cmd,
        capture_output=True, text=True, encoding='utf-8', errors='replace'
    )
    if result.returncode != 0:
        return []

    commits = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("|", 3)
        if len(parts) == 4:
            commits.append({
                "hash": parts[0].strip(),
                "author": parts[1].strip(),
                "time": parts[2].strip(),
                "message": parts[3].strip()
            })
    return commits

def has_uncommitted_changes():
    """Returns True if there are modified, staged, or untracked files."""
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True, text=True, encoding='utf-8', errors='replace'
    )
    return bool(result.stdout.strip())

def stash_changes(message="smartcommit-autostash"):
    """Stashes current changes including untracked files."""
    if not has_uncommitted_changes():
        return False
    result = subprocess.run(
        ["git", "stash", "push", "-u", "-m", message],
        capture_output=True, text=True, encoding='utf-8', errors='replace'
    )
    return result.returncode == 0 and "Saved working directory" in (result.stdout or "")

def pop_stash():
    """Restores the most recent stash."""
    result = subprocess.run(
        ["git", "stash", "pop"],
        capture_output=True, text=True, encoding='utf-8', errors='replace'
    )
    if result.returncode == 0:
        return True, result.stdout.strip()
    return False, (result.stderr or result.stdout).strip()

def get_conflicted_files():
    """Returns list of unmerged / conflicted file paths."""
    result = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=U"],
        capture_output=True, text=True, encoding='utf-8', errors='replace'
    )
    if result.returncode != 0:
        return []
    return [f.strip() for f in result.stdout.splitlines() if f.strip()]

def get_conflict_diff():
    """Returns raw diff text containing conflict markers."""
    result = subprocess.run(
        ["git", "diff", "--diff-filter=U"],
        capture_output=True, text=True, encoding='utf-8', errors='replace'
    )
    return result.stdout.strip()

def abort_merge():
    """Aborts an in-progress merge and restores working tree."""
    result = subprocess.run(
        ["git", "merge", "--abort"],
        capture_output=True, text=True, encoding='utf-8', errors='replace'
    )
    if result.returncode == 0:
        return True, "Merge aborted successfully."
    return False, (result.stderr or result.stdout).strip()

def merge_branch(source_branch, auto_stash=True):
    """
    Merges source_branch (e.g. 'origin/main', 'feature/friend-branch') into current branch.
    Safely stashes uncommitted local changes if auto_stash is True and restores them after.
    Returns: {"success": bool, "conflicts": list, "message": str, "stashed": bool}
    """
    stashed = False
    if auto_stash and has_uncommitted_changes():
        stashed = stash_changes("smartcommit-auto-merge-stash")

    cmd = ["git", "merge", source_branch]
    result = subprocess.run(
        cmd,
        capture_output=True, text=True, encoding='utf-8', errors='replace'
    )

    if result.returncode == 0:
        stash_note = ""
        if stashed:
            pop_ok, pop_err = pop_stash()
            if not pop_ok:
                stash_note = f" (Note: Unstashing needs manual resolution: {pop_err})"
        return {
            "success": True,
            "conflicts": [],
            "message": (result.stdout.strip() or "Merged successfully") + stash_note,
            "stashed": stashed
        }

    # Conflict or merge error
    conflicts = get_conflicted_files()
    return {
        "success": False,
        "conflicts": conflicts,
        "message": (result.stderr or result.stdout).strip(),
        "stashed": stashed
    }

def get_diff(staged=True):
    """Return git diff as string."""
    if staged:
        cmd = ["git", "diff", "--staged"]
    else:
        cmd = ["git", "diff"]

    result = subprocess.run(
        cmd,
        capture_output=True, text=True, encoding='utf-8', errors='replace'
    )
    return result.stdout

def get_diff_stats():
    """Return short stats of changes (files changed, insertions, deletions)."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--stat"],
        capture_output=True, text=True, encoding='utf-8', errors='replace'
    )
    out = result.stdout.strip()
    if not out:
        result = subprocess.run(
            ["git", "diff", "--stat"],
            capture_output=True, text=True, encoding='utf-8', errors='replace'
        )
        out = result.stdout.strip()
    return out

def get_recent_commits(limit=5):
    """Fetch recent commit messages to understand repository naming conventions and style."""
    try:
        result = subprocess.run(
            ["git", "log", f"-n", str(limit * 2), "--pretty=format:%s"],
            capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
        if result.returncode != 0:
            return []

        commits = []
        for line in result.stdout.splitlines():
            line = line.strip()
            if line and not line.lower().startswith(("merge branch", "merge pull request", "merge remote-tracking")):
                commits.append(line)
            if len(commits) >= limit:
                break
        return commits
    except Exception:
        return []

def commit_and_push(commit_msg, used_unstaged, target_branch=None, remote=None, only_push=False):
    """
    Commits changes locally and pushes to remote.
    Supports targeting custom remote branches and handles upstream setup or non-fast-forward collisions.
    Returns status dict: {"success": bool, "message": str, "rejected_non_fast_forward": bool, "error": str}
    """
    if not remote:
        remote = get_default_remote()
    active_branch = get_current_branch()
    branch_to_push = target_branch if target_branch else active_branch

    # 1. Commit locally if not only_push
    if not only_push:
        if used_unstaged:
            # Stage all files including newly created untracked files
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        else:
            subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        print_success("Committed locally!")

    # 2. Push to remote
    print(f"🚀 Pushing to remote repository ({remote}/{branch_to_push})...")
    push_cmd = (
        ["git", "push", remote, f"{active_branch}:{branch_to_push}"]
        if branch_to_push != active_branch
        else ["git", "push", remote, active_branch]
    )

    result = subprocess.run(
        push_cmd,
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )

    err = (result.stderr or "") + (result.stdout or "")

    if result.returncode == 0:
        print_success(f"Pushed to {remote}/{branch_to_push} successfully!")
        return {"success": True, "message": f"Pushed to {remote}/{branch_to_push}"}

    # 3. Check if upstream needs to be set (-u)
    if "no upstream branch" in err or "set-upstream" in err or result.returncode == 128:
        print_warning(f"First push detected for branch '{branch_to_push}'. Setting upstream...")
        up_cmd = (
            ["git", "push", "-u", remote, f"{active_branch}:{branch_to_push}"]
            if branch_to_push != active_branch
            else ["git", "push", "-u", remote, active_branch]
        )
        up_res = subprocess.run(
            up_cmd,
            capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
        if up_res.returncode == 0:
            print_success(f"Pushed and linked upstream for '{remote}/{branch_to_push}'!")
            return {"success": True, "message": "Upstream linked and pushed"}
        err = (up_res.stderr or "") + (up_res.stdout or "")

    # 4. Check if rejected due to non-fast-forward (friend pushed concurrent commits)
    if "fetch first" in err.lower() or "non-fast-forward" in err.lower() or "[rejected]" in err.lower():
        return {
            "success": False,
            "rejected_non_fast_forward": True,
            "branch": branch_to_push,
            "error": err.strip()
        }

    print_error(f"Failed to push to remote: {err.strip()}")
    return {"success": False, "rejected_non_fast_forward": False, "error": err.strip()}
