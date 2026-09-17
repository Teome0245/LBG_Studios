' Relance Agent_IA :5005 sans aucune fenetre (ni cmd, ni powershell visible).
' Usage : double-clic, ou : wscript //nologo C:\Agent_IA\restart_agent.vbs
Set sh = CreateObject("WScript.Shell")
sh.CurrentDirectory = "C:\Agent_IA"
' 0 = fenetre cachee, False = ne pas attendre
sh.Run "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File ""C:\Agent_IA\restart_agent.ps1""", 0, False
