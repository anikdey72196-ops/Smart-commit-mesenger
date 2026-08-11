import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# Add Logic directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "Logic"))

from git_utils import get_diff
from ai_utils import parse_options_from_response

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

if __name__ == '__main__':
    unittest.main()
