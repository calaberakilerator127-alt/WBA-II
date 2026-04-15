import os
import json
import subprocess
import shutil
import webbrowser

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

    # 5. Abrir GitHub para subir el Release
    print("\n" + "=" * 50)
    print(f"¡ACTUALIZACIÓN PREPARADA!")
    print(f"Archivo a subir: dist\\WarBrawlArena2-v{new_version}.zip")
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
        print("  1. Arrastra y suelta el archivo ZIP recien creado en la página de GitHub.")
        print("  2. Haz clic en 'Publish release'.")

if __name__ == "__main__":
    main()
