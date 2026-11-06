import sys
import argparse
from config import load_environment
from git_utils import (
    is_git_repo,
    get_current_branch,
    get_upstream_branch,
    get_local_branches,
    get_remote_branches,
    switch_branch,
    fetch_remote,
    get_incoming_commits,
    merge_branch,
    abort_merge,
    get_conflict_diff,
    get_diff,
    get_diff_stats,
    get_recent_commits,
    commit_and_push
)
from ai_utils import generate_commit_options, explain_merge_conflicts
from logger import log_commit
from security_utils import scan_diff_for_secrets, print_security_report
from ui_utils import (
    print_banner,
    print_diff_stats,
    print_options,
    print_incoming_commits,
    print_branch_status,
    print_branch_list,
    print_conflict_report,
    print_conflict_options,
    print_success,
    print_warning,
    print_error,
    Spinner
)

def handle_conflict_resolution(conflicts):
    """Interactively handles merge conflicts with manual, AI-assisted, or abort options."""
    print_conflict_report(conflicts)
    print_conflict_options()

    choice = input("Select resolution option [1-3, default 1]: ").strip()
    if choice == "2":
        diff = get_conflict_diff()
        with Spinner("Analyzing merge conflict with AI..."):
            explanation = explain_merge_conflicts(conflicts, diff)
        print("\n" + explanation + "\n")

        post_choice = input("Keep conflict markers to edit in code editor? (Y/n, 'n' to abort): ").strip().lower()
        if post_choice in ["n", "no"]:
            abort_merge()
            print_warning("Merge aborted. Working tree restored to previous clean state.")
            return False
        else:
            print_warning("Conflict markers kept. Open your code editor, resolve conflict markers, and commit.")
            return False
    elif choice == "3":
        abort_merge()
        print_warning("Merge aborted. Working tree restored to previous clean state.")
        return False
    else:
        print_warning("Conflict markers kept in files. Please resolve them in your code editor and commit.")
        return False

def run_merge_workflow(current_branch, source_branch=None):
    """Runs the Merging Agent workflow to merge another branch into current_branch."""
    if not source_branch:
        with Spinner("Fetching latest branch information..."):
            fetch_remote()

        local_branches = get_local_branches()
        remote_branches = get_remote_branches()

        all_candidates = [b for b in local_branches if b != current_branch]
        for rb in remote_branches:
            if rb != f"origin/{current_branch}" and rb not in all_candidates:
                all_candidates.append(rb)

        if not all_candidates:
            print_warning("No other local or remote branches found to merge.")
            return False

        print_branch_list(all_candidates, current_branch=None)
        sel = input("Select branch number or enter branch name to merge (or 'c' to cancel): ").strip()
        if sel.lower() in ["c", "cancel", ""]:
            print_warning("Merge cancelled.")
            return False

        if sel.isdigit() and 1 <= int(sel) <= len(all_candidates):
            source_branch = all_candidates[int(sel) - 1]
        else:
            source_branch = sel

    print(f"🔄 Merging '{source_branch}' into '{current_branch}'...")
    res = merge_branch(source_branch, auto_stash=True)
    if res["success"]:
        print_success(f"Successfully merged '{source_branch}' into '{current_branch}'!")
        return True

    return handle_conflict_resolution(res["conflicts"])

def check_and_sync_teammates(current_branch, auto_yes=False):
    """Checks for incoming commits from teammates on remote and prompts to merge."""
    with Spinner("Checking remote for teammate updates..."):
        fetch_remote()
        incoming = get_incoming_commits(current_branch)

    if not incoming:
        return True

    upstream = get_upstream_branch() or f"origin/{current_branch}"
    print_incoming_commits(incoming, upstream)

    if auto_yes:
        do_merge = True
    else:
        ans = input(f"🔔 Teammate pushed {len(incoming)} commit(s). Merge them now? (Y/n): ").strip().lower()
        do_merge = ans in ["", "y", "yes"]

    if do_merge:
        print(f"🔄 Merging teammate's commits from '{upstream}'...")
        res = merge_branch(upstream, auto_stash=True)
        if res["success"]:
            print_success(f"Teammate commits successfully merged into '{current_branch}'!")
            return True
        else:
            return handle_conflict_resolution(res["conflicts"])
    else:
        print_warning("Skipped merging teammate commits.")
        return True

