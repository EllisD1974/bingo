; ============================================================
; Inno Setup Script for Bingo Client
; ============================================================

[Setup]
AppName=BingoClient
AppVersion=1.0.0
AppPublisher=NEL
DefaultDirName={commonpf}\BingoClient
DefaultGroupName=BingoClient
OutputDir=installer_output
OutputBaseFilename=BingoClientInstaller
Compression=lzma
SolidCompression=yes
WizardStyle=modern

; Icon for installer itself
SetupIconFile=resources\icons\icon.ico

[Files]
; Include all PyInstaller output
Source: "dist\BingoClient.exe"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\BingoClient"; Filename: "{app}\BingoClient.exe"
Name: "{commondesktop}\BingoClient"; Filename: "{app}\BingoClient.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; Flags: unchecked

[Run]
Filename: "{app}\BingoClient.exe"; Description: "Launch BingoClient"; Flags: nowait postinstall skipifsilent