import pytest
from unittest.mock import patch, MagicMock
import os

def test_is_user_admin_nt():
    from manga_extractor.utils.admin import isUserAdmin
    with patch('os.name', 'nt'), \
         patch('ctypes.windll.shell32.IsUserAnAdmin', return_value=True):
        assert isUserAdmin() is True

def test_is_user_admin_posix():
    from manga_extractor.utils.admin import isUserAdmin
    with patch('os.name', 'posix'), \
         patch('os.getuid', return_value=0, create=True):
        assert isUserAdmin() is True


def test_is_user_admin_unsupported():
    from manga_extractor.utils.admin import isUserAdmin
    with patch('os.name', 'other'):
        with pytest.raises(RuntimeError, match="Unsupported operating system"):
            isUserAdmin()

def test_run_as_admin_non_nt():
    from manga_extractor.utils.admin import runAsAdmin
    with patch('os.name', 'posix'):
        with pytest.raises(RuntimeError, match="only implemented on Windows"):
            runAsAdmin()

@patch('win32com.shell.shell.ShellExecuteEx')
def test_run_as_admin_nt_success(mock_shell_ex):
    from manga_extractor.utils.admin import runAsAdmin
    with patch('os.name', 'nt'):
        mock_shell_ex.return_value = {'hProcess': MagicMock()}
        # Simulate wait=False to avoid win32event calls
        res = runAsAdmin(cmdLine=["python.exe", "script.py"], wait=False)
        assert res is None
        mock_shell_ex.assert_called()

def test_run_as_admin_invalid_cmdline():
    from manga_extractor.utils.admin import runAsAdmin
    with patch('os.name', 'nt'):
        with pytest.raises(ValueError, match="cmdLine is not a sequence"):
            runAsAdmin(cmdLine="not a list")

@patch('win32com.shell.shell.ShellExecuteEx')
@patch('win32event.WaitForSingleObject')
@patch('win32process.GetExitCodeProcess')
def test_run_as_admin_wait(mock_get_exit, mock_wait, mock_shell_ex):
    from manga_extractor.utils.admin import runAsAdmin
    with patch('os.name', 'nt'):
        mock_shell_ex.return_value = {'hProcess': MagicMock()}
        mock_get_exit.return_value = 0
        
        res = runAsAdmin(cmdLine=["test.exe"], wait=True)
        assert res == 0
        mock_wait.assert_called_once()
        mock_get_exit.assert_called_once()

def test_is_user_admin_exception():
    from manga_extractor.utils.admin import isUserAdmin
    with patch('os.name', 'nt'), \
         patch('ctypes.windll.shell32.IsUserAnAdmin', side_effect=Exception("error")):
        assert isUserAdmin() is False

