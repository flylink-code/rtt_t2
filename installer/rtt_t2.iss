#ifndef MyAppReleaseTag
  #define MyAppReleaseTag "v1.0.8"
#endif
#ifndef MyAppVersion
  #define MyAppVersion "1.0.8"
#endif

#define MyAppName "RTT_T2"
#define MyAppPublisher "flylink-code"
#define MyAppExeName "rtt_t2.exe"
#define MyAppURL "https://github.com/flylink-code/rtt_t2"

[Setup]
AppId={{A3E8B4C1-9F2D-4B6A-8C1E-5D7F9A2B4C6E}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\rtt_t2
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=
OutputDir=..\dist
OutputBaseFilename=rtt_t2-{#MyAppReleaseTag}-windows-x64-setup
SetupIconFile=..\tool.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=admin

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加图标:"; Flags: unchecked

[Files]
Source: "..\dist\rtt_t2\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "启动 {#MyAppName}"; Flags: nowait postinstall skipifsilent
