import os
import sys
import unittest
from unittest.mock import patch, mock_open

from Logic.config import load_environment

class TestConfig(unittest.TestCase):
    def test_load_environment_with_dotenv(self):
        # We need to mock sys.modules to simulate dotenv module
        import types
        mock_dotenv = types.ModuleType('dotenv')
        mock_dotenv.load_dotenv = lambda dotenv_path: None

        with patch.dict(sys.modules, {'dotenv': mock_dotenv}):
            with patch('dotenv.load_dotenv') as mock_load_dotenv:
                with patch('os.path.abspath', return_value='/fake/Logic/config.py'):
                    load_environment()
                    mock_load_dotenv.assert_called_once_with(dotenv_path='/fake/.env')

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data="TEST_KEY=TEST_VAL\n# COMMENT=NO\nKEY2='val2'\nKEY3=\"val3\"\n")
    @patch.dict(os.environ, {}, clear=True)
    def test_load_environment_fallback(self, mock_file, mock_exists):
        mock_exists.return_value = True

        # Make sure dotenv is NOT in sys.modules, so it raises ImportError
        if 'dotenv' in sys.modules:
            del sys.modules['dotenv']

        orig_import = __import__
        def mock_import(name, *args, **kwargs):
            if name == 'dotenv':
                raise ImportError()
            return orig_import(name, *args, **kwargs)

        with patch('builtins.__import__', side_effect=mock_import):
            with patch('os.path.abspath', return_value='/fake/Logic/config.py'):
                load_environment()

        self.assertEqual(os.environ.get("TEST_KEY"), "TEST_VAL")
        self.assertEqual(os.environ.get("KEY2"), "val2")
        self.assertEqual(os.environ.get("KEY3"), "val3")
        self.assertIsNone(os.environ.get("COMMENT"))

    @patch('os.path.exists')
    @patch.dict(os.environ, {}, clear=True)
    def test_load_environment_fallback_no_file(self, mock_exists):
        mock_exists.return_value = False

        # Make sure dotenv is NOT in sys.modules, so it raises ImportError
        if 'dotenv' in sys.modules:
            del sys.modules['dotenv']

        orig_import = __import__
        def mock_import(name, *args, **kwargs):
            if name == 'dotenv':
                raise ImportError()
            return orig_import(name, *args, **kwargs)

        with patch('builtins.__import__', side_effect=mock_import):
            with patch('os.path.abspath', return_value='/fake/Logic/config.py'):
                load_environment()

        self.assertNotIn("TEST_KEY", os.environ)

if __name__ == '__main__':
    unittest.main()
