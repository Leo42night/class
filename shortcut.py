import subprocess
from config.cred import REPO_PATH
import os

BAT_PATH = os.path.join(os.path.dirname(__file__), "C:/Tools/symlink.bat")


def create_symlink(folder_target, folder_link, name_file):
    result = subprocess.run(
        [BAT_PATH, os.path.abspath(f"{folder_target}/{name_file}"), f"{folder_link}/{name_file}"],
        capture_output=True, text=True, shell=True
    )
    if result.returncode == 0:
        print(f"✅ {name_file} di {folder_target} → sekarang ada di {folder_link}")
    else:
        print(f"❌ {result.stderr.strip() or result.stdout.strip()}")

X = "b"
N = "6"
create_symlink(
    f"{REPO_PATH}/class/data_score", f"{REPO_PATH}/ppwl{N}{X}-sub", f"{X}-{N}-score.txt"
)

# shortcut.bat <target_path> <shortcut_dir> [name]
