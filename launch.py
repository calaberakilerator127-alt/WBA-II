# War Brawl Arena II — Launcher entry point
# Run this file to start the launcher from dev mode:
#   python launch.py
import sys
import os

# Make sure the project root is in the path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from launcher.launcher import main

if __name__ == "__main__":
    main()
