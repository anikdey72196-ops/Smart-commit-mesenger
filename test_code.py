import subprocess
from unittest.mock import patch, MagicMock
import pytest
import importlib.util
import sys

# Import code.py dynamically to avoid conflict with standard library 'code' module
spec = importlib.util.spec_from_file_location("my_code", "code.py")
my_code = importlib.util.module_from_spec(spec)
sys.modules["my_code"] = my_code
spec.loader.exec_module(my_code)

from my_code import get_diff_stats

@patch("my_code.subprocess.run")
def test_get_diff_stats_staged(mock_run):
    # Setup mock for staged changes
    mock_result = MagicMock()
    mock_result.stdout = " 1 file changed, 1 insertion(+)\n"
    mock_run.return_value = mock_result

    # Call function
    result = get_diff_stats()

    # Assert correct behavior
    mock_run.assert_called_once_with(
        ["git", "diff", "--cached", "--stat"],
        capture_output=True, text=True
    )
    assert result == "1 file changed, 1 insertion(+)"


@patch("my_code.subprocess.run")
def test_get_diff_stats_unstaged(mock_run):
    # Setup mock to return empty for first call (cached) and output for second call (unstaged)
    mock_result_cached = MagicMock()
    mock_result_cached.stdout = " \n"

    mock_result_unstaged = MagicMock()
    mock_result_unstaged.stdout = " 2 files changed, 2 deletions(-)\n"

    mock_run.side_effect = [mock_result_cached, mock_result_unstaged]

    # Call function
    result = get_diff_stats()

    # Assert correct behavior
    assert mock_run.call_count == 2
    mock_run.assert_any_call(
        ["git", "diff", "--cached", "--stat"],
        capture_output=True, text=True
    )
    mock_run.assert_any_call(
        ["git", "diff", "--stat"],
        capture_output=True, text=True
    )
    assert result == "2 files changed, 2 deletions(-)"


@patch("my_code.subprocess.run")
def test_get_diff_stats_no_changes(mock_run):
    # Setup mock to return empty for both calls
    mock_result = MagicMock()
    mock_result.stdout = " \n"

    mock_run.side_effect = [mock_result, mock_result]

    # Call function
    result = get_diff_stats()

    # Assert correct behavior
    assert mock_run.call_count == 2
    assert result == ""
