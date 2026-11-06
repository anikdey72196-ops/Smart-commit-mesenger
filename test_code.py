import unittest
import sys
import os
import json
import tempfile
from unittest.mock import patch, MagicMock

# Add Logic directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "Logic"))

import logger
from git_utils import (
    get_diff,
    get_recent_commits,
    get_current_branch,
    get_default_remote,
    get_local_branches,
    get_remote_branches,
    switch_branch,
    fetch_remote,
    get_incoming_commits,
    has_uncommitted_changes,
    stash_changes,
    pop_stash,
    merge_branch,
    abort_merge,
    get_conflicted_files,
    get_conflict_diff,
    commit_and_push
)
from ai_utils import parse_options_from_response, explain_merge_conflicts
from ui_utils import (
    print_incoming_commits,
    print_branch_status,
    print_branch_list,
    print_conflict_report,
    print_conflict_options
)
from logger import sanitize_for_csv, log_commit

class TestGitUtils(unittest.TestCase):
    @patch('subprocess.run')
    def test_get_diff_staged_true(self, mock_run):
        mock_result = MagicMock()
        mock_result.stdout = "staged diff output"
        mock_run.return_value = mock_result

        result = get_diff(staged=True)
        self.assertEqual(result, "staged diff output")

    @patch('subprocess.run')
    def test_get_diff_staged_false(self, mock_run):
        mock_result = MagicMock()
        mock_result.stdout = "unstaged diff output"
        mock_run.return_value = mock_result

        result = get_diff(staged=False)
        self.assertEqual(result, "unstaged diff output")

    @patch('subprocess.run')
    def test_get_recent_commits_filters_merges_and_limits(self, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = (
            "refactor: update Ollama config\n"
            "Merge branch 'main' of repo\n"
            "feat: add CLI spinner\n"
            "Merge pull request #1 from user/branch\n"
            "fix: sanitize csv\n"
            "docs: update readme\n"
        )
        mock_run.return_value = mock_result

        commits = get_recent_commits(limit=3)
        self.assertEqual(len(commits), 3)
        self.assertEqual(commits, ["refactor: update Ollama config", "feat: add CLI spinner", "fix: sanitize csv"])

class TestAIUtils(unittest.TestCase):
    def test_parse_json_array(self):
        json_input = '["feat: add login", "feat(auth): JWT validation", "refactor: clean auth logic"]'
        options = parse_options_from_response(json_input)
        self.assertEqual(len(options), 3)
        self.assertEqual(options[0], "feat: add login")
        self.assertEqual(options[1], "feat(auth): JWT validation")
        self.assertEqual(options[2], "refactor: clean auth logic")

    def test_parse_markdown_json_block(self):
        markdown_input = '```json\n["feat: add login", "fix: resolve bug"]\n```'
        options = parse_options_from_response(markdown_input)
        self.assertEqual(len(options), 2)
        self.assertEqual(options[0], "feat: add login")

    def test_parse_numbered_list(self):
        list_input = "1. feat: option one\n2. fix: option two\n3. docs: option three"
        options = parse_options_from_response(list_input)
        self.assertEqual(len(options), 3)
        self.assertEqual(options[0], "feat: option one")

    def test_parse_reasoning_think_tags(self):
        think_input = '<think>\nAnalyzing the git diff...\nNeed 3 options.\n</think>\n["feat: add login", "fix: resolve bug"]'
        options = parse_options_from_response(think_input)
        self.assertEqual(len(options), 2)
        self.assertEqual(options[0], "feat: add login")
        self.assertEqual(options[1], "fix: resolve bug")

    def test_parse_embedded_json_in_text(self):
        conversational_input = 'Here are 3 Conventional Commit options based on your diff:\n```json\n["feat: add login", "fix: resolve bug"]\n```\nLet me know if you need more!'
        options = parse_options_from_response(conversational_input)
        self.assertEqual(len(options), 2)
        self.assertEqual(options[0], "feat: add login")

    def test_parse_empty_input(self):
        self.assertEqual(parse_options_from_response(""), [])
        self.assertEqual(parse_options_from_response(None), [])

    @patch('urllib.request.urlopen')
    def test_generate_commit_options_stdlib(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"response": '["feat: stdlib test"]'}).encode('utf-8')
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        from ai_utils import generate_commit_options
        options = generate_commit_options("dummy diff")
        self.assertEqual(options, ["feat: stdlib test"])

    @patch('urllib.request.urlopen')
    def test_generate_commit_options_with_recent_commits(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"response": '["feat: style matched"]'}).encode('utf-8')
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        from ai_utils import generate_commit_options
        recent = ["feat(auth): add JWT tokens", "fix(db): handle pool leak"]
        options = generate_commit_options("dummy diff", recent_commits=recent)
        self.assertEqual(options, ["feat: style matched"])

        # Verify that prompt includes the recent commit history for style reference
        call_args = mock_urlopen.call_args
        req = call_args[0][0]
        payload = json.loads(req.data.decode("utf-8"))
        self.assertIn("Recent commit messages in this repository", payload["prompt"])
        self.assertIn("feat(auth): add JWT tokens", payload["prompt"])
        self.assertIn("fix(db): handle pool leak", payload["prompt"])

