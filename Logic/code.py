import sys
import argparse
from config import load_environment
from git_utils import is_git_repo, get_current_branch, get_diff, get_diff_stats, commit_and_push
from ai_utils import generate_commit_options
from logger import log_commit
from ui_utils import (
    print_banner,
    print_diff_stats,
    print_options,
    print_success,
    print_warning,
    print_error,
    Spinner
)

def main():
    parser = argparse.ArgumentParser(description="Smart commit message generator")
    parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation and auto-select first option")
    parser.add_argument("--dry-run", action="store_true", help="Only show messages, don't commit")
    
    args = parser.parse_args()

    # 1. Load Environment Variables
    load_environment()

    # 2. Print Stylish Banner
    print_banner()

    # 3. Validate git repository
    if not is_git_repo():
        print_error("Error: Not a git repository.")
        sys.exit(1)
        
    branch_name = get_current_branch()

    # 4. Get changes (staged first, fallback to unstaged)
    diff_text = get_diff(staged=True)
    used_unstaged = False
    if not diff_text.strip():
        diff_text = get_diff(staged=False)
        used_unstaged = True

    if not diff_text.strip():
        print_warning("No staged or unstaged changes detected to commit.")
        sys.exit(0)

    # 5. Show formatted diff stats
    stats = get_diff_stats()
    print_diff_stats(stats, branch_name=branch_name)

    # 6. Truncate diff if too long to prevent LLM overload
    if len(diff_text) > 3000:
        diff_text = diff_text[:3000] + "\n... (truncated)"

    # 7. Generate commit options with Animated Spinner
    with Spinner("Analyzing diff & generating commit message options..."):
        options = generate_commit_options(diff_text)

    if not options:
        print_error("Error: Could not generate commit message options.")
        sys.exit(1)

    print_options(options)

    if args.dry_run:
        print_warning("[Dry run] Skipping commit & push.")
        sys.exit(0)

    # 8. Select option or accept custom input
    if args.yes:
        selected_msg = options[0]
        print_success(f"Auto-selected option [1]: {selected_msg}")
    else:
        choice = input(f"Select option (1-{len(options)}, e, c) [default 1]: ").strip().lower()
        if choice in ["", "1"]:
            selected_msg = options[0]
        elif choice == "2" and len(options) >= 2:
            selected_msg = options[1]
        elif choice == "3" and len(options) >= 3:
            selected_msg = options[2]
        elif choice in ["e", "edit"]:
            custom_msg = input("Enter your custom commit message: ").strip()
            if not custom_msg:
                print_warning("No message entered. Commit cancelled.")
                sys.exit(0)
            selected_msg = custom_msg
        elif choice in ["c", "cancel", "n", "no"]:
            print_warning("Commit cancelled.")
            sys.exit(0)
        else:
            print_error("Invalid selection. Commit cancelled.")
            sys.exit(0)

    # 9. Execute Commit, Push, and Log
    commit_and_push(selected_msg, used_unstaged)
    log_commit(selected_msg)

if __name__ == "__main__":
    main()
