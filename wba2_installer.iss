[Setup]
AppId={{3914C236-4091-4D90-A87A-28B3DC5D9D42}}
AppName=War Brawl Arena II
AppVersion=1.0.7
AppPublisher=Calaveroli127
AppPublisherURL=https://github.com/calaberakilerator127-alt/WBA-II
AppSupportURL=https://github.com/calaberakilerator127-alt/WBA-II/issues
AppUpdatesURL=https://github.com/calaberakilerator127-alt/WBA-II/releases
DefaultDirName={autopf}\War Brawl Arena II
DefaultGroupName=War Brawl Arena II
DisableProgramGroupPage=yes
LicenseFile=README.md
PrivilegesRequired=lowest
OutputDir=dist
OutputBaseFilename=WarBrawlArena2_Setup_v1.0.7
; SetupIconFile=assets\Icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\WarBrawlArena2\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\War Brawl Arena II"; Filename: "{app}\WarBrawlArena2.exe"; IconFilename: "{app}\assets\Icon.ico"
Name: "{autodesktop}\War Brawl Arena II"; Filename: "{app}\WarBrawlArena2.exe"; Tasks: desktopicon; IconFilename: "{app}\assets\Icon.ico"

[Run]
Filename: "{app}\WarBrawlArena2.exe"; Description: "{cm:LaunchProgram,War Brawl Arena II}"; Flags: nowait postinstall skipifsilent
