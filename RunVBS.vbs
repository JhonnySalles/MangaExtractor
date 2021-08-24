On Error Resume Next
Set File = CreateObject("WScript.Shell")
File.Run "silent.bat BOSS" , vbHide
