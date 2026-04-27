import pytest
from unittest.mock import patch

def test_main_calls_window_main():
    with patch('manga_extractor.gui.window.main') as mock_window_main:
        import manga_extractor.main
        # Re-importing might not work if it was already imported, 
        # but since we're running in a fresh process usually it's fine.
        # Actually, for main.py, we just want to ensure it calls window.main()
        # when __name__ == "__main__".
        # We can't easily trigger if __name__ == "__main__" unless we use runpy.
        import runpy
        runpy.run_module('manga_extractor.main', run_name='__main__')
        mock_window_main.assert_called_once()
