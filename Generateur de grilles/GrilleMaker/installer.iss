; Script Inno Setup pour GrilleMaker
#define AppName "GrilleMaker"
#define AppVersion "1.0.0"
#define AppExe "GrilleMaker.exe"

[Setup]
AppId={{7C2E4A1B-5D3F-4B8E-9A61-6F0C2D8E4B17}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=nickthegreek
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir=Output
OutputBaseFilename=GrilleMaker-Setup
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\{#AppExe}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequiredOverridesAllowed=dialog
ChangesAssociations=yes

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "Créer un raccourci sur le Bureau"; GroupDescription: "Raccourcis :"
Name: "assoc"; Description: "Ouvrir les fichiers .grille avec GrilleMaker"; GroupDescription: "Fichiers :"

[Files]
Source: "dist\GrilleMaker\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{group}\Désinstaller {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Registry]
Root: HKA; Subkey: "Software\Classes\.grille"; ValueType: string; ValueName: ""; ValueData: "GrilleMaker.Grille"; Flags: uninsdeletevalue; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\GrilleMaker.Grille"; ValueType: string; ValueName: ""; ValueData: "Grille d'accords"; Flags: uninsdeletekey; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\GrilleMaker.Grille\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#AppExe},0"; Tasks: assoc
Root: HKA; Subkey: "Software\Classes\GrilleMaker.Grille\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""; Tasks: assoc

[Run]
Filename: "{app}\{#AppExe}"; Description: "Lancer {#AppName}"; Flags: nowait postinstall skipifsilent
