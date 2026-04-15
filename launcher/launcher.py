"""
War Brawl Arena II — Launcher
Checks for updates from GitHub Releases, downloads & applies them,
then launches WarBrawlArena2.exe.

GitHub repo: calaberakilerator127-alt/WBA-II
"""
import os
import sys
import json
import shutil
import tempfile
import zipfile
import subprocess
import threading
import time
import urllib.request
import urllib.error

# ── Constants ─────────────────────────────────────────────────
GITHUB_API   = "https://api.github.com/repos/calaberakilerator127-alt/WBA-II/releases/latest"
ASSET_NAME   = "WarBrawlArena2"          # zip asset name starts with this
TIMEOUT_SEC  = 8                          # connection timeout

# ── Path helpers ──────────────────────────────────────────────

def _launcher_dir():
    """Directory of the launcher exe (or script during dev)."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    # Dev mode: launcher/ lives inside the project root
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _game_root():
    """Root of the installed game (parent of the launcher dir when deployed)."""
    return _launcher_dir()

def _version_file():
    return os.path.join(_game_root(), "version.json")

def _game_exe():
    try:
        with open(_version_file(), "r", encoding="utf-8") as f:
            data = json.load(f)
        return os.path.join(_game_root(), data.get("game_exe", "WarBrawlArena2.exe"))
    except Exception:
        return os.path.join(_game_root(), "WarBrawlArena2.exe")


# ── Version helpers ───────────────────────────────────────────

def _parse_version(v: str):
    """Converts '1.2.3' → (1, 2, 3) for comparison."""
    try:
        return tuple(int(x) for x in v.lstrip("v").split("."))
    except Exception:
        return (0,)

def _local_version():
    try:
        with open(_version_file(), "r", encoding="utf-8") as f:
            return json.load(f).get("version", "0.0.0")
    except Exception:
        return "0.0.0"

def _update_local_version(new_version: str):
    vf = _version_file()
    try:
        with open(vf, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {"game_exe": "WarBrawlArena2.exe"}
    data["version"] = new_version
    with open(vf, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


# ── Update logic ──────────────────────────────────────────────

class UpdateResult:
    __slots__ = ("available", "version", "download_url", "error")
    def __init__(self):
        self.available    = False
        self.version      = ""
        self.download_url = ""
        self.error        = ""


def check_for_update() -> UpdateResult:
    result = UpdateResult()
    try:
        req = urllib.request.Request(GITHUB_API,
                                     headers={"User-Agent": "WBA2-Launcher/1.0"})
        with urllib.request.urlopen(req, timeout=TIMEOUT_SEC) as resp:
            data = json.loads(resp.read().decode())

        remote_version = data.get("tag_name", "0.0.0").lstrip("v")
        local_version  = _local_version()

        if _parse_version(remote_version) > _parse_version(local_version):
            result.available = True
            result.version   = remote_version
            # Find the zip asset
            for asset in data.get("assets", []):
                name = asset.get("name", "")
                if name.startswith(ASSET_NAME) and name.endswith(".zip"):
                    result.download_url = asset["browser_download_url"]
                    break
            if not result.download_url:
                # Fallback: use zipball_url
                result.download_url = data.get("zipball_url", "")

    except urllib.error.URLError as e:
        result.error = f"Sin conexión: {e.reason}"
    except Exception as e:
        result.error = str(e)

    return result


def download_and_apply(url: str, new_version: str,
                       progress_callback=None,
                       status_callback=None) -> bool:
    """
    Downloads the zip, extracts it to a temp dir, then copies files
    over the game root — skipping the data/ directory to preserve saves.
    Returns True on success.
    """
    def _status(txt):
        if status_callback: status_callback(txt)

    def _progress(pct):
        if progress_callback: progress_callback(pct)

    tmp_dir = tempfile.mkdtemp(prefix="wba2_update_")
    zip_path = os.path.join(tmp_dir, "update.zip")

    try:
        _status(f"DESCARGANDO v{new_version}...")
        # Stream download with progress
        req = urllib.request.Request(url,
                                     headers={"User-Agent": "WBA2-Launcher/1.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            total = int(resp.headers.get("Content-Length", 0))
            downloaded = 0
            chunk = 65536
            with open(zip_path, "wb") as f:
                while True:
                    buf = resp.read(chunk)
                    if not buf:
                        break
                    f.write(buf)
                    downloaded += len(buf)
                    if total > 0:
                        _progress(0.1 + 0.7 * (downloaded / total))
        _progress(0.8)

        _status("EXTRAYENDO...")
        extract_dir = os.path.join(tmp_dir, "extracted")
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)
        _progress(0.9)

        # Find the root folder inside the zip (may be nested)
        candidates = [
            d for d in os.listdir(extract_dir)
            if os.path.isdir(os.path.join(extract_dir, d))
        ]
        src_root = os.path.join(extract_dir, candidates[0]) if candidates else extract_dir

        _status("INSTALANDO ARCHIVOS...")
        game_root = _game_root()
        SKIP_DIRS = {"data"}  # ← never overwrite saves

        for root, dirs, files in os.walk(src_root):
            rel_root = os.path.relpath(root, src_root)
            # Skip protected directories
            parts = rel_root.replace("\\", "/").split("/")
            if parts[0] in SKIP_DIRS:
                dirs.clear()
                continue

            dst_dir = os.path.join(game_root, rel_root) if rel_root != "." else game_root
            os.makedirs(dst_dir, exist_ok=True)
            for fname in files:
                src_f = os.path.join(root, fname)
                dst_f = os.path.join(dst_dir, fname)
                shutil.copy2(src_f, dst_f)

        _update_local_version(new_version)
        _progress(1.0)
        _status(f"¡ACTUALIZADO A v{new_version}!")
        return True

    except Exception as e:
        _status(f"ERROR: {e}")
        return False
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


# ── Main ──────────────────────────────────────────────────────

def launch_game():
    exe = _game_exe()
    if os.path.exists(exe):
        subprocess.Popen([exe], cwd=os.path.dirname(exe))
    else:
        print(f"[Launcher] No se encontró el ejecutable: {exe}")


def main():
    from launcher.launcher_ui import LauncherWindow

    ui = LauncherWindow()

    # ── Phase 1: Check for update (in background thread) ──────
    check_result   = [None]
    check_done     = [False]

    def do_check():
        check_result[0] = check_for_update()
        check_done[0]   = True

    threading.Thread(target=do_check, daemon=True).start()

    ui.set_status("BUSCANDO ACTUALIZACIONES...", sub="calaberakilerator127-alt/WBA-II")
    ui.set_progress(0.05)

    # Wait for check (max ~TIMEOUT_SEC + 1s) while pumping UI
    t0 = time.time()
    while not check_done[0]:
        if not ui.pump():
            ui.close()
            launch_game()
            return
        # Animate progress bar (fake loading feel)
        elapsed = time.time() - t0
        fake_pct = min(0.4, 0.05 + elapsed * 0.04)
        ui.set_progress(fake_pct)
        ui.render()

    result = check_result[0]

    # ── Phase 2: Handle result ─────────────────────────────────
    if result.error:
        ui.set_status("SIN CONEXIÓN — INICIANDO JUEGO", sub=result.error)
        ui.set_progress(1.0)
        ui.show_skip_button(False)
        for _ in range(60):   # show for ~1s
            if not ui.pump(): break
            ui.render()
        ui.close()
        launch_game()
        return

    if not result.available:
        ui.set_status("¡JUEGO ACTUALIZADO!", sub=f"v{_local_version()} — Iniciando...")
        ui.set_progress(1.0)
        for _ in range(60):
            if not ui.pump(): break
            ui.render()
        ui.close()
        launch_game()
        return

    # Update available — ask the user (optional: show skip button)
    ui.set_status(f"ACTUALIZACIÓN DISPONIBLE: v{result.version}",
                  sub=f"Versión actual: v{_local_version()}")
    ui.set_progress(0.0)
    ui.show_skip_button(True)

    # Show for up to 4s so the user can choose to skip
    t0 = time.time()
    skipped = False
    while time.time() - t0 < 4.0:
        if not ui.pump():
            skipped = True
            break
        ui.set_progress((time.time() - t0) / 4.0 * 0.08)
        ui.render()

    if skipped or ui.skip_clicked:
        ui.close()
        launch_game()
        return

    # ── Phase 3: Download & apply ──────────────────────────────
    apply_done  = [False]
    apply_ok    = [False]
    _status_msg = [""]
    _pct        = [0.0]

    def do_apply():
        apply_ok[0]  = download_and_apply(
            result.download_url, result.version,
            progress_callback=lambda p: _pct.__setitem__(0, p),
            status_callback=lambda s: _status_msg.__setitem__(0, s)
        )
        apply_done[0] = True

    threading.Thread(target=do_apply, daemon=True).start()

    while not apply_done[0]:
        if not ui.pump():
            break  # User closed; apply keeps running in background
        ui.set_status(_status_msg[0] or "DESCARGANDO...",
                      sub=f"v{_local_version()} → v{result.version}")
        ui.set_progress(_pct[0])
        ui.render()

    # Show final status briefly
    ui.set_progress(1.0)
    msg = f"¡LISTO! v{result.version}" if apply_ok[0] else "ACTUALIZACIÓN FALLIDA"
    ui.set_status(msg)
    for _ in range(90):
        if not ui.pump(): break
        ui.render()

    ui.close()
    launch_game()


if __name__ == "__main__":
    main()
