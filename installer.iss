[Setup]
AppName=ChatList
AppVersion={#GetPythonValue("__version__", "version.py")}
AppPublisher=My Company
DefaultDirName={autopf}\ChatList
DefaultGroupName=ChatList
OutputBaseFilename=ChatList_Installer_v{#GetPythonValue("__version__", "version.py")}
Compression=lzma
SolidCompression=yes
PrivilegesRequired=none

[Files]
Source: "dist\ChatList_v{#GetPythonValue("__version__", "version.py")}.exe"; DestDir: "{tmp}"; Flags: deleteafterbyrun

[Run]
Filename: "{tmp}\ChatList_v{#GetPythonValue("__version__", "version.py")}.exe"; Description: "Запустить ChatList"; Flags: postinstall nowait skipifsilent
