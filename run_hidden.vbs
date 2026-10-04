Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "D:\edith"
WshShell.Run "D:\edith\venv\Scripts\python.exe D:\edith\edith_daemon.py", 0, False
