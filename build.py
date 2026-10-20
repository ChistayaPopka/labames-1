"""
Собирает два exe: dist/Кнопка.exe и dist/Картинка.exe (с иконками).
Нужно: pip install pyinstaller pillow
Запуск: python build.py  (или двойной клик по build.bat)
"""

import os
import subprocess
import sys

import make_icons

HERE = os.path.dirname(os.path.abspath(__file__))
APPS = [
    ("Кнопка", "button.py", "button.ico"),
    ("Картинка", "display.py", "display.ico"),
]


def main():
    os.chdir(HERE)
    make_icons.save_icons()

    for exe_name, script, icon in APPS:
        icon_path = os.path.join("icons", icon)
        subprocess.run([
            sys.executable, "-m", "PyInstaller", "--noconfirm", "--onefile", "--windowed",
            "--name", exe_name, "--icon", icon_path,
            "--add-data", f"{icon_path}{os.pathsep}icons", script,
        ], check=True)

    os.makedirs(os.path.join("dist", "images"), exist_ok=True)
    print("\nГотово: dist\\Кнопка.exe и dist\\Картинка.exe")


if __name__ == "__main__":
    main()
