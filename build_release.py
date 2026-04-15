import os
import json
import subprocess
import shutil
import webbrowser

def create_installer(version):
    inno_setup_path = r"C:\Users\Calaveroli127\AppData\Local\Programs\Inno Setup 6\iscc.exe"
    if not os.path.exists(inno_setup_path):
        inno_setup_path = r"C:\Program Files (x86)\Inno Setup 6\iscc.exe"
        
    if not os.path.exists(inno_setup_path):
        print("\n[!] Inno Setup no encontrado. Omitiendo la creación del Instalador .exe")
        print("    Para generar instaladores profesionales, instala Inno Setup desde:")
        print("    https://jrsoftware.org/isdl.php o usa 'winget install JRSoftware.InnoSetup'")
        return None

    iss_content = f"""[Setup]
AppId={{{{3914C236-4091-4D90-A87A-28B3DC5D9D42}}}}
AppName=War Brawl Arena II
AppVersion={version}
AppPublisher=Calaveroli127
AppPublisherURL=https://github.com/calaberakilerator127-alt/WBA-II
AppSupportURL=https://github.com/calaberakilerator127-alt/WBA-II/issues
AppUpdatesURL=https://github.com/calaberakilerator127-alt/WBA-II/releases
DefaultDirName={{autopf}}\\War Brawl Arena II
DefaultGroupName=War Brawl Arena II
DisableProgramGroupPage=yes
LicenseFile=README.md
PrivilegesRequired=lowest
OutputDir=dist
OutputBaseFilename=WarBrawlArena2_Setup_v{version}
; SetupIconFile=assets\\Icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{{cm:CreateDesktopIcon}}"; GroupDescription: "{{cm:AdditionalIcons}}"; Flags: unchecked

[Files]
Source: "dist\\WarBrawlArena2\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{{group}}\\War Brawl Arena II"; Filename: "{{app}}\\WarBrawlArena2.exe"; IconFilename: "{{app}}\\assets\\Icon.ico"
Name: "{{autodesktop}}\\War Brawl Arena II"; Filename: "{{app}}\\WarBrawlArena2.exe"; Tasks: desktopicon; IconFilename: "{{app}}\\assets\\Icon.ico"

[Run]
Filename: "{{app}}\\WarBrawlArena2.exe"; Description: "{{cm:LaunchProgram,War Brawl Arena II}}"; Flags: nowait postinstall skipifsilent
"""
    iss_file = "wba2_installer.iss"
    with open(iss_file, "w", encoding="utf-8") as f:
        f.write(iss_content)
        
    print("\n[+] Compilando el Instalador Windows con Inno Setup...")
    result = subprocess.run([inno_setup_path, iss_file])
    
    if result.returncode == 0:
        installer_path = os.path.join("dist", f"WarBrawlArena2_Setup_v{version}.exe")
        print(f"[+] Instalador .exe creado exitosamente en: {installer_path}")
        return installer_path
    else:
        print("[-] Error durante la creación del instalador.")
        return None

def main():
    print("=" * 50)
    print("  WBA II - Sistema de Lanzamiento de Actualizaciones")
    print("=" * 50)

    # 1. Leer versión actual
    version_file = "version.json"
    try:
        with open(version_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            current_version = data.get("version", "1.0.0")
    except Exception as e:
        print(f"Error leyendo {version_file}: {e}")
        return

    print(f"Versión actual: {current_version}")
    
    # Calcular siguiente versión por defecto (incrementar el último dígito)
    parts = current_version.split(".")
    try:
        parts[-1] = str(int(parts[-1]) + 1)
        next_ver = ".".join(parts)
    except:
        next_ver = current_version + "-1"

    new_version = input(f"Ingresa la nueva versión (Enter para {next_ver}): ").strip()
    if not new_version:
        new_version = next_ver

    # 2. Actualizar version.json
    data["version"] = new_version
    with open(version_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    print(f"\n[+] version.json actualizado a {new_version}")

    # 3. Compilar con PyInstaller
    print("\n[+] Compilando el juego con PyInstaller... (esto tomará un momento)")
    result = subprocess.run(["python", "-m", "PyInstaller", "--noconfirm", "wba2.spec"])
    if result.returncode != 0:
        print("Error durante la compilación. Abortando.")
        return

    # 4. Crear archivo ZIP
    dist_folder = os.path.join("dist", "WarBrawlArena2")
    zip_name = os.path.join("dist", f"WarBrawlArena2-v{new_version}")

    if not os.path.exists(dist_folder):
        print(f"\nError: No se encontró la carpeta compilada '{dist_folder}'.")
        return

    print(f"\n[+] Comprimiendo la carpeta en: {zip_name}.zip ...")
    shutil.make_archive(zip_name, 'zip', root_dir="dist", base_dir="WarBrawlArena2")
    print("[+] Archivo ZIP creado exitosamente.")

    # 4.5 Crear Instalador con Inno Setup
    installer_path = create_installer(new_version)

    # 5. Abrir GitHub para subir el Release
    print("\n" + "=" * 50)
    print(f"¡ACTUALIZACIÓN PREPARADA!")
    print(f"Archivos a subir (recomendamos subir ambos a GitHub):")
    print(f"  -> dist\\WarBrawlArena2-v{new_version}.zip (Versión Portable)")
    if installer_path:
        print(f"  -> {installer_path} (Instalador Profesional)")
    print("=" * 50)
    
    # Construir URL para crear el release pre-llenado
    repo_url = "https://github.com/calaberakilerator127-alt/WBA-II/releases/new"
    tag_name = f"v{new_version}"
    release_title = f"Actualización v{new_version}"
    full_url = f"{repo_url}?tag={tag_name}&title={release_title}"
    
    abrir = input("¿Deseas abrir la página de GitHub para publicar la actualización? (S/n): ").strip().lower()
    if abrir != 'n':
        print("Abriendo el navegador...")
        webbrowser.open(full_url)
        print("Por favor:")
        print("  1. Arrastra y suelta el archivo Instalador (.exe) y el ZIP en la página de GitHub.")
        print("  2. Haz clic en 'Publish release'.")

if __name__ == "__main__":
    main()
