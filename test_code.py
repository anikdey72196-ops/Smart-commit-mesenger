import unittest
from unittest.mock import patch, MagicMock
from code import get_diff

class TestCode(unittest.TestCase):
    @patch('code.subprocess.run')
    def test_get_diff_staged_true(self, mock_run):
        mock_result = MagicMock()
        mock_result.stdout = "staged diff output"
        mock_run.return_value = mock_result

        result = get_diff(staged=True)

        mock_run.assert_called_once_with(["git", "diff", "--staged"], capture_output=True, text=True)
        self.assertEqual(result, "staged diff output")

    @patch('code.subprocess.run')
    def test_get_diff_staged_false(self, mock_run):
        mock_result = MagicMock()
        mock_result.stdout = "unstaged diff output"
        mock_run.return_value = mock_result

        result = get_diff(staged=False)

        mock_run.assert_called_once_with(["git", "diff"], capture_output=True, text=True)
        self.assertEqual(result, "unstaged diff output")

    @patch('code.subprocess.run')
    def test_get_diff_default(self, mock_run):
        mock_result = MagicMock()
        mock_result.stdout = "default staged diff output"
        mock_run.return_value = mock_result

        result = get_diff()

        mock_run.assert_called_once_with(["git", "diff", "--staged"], capture_output=True, text=True)
        self.assertEqual(result, "default staged diff output")

if __name__ == '__main__':
    unittest.main()
