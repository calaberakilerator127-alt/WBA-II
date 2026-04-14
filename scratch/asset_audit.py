import os
import re

def verify_assets(root_path):
    print(f"--- ANALYZING PROJECT AT: {root_path} ---")
    
    # 1. Map all files in assets folder
    assets_dir = os.path.join(root_path, "assets")
    existing_assets = set()
    for root, dirs, files in os.walk(assets_dir):
        for file in files:
            rel_path = os.path.relpath(os.path.join(root, file), root_path)
            existing_assets.add(rel_path.replace("\\", "/"))

    # 2. Scan all python files for string literals that look like paths
    path_pattern = re.compile(r"['\"](assets/.*?\.(png|wav|mp3))['\"]")
    src_dir = os.path.join(root_path, "src")
    
    referenced_assets = {}
    
    files_to_scan = [os.path.join(root_path, "main.py")]
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if file.endswith(".py"):
                files_to_scan.append(os.path.join(root, file))

    for py_file in files_to_scan:
        with open(py_file, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            matches = path_pattern.findall(content)
            for match in matches:
                path = match[0]
                if path not in referenced_assets:
                    referenced_assets[path] = []
                referenced_assets[path].append(os.path.relpath(py_file, root_path))

    # 3. Validation
    broken_links = []
    for path in referenced_assets:
        if path not in existing_assets:
            broken_links.append((path, referenced_assets[path]))

    unused_assets = existing_assets - set(referenced_assets.keys())

    print("\n--- BROKEN LINKS (Referenced in code but missing in folder) ---")
    if not broken_links:
        print("None found!")
    else:
        for path, files in broken_links:
            print(f"X MISSING: {path} (Used in: {', '.join(files)})")

    print("\n--- UNUSED ASSETS (Existing in folder but not found in code) ---")
    if not unused_assets:
        print("None found!")
    else:
        # Sort and group for readability
        for path in sorted(list(unused_assets)):
            print(f"U UNUSED: {path}")

if __name__ == "__main__":
    verify_assets(r"c:\Users\Calaveroli127\Downloads\WBA II")
