import unittest
from unittest.mock import patch, MagicMock
from code import is_git_repo

class TestIsGitRepo(unittest.TestCase):
    @patch('code.subprocess.run')
    def test_is_git_repo_true(self, mock_run):
        # Setup mock to return a result with returncode 0
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        # Call function
        result = is_git_repo()

        # Verify result and correct call
        self.assertTrue(result)
        mock_run.assert_called_once_with(["git", "rev-parse", "--git-dir"],
                                         capture_output=True, text=True)

    @patch('code.subprocess.run')
    def test_is_git_repo_false(self, mock_run):
        # Setup mock to return a result with non-zero returncode
        mock_result = MagicMock()
        mock_result.returncode = 128
        mock_run.return_value = mock_result

        # Call function
        result = is_git_repo()

        # Verify result and correct call
        self.assertFalse(result)
        mock_run.assert_called_once_with(["git", "rev-parse", "--git-dir"],
                                         capture_output=True, text=True)

if __name__ == '__main__':
    unittest.main()
