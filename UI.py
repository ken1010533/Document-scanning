"""應用程式啟動入口。

實際的主視窗與頁面邏輯放在 UI/main_window.py。
保留這個薄入口，之後啟動方式仍可使用：
aaaaaa
    python UI.py
"""

from UI.main_window import 主應用程式
import subprocess
import sys
from pathlib import Path
from tkinter import messagebox

PROJECT_DIR = Path(__file__).resolve().parent
    
def run(cmd):
    return subprocess.run(
        cmd,
        cwd=PROJECT_DIR,
        shell=True,
        text=True,
        capture_output=True
    )

def check_update():
    run("git remote update")

    result = run("git status -uno")

    if "behind" not in result.stdout:
        return False

    yes = messagebox.askyesno(
        "發現新版本",
        "GitHub 上有新版本，要現在更新嗎？\n\n更新後程式會關閉，請重新打開。"
    )

    if not yes:
        return False

    run("git reset --hard")
    pull = run("git pull")

    if pull.returncode == 0:
        messagebox.showinfo("更新完成", "更新完成，請重新啟動程式。")
        sys.exit()
    else:
        messagebox.showerror("更新失敗", pull.stderr)

    return True

if __name__ == "__main__":
    app = 主應用程式()
    app.mainloop()
