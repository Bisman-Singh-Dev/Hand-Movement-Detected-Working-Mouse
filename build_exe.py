"""
Automated PyInstaller Build Script.
Packages Hand-Movement-Detected-Working-Mouse into a standalone Windows .exe.
Collects MediaPipe graph definitions, protobufs, OpenCV binaries, and dependencies.
"""

import os
import sys
import subprocess
import shutil

def build():
    print("================================================================")
    print(" 🛠️  Building Hand Mouse Standalone Executable (.exe)")
    print("================================================================")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    dist_dir = os.path.join(base_dir, "dist")
    build_dir = os.path.join(base_dir, "build")

    # Command line arguments for PyInstaller
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--name=HandMousePro",
        "--icon=assets/icon.ico",
        "--onefile",
        "--collect-all=mediapipe",
        "--collect-data=cv2",
        "--exclude-module=matplotlib",
        "--exclude-module=tkinter",
        "--exclude-module=_tkinter",
        "--exclude-module=IPython",
        "--hidden-import=mediapipe",
        "--hidden-import=cv2",
        "--hidden-import=pyautogui",
        "--hidden-import=pynput",
        "--hidden-import=numpy",
        "--hidden-import=PIL",
        "--add-data=config.py;.",
        os.path.join(base_dir, "main.py")
    ]

    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=base_dir)

    if result.returncode == 0:
        exe_path = os.path.join(dist_dir, "HandMousePro.exe")
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print("================================================================")
            print(" ✅ BUILD SUCCESSFUL!")
            print(f" 📦 Executable: {exe_path}")
            print(f" 📊 File Size  : {size_mb:.2f} MB")
            print("================================================================")
            return True
    
    print("❌ Build failed with return code:", result.returncode)
    return False

if __name__ == "__main__":
    success = build()
    sys.exit(0 if success else 1)
