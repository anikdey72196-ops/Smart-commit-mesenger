import sys
import argparse
from config import load_environment
from git_utils import is_git_repo, get_diff, get_diff_stats, commit_and_push
from ai_utils import generate_commit_options
from logger import log_commit

def main():
    parser = argparse.ArgumentParser(description="Smart commit message generator")
    parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation and auto-select first option")
    parser.add_argument("--dry-run", action="store_true", help="Only show messages, don't commit")
    
    args = parser.parse_args()

    # 1. Load Environment Variables (e.g. API keys if added later)
    load_environment()

    # 2. Validate git repository
    if not is_git_repo():
        print("Error: Not a git repository.")
        sys.exit(1)
        
    # 3. Get changes (staged first, fallback to unstaged)
    diff_text = get_diff(staged=True)
    used_unstaged = False
    if not diff_text.strip():
        diff_text = get_diff(staged=False)
        used_unstaged = True

    if not diff_text.strip():
        print("No changes to commit.")
        sys.exit(0)

    # 4. Show diff stats before generating
    stats = get_diff_stats()
    print(f"\nChanges detected:\n{stats}\n")

    # 5. Truncate diff if too long to prevent LLM overload
    if len(diff_text) > 3000:
        diff_text = diff_text[:3000] + "\n... (truncated)"

    # 6. Generate commit options using AI
    print("🤖 Thinking and generating commit message options...\n")
    options = generate_commit_options(diff_text)

    if not options:
        print("Error: Could not generate commit message options.")
        sys.exit(1)

    print("Suggested commit message options:")
    for idx, opt in enumerate(options, 1):
        print(f"  [{idx}] {opt}")
    print("  [e] Edit / Enter custom message")
    print("  [c] Cancel commit")
    print()

    if args.dry_run:
        print("[Dry run] Not committing.")
        sys.exit(0)

    # 7. Select option or accept custom input
    if args.yes:
        selected_msg = options[0]
        print(f"Auto-selected option [1]: {selected_msg}")
    else:
        choice = input(f"Select an option (1-{len(options)}, e, c) [default 1]: ").strip().lower()
        if choice in ["", "1"]:
            selected_msg = options[0]
        elif choice == "2" and len(options) >= 2:
            selected_msg = options[1]
        elif choice == "3" and len(options) >= 3:
            selected_msg = options[2]
        elif choice in ["e", "edit"]:
            custom_msg = input("Enter your custom commit message: ").strip()
            if not custom_msg:
                print("No message entered. Commit cancelled.")
                sys.exit(0)
            selected_msg = custom_msg
        elif choice in ["c", "cancel", "n", "no"]:
            print("Commit cancelled.")
            sys.exit(0)
        else:
            print("Invalid selection. Commit cancelled.")
            sys.exit(0)

    # 8. Execute Commit, Push, and Log
    commit_and_push(selected_msg, used_unstaged)
    log_commit(selected_msg)

if __name__ == "__main__":
    main()