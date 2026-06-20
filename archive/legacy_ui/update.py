from tkinter import ttk, messagebox
import threading

from core.updater import 檢查更新


class 更新分頁(ttk.Frame):
    def __init__(self, parent, notebook):
        super().__init__(parent)
        self.notebook = notebook

        # 標題
        ttk.Label(self, text="版本：1.0.0", font=("Arial", 12)).pack(pady=10)

        # 狀態文字
        self.狀態文字 = ttk.Label(self, text="尚未檢查更新")
        self.狀態文字.pack(pady=5)

        # 按鈕
        ttk.Button(self, text="檢查更新", command=self.開始檢查).pack(pady=10)

        ttk.Button(
            self,
            text="返回首頁",
            command=lambda: self.notebook.select(0)
        ).pack(pady=10)

    # =========================
    # 開始檢查（避免卡 UI）
    # =========================
    def 開始檢查(self):
        self.狀態文字.config(text="🔍 檢查更新中...")
        threading.Thread(target=self.檢查更新執行, daemon=True).start()

    # =========================
    # 真正執行更新
    # =========================
    def 檢查更新執行(self):
        結果 = 檢查更新()

        # 回到主執行緒更新 UI
        self.after(0, self.顯示結果, 結果)

    # =========================
    # 顯示結果
    # =========================
    def 顯示結果(self, 結果):
        self.狀態文字.config(text=結果)

        # 彈出提示
        messagebox.showinfo("更新結果", 結果)