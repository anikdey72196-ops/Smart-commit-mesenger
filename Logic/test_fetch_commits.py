import unittest
from unittest.mock import patch, MagicMock
from fetch_commits import fetch_and_save_commits, sanitize_csv_field

class TestFetchCommits(unittest.TestCase):
    def test_sanitize_csv_field(self):
        self.assertEqual(sanitize_csv_field("normal"), "normal")
        self.assertEqual(sanitize_csv_field("=cmd"), "'=cmd")
        self.assertEqual(sanitize_csv_field("+cmd"), "'+cmd")
        self.assertEqual(sanitize_csv_field("-cmd"), "'-cmd")
        self.assertEqual(sanitize_csv_field("@cmd"), "'@cmd")
        self.assertEqual(sanitize_csv_field(123), "123")

    @patch('fetch_commits.requests.get')
    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    @patch('fetch_commits.csv.writer')
    def test_fetch_and_save_commits_success(self, mock_csv_writer, mock_open, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"commit": {"author": {"date": "2023-01-01T00:00:00Z"}, "message": "Test commit"}}
        ]
        mock_get.return_value = mock_response

        fetch_and_save_commits("testowner", "testrepo")

        mock_get.assert_called_once_with("https://api.github.com/repos/testowner/testrepo/commits", timeout=10)
        mock_open.assert_called_once_with("commit_history.csv", "w", newline="", encoding="utf-8")
        mock_csv_writer().writerow.assert_any_call(["Repository", "Date", "Message"])
        mock_csv_writer().writerow.assert_any_call(["testrepo", "2023-01-01T00:00:00Z", "Test commit"])

    @patch('fetch_commits.requests.get')
    def test_fetch_and_save_commits_failure(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        # Suppress print statements for this test
        with patch('builtins.print') as mock_print:
            fetch_and_save_commits("invalid", "repo")
            mock_print.assert_any_call("Error: Could not connect to API. Status code 404")

if __name__ == '__main__':
    unittest.main()