def main():
    parser = argparse.ArgumentParser(
        description="Smart commit message generator & Git collaborative merging agent"
    )
    parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation and auto-select first option")
    parser.add_argument("--dry-run", action="store_true", help="Only show messages, don't commit")
    parser.add_argument("--no-verify", "--skip-security", dest="no_verify", action="store_true", help="Bypass pre-commit security & secret scan")
    parser.add_argument("-b", "--branch", dest="branch", type=str, help="Switch to an existing branch before committing")
    parser.add_argument("-B", "--new-branch", dest="new_branch", type=str, help="Create and switch to a new branch before committing")
    parser.add_argument("-m", "--merge", dest="merge_branch", nargs="?", const="", default=None, help="Merge a branch (friend's branch or remote) into current branch")
    parser.add_argument("--sync", "--pull", dest="sync_remote", action="store_true", help="Sync/pull latest teammate commits from remote")
    parser.add_argument("--no-sync", "--skip-sync", dest="no_sync", action="store_true", help="Skip checking remote for teammate commits")
    parser.add_argument("--target-branch", dest="target_branch", type=str, help="Target remote branch to push commits to")

    args = parser.parse_args()

    # 1. Load Environment Variables
    load_environment()

    # 2. Print Stylish Banner
    print_banner()

    # 3. Validate git repository
    if not is_git_repo():
        print_error("Error: Not a git repository.")
        sys.exit(1)

    current_branch = get_current_branch()

    # 4. Handle Direct Branch CLI Flags (-b or -B)
    if args.new_branch:
        ok, msg = switch_branch(args.new_branch, create=True)
        if ok:
            current_branch = get_current_branch()
            print_success(f"Created and switched to new branch '{current_branch}'!")
        else:
            print_error(f"Could not create branch '{args.new_branch}': {msg}")
            sys.exit(1)
    elif args.branch:
        ok, msg = switch_branch(args.branch, create=False)
        if ok:
            current_branch = get_current_branch()
            print_success(f"Switched to branch '{current_branch}'!")
        else:
            print_error(f"Could not switch to branch '{args.branch}': {msg}")
            sys.exit(1)

    # 5. Check Remote Teammate Commits & Sync
    if not args.no_sync:
        sync_ok = check_and_sync_teammates(current_branch, auto_yes=args.yes or args.sync_remote)
        if not sync_ok:
            # If conflicts were encountered and kept or aborted
            sys.exit(1)

    # 6. Direct Merge Agent Mode (--merge / -m)
    if args.merge_branch is not None:
        target = args.merge_branch if args.merge_branch.strip() else None
        merged = run_merge_workflow(current_branch, source_branch=target)
        if not merged:
            sys.exit(1)

    # 7. Interactive Branch Management (if not bypassed by flags)
    if not args.yes and not args.branch and not args.new_branch and args.merge_branch is None and not args.dry_run:
        upstream = get_upstream_branch()
        print_branch_status(current_branch, upstream)
        b_prompt = input(f"Work on branch '{current_branch}'? [Enter=Keep, (s)witch branch, (n)ew branch, (m)erge another branch]: ").strip().lower()
        if b_prompt in ["s", "switch"]:
            local_branches = get_local_branches()
            remote_branches = get_remote_branches()
            candidates = list(dict.fromkeys(local_branches + remote_branches))
            print_branch_list(candidates, current_branch)
            target = input("Enter branch number or name to switch to (or 'c' to cancel): ").strip()
            if target.lower() not in ["c", "cancel", ""]:
                if target.isdigit() and 1 <= int(target) <= len(candidates):
                    target_name = candidates[int(target) - 1]
                else:
                    target_name = target
                clean_target = target_name.split("/", 1)[-1] if "/" in target_name else target_name
                ok, msg = switch_branch(clean_target, create=False)
                if ok:
                    current_branch = get_current_branch()
                    print_success(f"Switched to branch '{current_branch}'!")
                else:
                    print_error(f"Could not switch to branch '{target_name}': {msg}")
                    sys.exit(1)
        elif b_prompt in ["n", "new"]:
            new_name = input("Enter name for new branch: ").strip()
            if not new_name:
                print_warning("No branch name provided. Staying on current branch.")
            else:
                ok, msg = switch_branch(new_name, create=True)
                if ok:
                    current_branch = get_current_branch()
                    print_success(f"Created and switched to new branch '{current_branch}'!")
                else:
                    print_error(f"Could not create branch '{new_name}': {msg}")
                    sys.exit(1)
        elif b_prompt in ["m", "merge"]:
            merged_ok = run_merge_workflow(current_branch)
            if not merged_ok:
                sys.exit(0)

    # 8. Get changes (staged first, fallback to unstaged)
    diff_text = get_diff(staged=True)
    used_unstaged = False
    if not diff_text.strip():
        diff_text = get_diff(staged=False)
        used_unstaged = True

    if not diff_text.strip():
        if args.merge_branch is not None:
            print_success("Merge completed. Working tree is clean and up to date.")
            sys.exit(0)

        print_warning("No staged or unstaged code changes detected to commit.")
        if not args.yes:
            run_merge = input("Would you like to sync teammate commits or merge another branch? (y/N): ").strip().lower()
            if run_merge in ["y", "yes"]:
                run_merge_workflow(current_branch)
        sys.exit(0)

    # 9. Pre-Commit Security & Secret Leak Guardrails
    if not args.no_verify:
        report = scan_diff_for_secrets(diff_text)
        if report["findings"]:
            print_security_report(report)
            if report["has_critical"]:
                print_error("CRITICAL: Sensitive files or secrets detected in your changes!")
            else:
                print_warning("WARNING: Debug statements or code smells detected in your changes.")

            confirm = input("Are you sure you want to proceed with this commit? (y/N): ").strip().lower()
            if confirm not in ["y", "yes"]:
                print_warning("Commit aborted for security reasons.")
                sys.exit(1)

    # 10. Show formatted diff stats
    stats = get_diff_stats()
    print_diff_stats(stats, branch_name=current_branch)

    # 11. Fetch recent repository commit messages for style matching
    recent_commits = get_recent_commits(limit=5)

    # 12. Truncate diff if too long to prevent LLM overload
    if len(diff_text) > 3000:
        diff_text = diff_text[:3000] + "\n... (truncated)"

    # 13. Generate commit options with Animated Spinner
    with Spinner("Analyzing diff & generating commit message options..."):
        options = generate_commit_options(diff_text, recent_commits=recent_commits)

    if not options:
        print_error("Error: Could not generate commit message options.")
        sys.exit(1)

    print_options(options)

    if args.dry_run:
        print_warning("[Dry run] Skipping commit & push.")
        sys.exit(0)

    # 14. Select option or accept custom input
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

    # 15. Ask About Target Branch Before Push
    target_push_branch = args.target_branch
    if not args.yes and not target_push_branch:
        push_prompt = input(f"Push commit to remote branch '{current_branch}'? [Enter=Yes, (o)ther branch, (s)kip]: ").strip()
        if push_prompt.lower() in ["s", "skip", "n", "no"]:
            commit_and_push(selected_msg, used_unstaged, target_branch=current_branch, only_push=False)
            print_warning("Skipped pushing to remote. Changes committed locally.")
            log_commit(selected_msg)
            sys.exit(0)
        elif push_prompt.lower() in ["o", "other"]:
            custom_b = input("Enter target remote branch name: ").strip()
            target_push_branch = custom_b if custom_b else current_branch
        else:
            target_push_branch = current_branch
    else:
        target_push_branch = target_push_branch or current_branch

    # 16. Execute Commit, Push, and Collision Recovery
    push_res = commit_and_push(selected_msg, used_unstaged, target_branch=target_push_branch)

    if not push_res.get("success"):
        # Handle teammate concurrent push collision
        if push_res.get("rejected_non_fast_forward"):
            print_warning(f"Push rejected: Teammates pushed new commits to '{target_push_branch}' while you were working.")
            retry_ans = input("Would you like to merge teammate commits and retry push? (Y/n): ").strip().lower()
            if retry_ans in ["", "y", "yes"]:
                fetch_remote()
                upstream_ref = f"origin/{target_push_branch}"
                m_res = merge_branch(upstream_ref, auto_stash=False)
                if m_res["success"]:
                    print_success("Merged teammate commits! Retrying push...")
                    retry_push = commit_and_push(None, used_unstaged=False, target_branch=target_push_branch, only_push=True)
                    if retry_push.get("success"):
                        log_commit(selected_msg)
                else:
                    handle_conflict_resolution(m_res["conflicts"])
        return

    log_commit(selected_msg)

if __name__ == "__main__":
    main()
