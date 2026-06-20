from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "dist" / "installer"
EXE_NAME = "长篇网文蒸馏器"

cmd = [
    sys.executable,
    "-m",
    "PyInstaller",
    "--noconsole",
    "--onefile",
    "--name",
    EXE_NAME,
    "--distpath",
    str(OUTPUT_DIR),
    "--workpath",
    str(ROOT / "build"),
    "--specpath",
    str(ROOT / "build"),
    "--add-data",
    f"{ROOT / 'templates'};templates",
    "--add-data",
    f"{ROOT / 'prompts'};prompts",
    "--add-data",
    f"{ROOT / 'scripts'};scripts",
    str(ROOT / "app.py"),
]

print("正在构建 Windows 可执行文件...")
subprocess.run(cmd, check=True)
print(f"可执行文件已输出到：{OUTPUT_DIR}")
