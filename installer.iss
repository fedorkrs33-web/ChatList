[Setup]
AppName=ChatList
AppVersion=1.0.0
AppPublisher=My Company
AppCopyright=© 2025. Все права защищены.
AppSupportURL=https://github.com/yourname/ChatList
AppUpdatesURL=https://github.com/yourname/ChatList/releases

DefaultDirName={autopf}\ChatList
DefaultGroupName=ChatList
DisableProgramGroupPage=yes

OutputDir={src}\installer_output
OutputBaseFilename=ChatList_Installer_v1.0.0

Compression=lzma
SolidCompression=yes
PrivilegesRequired=none
AllowNoIcons=yes
ChangesEnvironment=yes

SetupIconFile=app.ico
UninstallDisplayIcon=app.ico

AppMutex=ChatListSetupMutex

[Languages]
Name: "ru"; MessagesFile: "compiler:Languages\Russian.isl"

[Types]
Name: "full"; Description: "Полная установка"

[Components]
Name: "program"; Description: "Основная программа"; Types: full; Flags: fixed

[Tasks]
Name: desktopicon; Description: "Создать ярлык на рабочем столе"; GroupDescription: "Дополнительные задачи:"

[Files]
Source: "dist\ChatList_v1.0.0.exe"; DestDir: "{app}"; Components: program; Flags: ignoreversion
Source: ".env.example"; DestDir: "{app}"; Components: program
Source: "README.md"; DestDir: "{app}"; Components: program
Source: "app.ico"; DestDir: "{app}"; Components: program

[Icons]
Name: "{group}\ChatList"; Filename: "{app}\ChatList_v1.0.0.exe"; IconFilename: "{app}\app.ico"
Name: "{commondesktop}\ChatList"; Filename: "{app}\ChatList_v1.0.0.exe"; IconFilename: "{app}\app.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\ChatList_v1.0.0.exe"; Description: "Запустить ChatList"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: files; Name: "{app}\.env"
Type: files; Name: "{app}\*.log"
Type: files; Name: "{app}\*.cache"

[UninstallFinish]
String: "Чтобы завершить удаление, перезагрузите компьютер (если приложение было запущено)."
