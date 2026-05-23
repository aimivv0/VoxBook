"""Build VoxBook EXE"""
import subprocess, sys
from pathlib import Path

ROOT = Path(__file__).parent
PY = ROOT / ".buildvenv" / "Scripts" / "python.exe"
if not PY.exists():
    PY = sys.executable

cmd = [str(PY), "-m", "PyInstaller",
    "--name", "VoxBook",
    "--onedir",
    "--icon", "NONE",
    "--hidden-import", "edge_tts",
    "--hidden-import", "ebooklib",
    "--hidden-import", "ebooklib.epub",
    "--hidden-import", "bs4",
    "--hidden-import", "lxml",
    "--hidden-import", "lxml.etree",
    "--hidden-import", "lxml._elementpath",
    "--hidden-import", "pystray",
    "--hidden-import", "pystray._win32",
    "--hidden-import", "PIL",
    "--hidden-import", "tkinter",
    "--hidden-import", "tkinter.filedialog",
    "--collect-data", "edge_tts",
    "--collect-data", "ebooklib",
    "--clean", "--noconfirm",
    str(ROOT / "app.py"),
]
print("Building VoxBook...")
result = subprocess.run(cmd, cwd=str(ROOT))
if result.returncode == 0:
    folder = ROOT / "dist" / "VoxBook"
    if folder.exists():
        size = sum(f.stat().st_size for f in folder.rglob("*") if f.is_file())
        print(f"\n[OK] Built: {folder} ({size/1024/1024:.1f} MB)")