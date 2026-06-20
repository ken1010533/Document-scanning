"""掃描路徑新增、刪除、瀏覽與本機記憶。

這個模組從 main_window.py 拆出來，讓主視窗檔案維持薄而好讀。
方法仍以 mixin 形式操作主頁面的 self 狀態，避免重寫既有事件流程。
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import json
import os


class 路徑管理Mixin:
    """掃描路徑新增、刪除、瀏覽與本機記憶。"""

    def 儲存路徑設定(self):
        路徑資料 = []
        for 路徑變數 in self.資料夾路徑列表:
            路徑文字 = 路徑變數.get().strip()
            if 路徑文字:
                路徑資料.append(os.path.normpath(os.path.abspath(路徑文字)))

        with open("last_paths.json", "w", encoding="utf-8") as f:
            json.dump(路徑資料, f, ensure_ascii=False, indent=4)



    def 刪除路徑(self, 路徑框架, 路徑變數):
        路徑框架.destroy()

        if 路徑框架 in self.路徑框架列表:
            self.路徑框架列表.remove(路徑框架)

        if 路徑變數 in self.資料夾路徑列表:
            self.資料夾路徑列表.remove(路徑變數)

        self.儲存路徑設定()

        if not self.資料夾路徑列表:
            self.新增路徑()



    def 加入多個路徑(self):
        已加入數量 = 0

        while True:
            folder = filedialog.askdirectory(title="選擇要掃描的資料夾（取消結束）")
            if not folder:
                break

            正規路徑 = os.path.normpath(os.path.abspath(folder))
            現有路徑 = {
                os.path.normpath(os.path.abspath(路徑變數.get().strip()))
                for 路徑變數 in self.資料夾路徑列表
                if 路徑變數.get().strip()
            }

            if 正規路徑 not in 現有路徑:
                空白路徑變數 = next((路徑變數 for 路徑變數 in self.資料夾路徑列表 if not 路徑變數.get().strip()), None)
                if 空白路徑變數:
                    空白路徑變數.set(正規路徑)
                    self.儲存路徑設定()
                else:
                    self.新增路徑(正規路徑)
                已加入數量 += 1

            繼續 = messagebox.askyesno("繼續加入", "要再加入另一個掃描路徑嗎？")
            if not 繼續:
                break

        if 已加入數量:
            self.狀態標籤.config(text=f"已加入 {已加入數量} 個掃描路徑", foreground="black")



    def 新增路徑(self, 初始路徑=""):
        路徑框架 = ttk.Frame(self.路徑內部框架)
        路徑框架.pack(fill="x", pady=3)

        路徑變數 = tk.StringVar(value=初始路徑)

        輸入框 = ttk.Entry(路徑框架, textvariable=路徑變數)
        輸入框.pack(side="left", fill="x", expand=True, padx=(0, 6))

        ttk.Button(
            路徑框架,
            text="瀏覽",
            width=8,
            command=lambda: self.瀏覽資料夾(路徑變數)
        ).pack(side="left", padx=(0, 6))

        ttk.Button(
            路徑框架,
            text="刪除",
            width=8,
            command=lambda: self.刪除路徑(路徑框架, 路徑變數)
        ).pack(side="left")

        self.路徑框架列表.append(路徑框架)
        self.資料夾路徑列表.append(路徑變數)
        self.儲存路徑設定()



    def 瀏覽資料夾(self, 路徑變數):
        folder = filedialog.askdirectory()
        if folder:
            路徑變數.set(os.path.normpath(os.path.abspath(folder)))
            self.儲存路徑設定()



    def 載入上次路徑(self):
        if os.path.exists("last_paths.json"):
            try:
                with open("last_paths.json", "r", encoding="utf-8") as f:
                    路徑資料 = json.load(f)

                for 路徑 in 路徑資料:
                    self.新增路徑(os.path.normpath(os.path.abspath(路徑)))
            except Exception:
                pass

        if not self.資料夾路徑列表:
            self.新增路徑()

    # =========================
    # 掃描控制
    # =========================




