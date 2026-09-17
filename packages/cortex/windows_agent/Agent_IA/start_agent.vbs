' Demarre Agent_IA :5005 sans aucune fenetre (ni cmd, ni powershell visible).
' Usage : double-clic, ou : wscript //nologo C:\Agent_IA\start_agent.vbs
Set sh = CreateObject("WScript.Shell")
sh.CurrentDirectory = "C:\Agent_IA"
sh.Run "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File ""C:\Agent_IA\start_agent.ps1""", 0, False
