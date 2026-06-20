"""應用程式啟動入口。

實際的主視窗與頁面邏輯放在 UI/main_window.py。
保留這個薄入口，之後啟動方式仍可使用：

    python UI.py
"""

from UI.main_window import 主應用程式
import requests
import zipfile
import shutil
import hashlib
import sys
from pathlib import Path
from tkinter import messagebox

GitHub壓縮檔網址 = (
    "https://github.com/ken1010533/Document-scanning/archive/refs/heads/main.zip"
)

專案資料夾 = Path(__file__).resolve().parent
更新壓縮檔 = 專案資料夾 / "update.zip"
暫存資料夾 = 專案資料夾 / "_update_temp"

忽略項目 = {
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "update.zip",
    "_update_temp",
    "config.json",
    "settings.json",
}

def 計算檔案雜湊值(檔案路徑):
    雜湊 = hashlib.sha256()

    with open(檔案路徑, "rb") as 檔案:
        for 區塊 in iter(lambda: 檔案.read(1024 * 1024), b""):
            雜湊.update(區塊)

    return 雜湊.hexdigest()

def 是否忽略(路徑):
    return any(部分 in 忽略項目 for 部分 in 路徑.parts)

def 檢查是否有差異(雲端資料夾):

    for 雲端檔案 in 雲端資料夾.rglob("*"):

        if not 雲端檔案.is_file():
            continue

        相對路徑 = 雲端檔案.relative_to(雲端資料夾)

        if 是否忽略(相對路徑):
            continue

        本機檔案 = 專案資料夾 / 相對路徑

        if not 本機檔案.exists():
            return True

        if 計算檔案雜湊值(雲端檔案) != 計算檔案雜湊值(本機檔案):
            return True

    return False

def 檢查更新():

    try:

        回應 = requests.get(GitHub壓縮檔網址, timeout=30)
        回應.raise_for_status()

        更新壓縮檔.write_bytes(回應.content)

        if 暫存資料夾.exists():
            shutil.rmtree(暫存資料夾)

        with zipfile.ZipFile(更新壓縮檔, "r") as 壓縮檔:
            壓縮檔.extractall(暫存資料夾)

        GitHub資料夾 = next(暫存資料夾.iterdir())

        if not 檢查是否有差異(GitHub資料夾):

            更新壓縮檔.unlink(missing_ok=True)
            shutil.rmtree(暫存資料夾)

            messagebox.showinfo(
                "檢查更新",
                "目前已是最新版本。"
            )

            return

        是否更新 = messagebox.askyesno(
            "發現更新",
            "偵測到 GitHub 版本與本機版本不同。\n\n是否立即更新？"
        )

        if 是否更新:
            執行更新(GitHub資料夾)

        else:
            更新壓縮檔.unlink(missing_ok=True)
            shutil.rmtree(暫存資料夾)

    except Exception as 錯誤:

        messagebox.showerror(
            "檢查更新失敗",
            f"檢查更新時發生錯誤：\n\n{錯誤}"
        )

def 執行更新(GitHub資料夾):

    try:

        for 項目 in GitHub資料夾.iterdir():

            if 項目.name in 忽略項目:
                continue

            目標路徑 = 專案資料夾 / 項目.name

            if 目標路徑.exists():

                if 目標路徑.is_dir():
                    shutil.rmtree(目標路徑)
                else:
                    目標路徑.unlink()

            if 項目.is_dir():
                shutil.copytree(項目, 目標路徑)
            else:
                shutil.copy2(項目, 目標路徑)

        更新壓縮檔.unlink(missing_ok=True)
        shutil.rmtree(暫存資料夾)

        messagebox.showinfo(
            "更新完成",
            "程式已更新完成。\n\n請重新啟動程式。"
        )

        sys.exit()

    except Exception as 錯誤:

        messagebox.showerror(
            "更新失敗",
            f"更新過程發生錯誤：\n\n{錯誤}"
        )

if __name__ == "__main__":
    app = 主應用程式()
    app.mainloop()