class TestLoggerUtils(unittest.TestCase):
    def test_sanitize_for_csv(self):
        self.assertEqual(sanitize_for_csv("=1+2"), "'=1+2")
        self.assertEqual(sanitize_for_csv("+cmd|' /C calc'!A0"), "'+cmd|' /C calc'!A0")
        self.assertEqual(sanitize_for_csv("-100"), "'-100")
        self.assertEqual(sanitize_for_csv("@SUM(A1:A10)"), "'@SUM(A1:A10)")
        self.assertEqual(sanitize_for_csv("\tval"), "'\tval")
        self.assertEqual(sanitize_for_csv("\rval"), "'\rval")
        self.assertEqual(sanitize_for_csv("Normal message"), "Normal message")
        self.assertEqual(sanitize_for_csv(123), 123)

    def test_log_commit_sanitizes_formula(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            dummy_script_dir = os.path.join(tmp_dir, "Logic")
            os.makedirs(dummy_script_dir, exist_ok=True)
            dummy_logger_file = os.path.join(dummy_script_dir, "logger.py")

            with patch.object(logger, '__file__', dummy_logger_file):
                log_commit("=SUM(1,2)")
                csv_path = os.path.join(tmp_dir, "commit_history.csv")
                self.assertTrue(os.path.isfile(csv_path))
                with open(csv_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    self.assertIn("'=SUM(1,2)", content)

from security_utils import scan_diff_for_secrets, mask_secret

class TestSecurityUtils(unittest.TestCase):
    def test_mask_secret(self):
        self.assertEqual(mask_secret("short"), "****")
        self.assertEqual(mask_secret("AKIA1234567890EXAMPLE"), "AKIA*************MPLE")

    def test_clean_diff_no_findings(self):
        diff = (
            "diff --git a/app.py b/app.py\n"
            "--- a/app.py\n"
            "+++ b/app.py\n"
            "@@ -1 +1 @@\n"
            "+print('hello world')\n"
        )
        report = scan_diff_for_secrets(diff)
        self.assertFalse(report["has_critical"])
        self.assertFalse(report["has_warnings"])
        self.assertEqual(len(report["findings"]), 0)

    def test_detect_sensitive_file(self):
        diff = (
            "diff --git a/.env b/.env\n"
            "--- /dev/null\n"
            "+++ b/.env\n"
            "@@ -0,0 +1 @@\n"
            "+SECRET=12345\n"
        )
        report = scan_diff_for_secrets(diff)
        self.assertTrue(report["has_critical"])
        self.assertTrue(any(f["type"] == "SENSITIVE_FILE" for f in report["findings"]))

    def test_ignore_example_env_file(self):
        diff = (
            "diff --git a/.env.example b/.env.example\n"
            "--- /dev/null\n"
            "+++ b/.env.example\n"
            "@@ -0,0 +1 @@\n"
            "+OLLAMA_MODEL=model\n"
        )
        report = scan_diff_for_secrets(diff)
        self.assertFalse(report["has_critical"])

    def test_detect_api_keys(self):
        gh_sample = "gh" + "p_ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"
        google_sample = "AI" + "zaSyD-1234567890abcdefghijklmnopqrst"
        openai_sample = "s" + "k-abcdefghijklmnopqrstuvwxyz12345"
        aws_sample = "AK" + "IAIOSFODNN7EXAMPLE"
        diff = (
            "diff --git a/config.py b/config.py\n"
            "--- a/config.py\n"
            "+++ b/config.py\n"
            f"@@ -1 +1,4 @@\n"
            f"+gh_token = '{gh_sample}'\n"
            f"+google_key = '{google_sample}'\n"
            f"+openai_key = '{openai_sample}'\n"
            f"+aws_key = '{aws_sample}'\n"
        )
        report = scan_diff_for_secrets(diff)
        self.assertTrue(report["has_critical"])
        secret_findings = [f for f in report["findings"] if f["type"] == "SECRET"]
        self.assertEqual(len(secret_findings), 4)

    def test_detect_debug_statements(self):
        c_log = "console." + "log"
        d_bug = "debug" + "ger;"
        diff = (
            "diff --git a/debug.js b/debug.js\n"
            "--- a/debug.js\n"
            "+++ b/debug.js\n"
            f"@@ -1 +1,2 @@\n"
            f"+{c_log}('debugging value');\n"
            f"+{d_bug}\n"
        )
        report = scan_diff_for_secrets(diff)
        self.assertFalse(report["has_critical"])
        self.assertTrue(report["has_warnings"])
        debug_findings = [f for f in report["findings"] if f["type"] == "DEBUG"]
        self.assertEqual(len(debug_findings), 2)

class TestBranchAndMergeUtils(unittest.TestCase):
    @patch('subprocess.run')
    def test_get_local_branches(self, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "main\nfeature-auth\ndev\n"
        mock_run.return_value = mock_result

        branches = get_local_branches()
        self.assertEqual(branches, ["main", "feature-auth", "dev"])

    @patch('subprocess.run')
    def test_get_remote_branches_filters_head(self, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "origin\norigin/main\norigin/feature-friend\norigin/HEAD\n"
        mock_run.return_value = mock_result

        branches = get_remote_branches(remote="origin")
        self.assertEqual(branches, ["origin/main", "origin/feature-friend"])

    @patch('subprocess.run')
    def test_switch_branch_existing(self, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Switched to branch 'feature-auth'"
        mock_run.return_value = mock_result

        ok, msg = switch_branch("feature-auth", create=False)
        self.assertTrue(ok)
        mock_run.assert_called_with(
            ["git", "checkout", "feature-auth"],
            capture_output=True, text=True, encoding='utf-8', errors='replace'
        )

    @patch('subprocess.run')
    def test_switch_branch_create(self, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Switched to a new branch 'feature-new'"
        mock_run.return_value = mock_result

        ok, msg = switch_branch("feature-new", create=True)
        self.assertTrue(ok)
        mock_run.assert_called_with(
            ["git", "checkout", "-b", "feature-new"],
            capture_output=True, text=True, encoding='utf-8', errors='replace'
        )

    @patch('subprocess.run')
    def test_get_incoming_commits_from_teammates(self, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = (
            "abc1234|alice|2 hours ago|feat: add team dashboard\n"
            "def5678|bob|1 hour ago|fix: resolve race condition\n"
        )
        mock_run.return_value = mock_result

        commits = get_incoming_commits(branch_name="main", remote="origin")
        self.assertEqual(len(commits), 2)
        self.assertEqual(commits[0]["hash"], "abc1234")
        self.assertEqual(commits[0]["author"], "alice")
        self.assertEqual(commits[0]["message"], "feat: add team dashboard")
        self.assertEqual(commits[1]["author"], "bob")

    @patch('git_utils.has_uncommitted_changes', return_value=False)
    @patch('subprocess.run')
    def test_merge_branch_clean_success(self, mock_run, mock_has_changes):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Updating 1d36dab..793e9bc\nFast-forward\n"
        mock_run.return_value = mock_result

        res = merge_branch("origin/main", auto_stash=True)
        self.assertTrue(res["success"])
        self.assertEqual(res["conflicts"], [])
        self.assertFalse(res["stashed"])

    @patch('git_utils.get_conflicted_files', return_value=["Logic/code.py", "README.md"])
    @patch('git_utils.has_uncommitted_changes', return_value=False)
    @patch('subprocess.run')
    def test_merge_branch_conflict(self, mock_run, mock_has_changes, mock_conflicts):
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "CONFLICT (content): Merge conflict in Logic/code.py"
        mock_run.return_value = mock_result

        res = merge_branch("origin/feature-friend", auto_stash=True)
        self.assertFalse(res["success"])
        self.assertEqual(res["conflicts"], ["Logic/code.py", "README.md"])

    @patch('subprocess.run')
    def test_abort_merge(self, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        ok, msg = abort_merge()
        self.assertTrue(ok)
        self.assertIn("aborted", msg.lower())

    @patch('git_utils.get_current_branch', return_value="main")
    @patch('git_utils.get_default_remote', return_value="origin")
    @patch('subprocess.run')
    def test_commit_and_push_target_branch(self, mock_run, mock_remote, mock_branch):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Everything up-to-date"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        res = commit_and_push("feat: test", used_unstaged=True, target_branch="feature-collab")
        self.assertTrue(res["success"])

    @patch('git_utils.get_current_branch', return_value="main")
    @patch('git_utils.get_default_remote', return_value="origin")
    @patch('subprocess.run')
    def test_commit_and_push_detects_non_fast_forward_collision(self, mock_run, mock_remote, mock_branch):
        commit_res = MagicMock()
        commit_res.returncode = 0
        commit_res.stdout = "[main 1234567] feat: test"

        push_res = MagicMock()
        push_res.returncode = 1
        push_res.stderr = "error: failed to push some refs to 'origin'\nhint: Updates were rejected because the remote contains work that you do\nhint: not have locally. Fetch first."
        push_res.stdout = ""

        mock_run.side_effect = [commit_res, push_res]

        res = commit_and_push("feat: test", used_unstaged=False, target_branch="main")
        self.assertFalse(res["success"])
        self.assertTrue(res["rejected_non_fast_forward"])

class TestAIConflictResolution(unittest.TestCase):
    @patch('urllib.request.urlopen')
    def test_explain_merge_conflicts_ai(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "response": "Here is the conflict breakdown:\n1. Local branch added security checks.\n2. Remote branch updated models.\n3. Recommend keeping both."
        }).encode('utf-8')
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        diff = "<<<<<<< HEAD\nlocal\n=======\nfriend\n>>>>>>> origin/main\n"
        explanation = explain_merge_conflicts(["test.py"], diff)
        self.assertIn("Local branch added security checks", explanation)

class TestUIBranchAndMerge(unittest.TestCase):
    def test_ui_helpers_no_crash(self):
        # Ensure UI render functions execute safely without crashing
        commits = [{"hash": "abc1234", "author": "friend", "time": "2 hours ago", "message": "feat: friend work"}]
        print_incoming_commits(commits, "origin/main")
        print_branch_status("main", "origin/main")
        print_branch_list(["main", "feature-auth"], "main")
        print_conflict_report(["file1.py"])
        print_conflict_options()

if __name__ == '__main__':
    unittest.main()
