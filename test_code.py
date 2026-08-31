import unittest
import sys
import os
import json
import tempfile
from unittest.mock import patch, MagicMock

# Add Logic directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "Logic"))

import logger
from git_utils import get_diff
from ai_utils import parse_options_from_response
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

    @patch('urllib.request.urlopen')
    def test_generate_commit_options_stdlib(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"response": '["feat: stdlib test"]'}).encode('utf-8')
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        from ai_utils import generate_commit_options
        options = generate_commit_options("dummy diff")
        self.assertEqual(options, ["feat: stdlib test"])

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

if __name__ == '__main__':
    unittest.main()
