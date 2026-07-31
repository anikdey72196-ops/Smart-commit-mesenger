import sys
import argparse
from config import load_environment
from git_utils import is_git_repo, has_untracked_files, stage_all, get_diff, get_diff_stats, commit_and_push
from ai_utils import generate_commit_message
from logger import log_commit

def main():
    parser = argparse.ArgumentParser(description="Smart commit message generator")
    parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation")
    parser.add_argument("--dry-run", action="store_true", help="Only show message, don't commit")
    args = parser.parse_args()

    # 1. Load Environment Variables
    load_environment()

    # 2. Validate git repository
    if not is_git_repo():
        print("Error: Not a git repository.")
        sys.exit(1)

    # 3. Automatically detect and stage untracked files
    if has_untracked_files():
        stage_all()

    # 4. Get changes (staged first, fallback to unstaged)
    diff_text = get_diff(staged=True)
    used_unstaged = False
    if not diff_text.strip():
        diff_text = get_diff(staged=False)
        used_unstaged = True

    if not diff_text.strip():
        print("No changes to commit.")
        sys.exit(0)

    # 5. Show diff stats before generating
    stats = get_diff_stats()
    print(f"\nChanges detected:\n{stats}\n")

    # 6. Truncate diff if too long to prevent LLM overload
    if len(diff_text) > 3000:
        diff_text = diff_text[:3000] + "\n... (truncated)"

    # 7. Generate commit message using AI
    commit_msg = generate_commit_message(diff_text)

    if args.dry_run:
        print("\n[Dry run] Not committing.")
        sys.exit(0)

    # 8. Ask for confirmation
    if args.yes:
        confirm = 'y'
    else:
        confirm = input(f"Use this message? (y/n): ").lower()

    # 9. Execute Commit, Push, and Log
    if confirm == 'y' or confirm == 'yes':
        commit_and_push(commit_msg, used_unstaged)
        log_commit(commit_msg)
    else:
        print("Commit cancelled.")

if __name__ == "__main__":
    main()
