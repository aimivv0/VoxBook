"""PyInstaller build script"""
import subprocess, sys, os
from pathlib import Path

ROOT = Path(__file__).parent

try:
    import PyInstaller  # noqa
except ImportError:
    print("Installing PyInstaller...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

cmd = [
    sys.executable, "-m", "PyInstaller",
    "--name", "Ebook2Audiobook",
    "--onefile",
    "--console",  # 保留命令窗口，用户能看到日志
    "--icon", "NONE",
    "--hidden-import", "edge_tts",
    "--hidden-import", "ebooklib",
    "--hidden-import", "ebooklib.epub",
    "--hidden-import", "bs4",
    "--hidden-import", "lxml",
    "--hidden-import", "lxml.etree",
    "--hidden-import", "lxml._elementpath",
    "--collect-data", "edge_tts",
    "--collect-data", "ebooklib",
    "--clean",
    "--noconfirm",
    str(ROOT / "app.py"),
]

print("Building EXE...")
result = subprocess.run(cmd, cwd=str(ROOT))

if result.returncode == 0:
    exe = ROOT / "dist" / "Ebook2Audiobook.exe"
    if exe.exists():
        size_mb = exe.stat().st_size / 1024 / 1024
        print(f"\n[OK] Built: {exe} ({size_mb:.1f} MB)")
        print("\nDistribute the entire 'dist' folder.")
        print("Make sure ffmpeg is in PATH or in dist/ffmpeg/ffmpeg.exe")
    else:
        print("[ERROR] EXE not found")
        sys.exit(1)
else:
    sys.exit(result.returncode)