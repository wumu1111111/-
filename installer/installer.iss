; Inno Setup Script for Long-form Web Novel Distillation Tool
; Build with: iscc installer\installer.iss

[Setup]
AppName=长篇网文蒸馏器
AppVersion=1.0.0
DefaultDirName={autopf}\长篇网文蒸馏器
DefaultGroupName=长篇网文蒸馏器
OutputBaseFilename=长篇网文蒸馏器_Setup
Compression=lzma2
SolidCompression=yes
OutputDir=dist\installer

[Files]
Source: "dist\installer\长篇网文蒸馏器.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "templates"; DestDir: "{app}\templates"; Flags: recursesubdirs createallsubdirs
Source: "prompts"; DestDir: "{app}\prompts"; Flags: recursesubdirs createallsubdirs
Source: "scripts"; DestDir: "{app}\scripts"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{group}\长篇网文蒸馏器"; Filename: "{app}\长篇网文蒸馏器.exe"

[Run]
Filename: "{app}\长篇网文蒸馏器.exe"; Description: "运行长篇网文蒸馏器"; Flags: nowait postinstall skipifsilent
