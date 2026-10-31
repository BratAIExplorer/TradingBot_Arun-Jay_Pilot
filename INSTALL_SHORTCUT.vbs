' ORBIT TRADING - Desktop Shortcut Installer
' Creates a clickable desktop icon to launch the trading system

Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

' Get paths
strProjectPath = objFSO.GetParentFolderName(WScript.ScriptFullName)
strDesktop = objShell.SpecialFolders("Desktop")
strLinkPath = strDesktop & "\🚀 ORBIT TRADING.lnk"
strBatPath = strProjectPath & "\START_ORBIT.bat"

' Verify batch file exists
If Not objFSO.FileExists(strBatPath) Then
    MsgBox "Error: START_ORBIT.bat not found at " & strBatPath, vbCritical, "Shortcut Creation Failed"
    WScript.Quit 1
End If

' Create shortcut
Set objLink = objShell.CreateShortcut(strLinkPath)
objLink.TargetPath = strBatPath
objLink.WorkingDirectory = strProjectPath
objLink.Description = "Click to launch ORBIT TRADING dashboard"
objLink.WindowStyle = 1  ' Normal window
objLink.Save

MsgBox "✅ Shortcut created on desktop!" & vbCrLf & vbCrLf & _
        "Icon: 🚀 ORBIT TRADING" & vbCrLf & _
        "Location: " & strDesktop & vbCrLf & vbCrLf & _
        "Double-click to start trading!", vbInformation, "Success"

WScript.Quit 0
