"""設定分頁。

這個頁面負責讀寫 config.json，並在使用者切換設定時自動保存。
主畫面會透過 core.config.讀取設定() 取得最新設定。
"""

import tkinter as tk
import os
from tkinter import ttk, messagebox, filedialog
from core.config import 儲存設定, 讀取設定


class 設定分頁(ttk.Frame):
    """左側設定頁 UI，集中管理掃描、刪除與 Excel 匯出設定。"""

    def __init__(self, parent, main_app):
        super().__init__(parent)
        self.main_app = main_app

        設定 = 讀取設定()
        self.允許刪除 = tk.BooleanVar(value=設定.get("允許刪除重複檔案", False))
        self.輸出檔名 = tk.StringVar(value=設定.get("Excel輸出檔名", "重複檔案.xlsx"))
        self.輸出資料夾 = tk.StringVar(value=設定.get("Excel輸出資料夾", os.getcwd()))
        self.Excel自動命名 = tk.BooleanVar(value=設定.get("Excel自動命名", False))
        self.Excel掃描後自動匯出 = tk.BooleanVar(value=設定.get("Excel掃描後自動匯出", False))
        self.掃描模式 = tk.StringVar(value=設定.get("掃描模式", "完整"))
        self.掃描空資料夾 = tk.BooleanVar(value=設定.get("掃描空資料夾", False))
        self.快速刪除模式 = tk.BooleanVar(value=設定.get("快速刪除模式", False))
        self.允許勾選保留項目 = tk.BooleanVar(value=設定.get("允許勾選保留項目", False))
        self.啟用忽略路徑 = tk.BooleanVar(value=設定.get("啟用忽略掃描路徑", True))
        self.忽略路徑列表 = [
            os.path.normpath(os.path.abspath(路徑))
            for 路徑 in 設定.get("忽略掃描路徑", [])
            if 路徑
        ]

        self.columnconfigure(0, weight=1)
        self.rowconfigure(14, weight=1)

        ttk.Label(self, text="應用程式設定", font=("Microsoft JhengHei UI", 13, "bold")).grid(
            row=0, column=0, sticky="w", padx=10, pady=(10, 12)
        )

        ttk.Checkbutton(
            self,
            text="允許移到回收桶",
            variable=self.允許刪除
        ).grid(row=1, column=0, sticky="w", padx=10, pady=(0, 10))

        ttk.Label(self, text="Excel 輸出資料夾").grid(row=2, column=0, sticky="w", padx=10)
        Excel資料夾列 = ttk.Frame(self)
        Excel資料夾列.grid(row=3, column=0, sticky="ew", padx=10, pady=(2, 8))
        Excel資料夾列.columnconfigure(0, weight=1)
        ttk.Entry(Excel資料夾列, textvariable=self.輸出資料夾).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ttk.Button(Excel資料夾列, text="瀏覽", command=self.選擇Excel輸出資料夾).grid(row=0, column=1)

        ttk.Checkbutton(
            self,
            text="Excel 檔案自動命名",
            variable=self.Excel自動命名,
            command=self.自動儲存
        ).grid(row=4, column=0, sticky="w", padx=10, pady=(0, 6))

        ttk.Checkbutton(
            self,
            text="掃描完成後自動匯出 Excel",
            variable=self.Excel掃描後自動匯出,
            command=self.自動儲存
        ).grid(row=5, column=0, sticky="w", padx=10, pady=(0, 6))

        ttk.Label(self, text="Excel 固定檔名").grid(row=6, column=0, sticky="w", padx=10)
        self.輸出檔名輸入框 = ttk.Entry(self, textvariable=self.輸出檔名)
        self.輸出檔名輸入框.grid(row=7, column=0, sticky="ew", padx=10, pady=(2, 8))
        self.輸出檔名輸入框.bind("<FocusOut>", lambda e: self.自動儲存())
        self.輸出檔名輸入框.bind("<Return>", lambda e: self.自動儲存())

        ttk.Label(self, text="掃描模式").grid(row=8, column=0, sticky="w", padx=10)
        ttk.Combobox(
            self,
            textvariable=self.掃描模式,
            values=["完整", "快速"],
            state="readonly"
        ).grid(row=9, column=0, sticky="ew", padx=10, pady=(2, 10))
        self.掃描模式.trace_add("write", lambda *_: self.自動儲存())

        ttk.Checkbutton(
            self,
            text="掃描空資料夾",
            variable=self.掃描空資料夾,
            command=self.自動儲存
        ).grid(row=10, column=0, sticky="w", padx=10, pady=(2, 6))

        ttk.Checkbutton(
            self,
            text="啟用快速刪除模式",
            variable=self.快速刪除模式,
            command=self.自動儲存
        ).grid(row=11, column=0, sticky="w", padx=10, pady=(2, 6))

        ttk.Checkbutton(
            self,
            text="允許勾選每組第 1 個檔案",
            variable=self.允許勾選保留項目,
            command=self.保留項目設定變更
        ).grid(row=12, column=0, sticky="w", padx=10, pady=(2, 6))

        ttk.Checkbutton(
            self,
            text="啟用忽略掃描路徑",
            variable=self.啟用忽略路徑,
            command=self.自動儲存
        ).grid(row=13, column=0, sticky="w", padx=10, pady=(2, 6))

        忽略框架 = ttk.LabelFrame(self, text="忽略掃描路徑")
        忽略框架.grid(row=14, column=0, sticky="nsew", padx=10, pady=(0, 10))
        忽略框架.columnconfigure(0, weight=1)
        忽略框架.rowconfigure(0, weight=1)

        self.忽略清單 = tk.Listbox(忽略框架, height=7, exportselection=False)
        self.忽略清單.grid(row=0, column=0, sticky="nsew")
        忽略滾動條 = ttk.Scrollbar(忽略框架, orient="vertical", command=self.忽略清單.yview)
        忽略滾動條.grid(row=0, column=1, sticky="ns")
        self.忽略清單.configure(yscrollcommand=忽略滾動條.set)

        忽略按鈕列 = ttk.Frame(忽略框架)
        忽略按鈕列.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        for 欄位 in range(3):
            忽略按鈕列.columnconfigure(欄位, weight=1, uniform="忽略按鈕")
        ttk.Button(忽略按鈕列, text="加入", command=self.加入忽略路徑).grid(row=0, column=0, sticky="ew", padx=(0, 4))
        ttk.Button(忽略按鈕列, text="移除", command=self.移除忽略路徑).grid(row=0, column=1, sticky="ew", padx=4)
        ttk.Button(忽略按鈕列, text="清空", command=self.清空忽略路徑).grid(row=0, column=2, sticky="ew", padx=(4, 0))

        ttk.Button(self, text="儲存設定", command=self.儲存).grid(row=15, column=0, sticky="ew", padx=10, pady=(0, 10))
        self.刷新忽略清單()

    def 選擇Excel輸出資料夾(self):
        路徑 = filedialog.askdirectory(title="選擇 Excel 輸出資料夾")
        if 路徑:
            self.輸出資料夾.set(os.path.normpath(os.path.abspath(路徑)))
            self.自動儲存()

    def 刷新忽略清單(self):
        self.忽略清單.delete(0, "end")
        for 路徑 in self.忽略路徑列表:
            self.忽略清單.insert("end", 路徑)

    def 加入忽略路徑(self):
        while True:
            路徑 = filedialog.askdirectory(title="選擇要忽略的資料夾（取消結束）")
            if not 路徑:
                break

            正規路徑 = os.path.normpath(os.path.abspath(路徑))
            if 正規路徑 not in self.忽略路徑列表:
                self.忽略路徑列表.append(正規路徑)

            繼續 = messagebox.askyesno("繼續加入", "要再加入另一個忽略路徑嗎？")
            if not 繼續:
                break

        self.刷新忽略清單()
        self.自動儲存()

    def 移除忽略路徑(self):
        選取索引 = list(self.忽略清單.curselection())
        if not 選取索引:
            messagebox.showinfo("提示", "請先選擇要移除的忽略路徑")
            return

        for 索引 in reversed(選取索引):
            del self.忽略路徑列表[索引]
        self.刷新忽略清單()
        self.自動儲存()

    def 清空忽略路徑(self):
        if not self.忽略路徑列表:
            return
        if messagebox.askyesno("確認清空", "確定要清空所有忽略掃描路徑嗎？"):
            self.忽略路徑列表.clear()
            self.刷新忽略清單()
            self.自動儲存()

    def 儲存(self, 顯示提示=True):
        """把畫面上的設定寫回 config.json。"""
        輸出檔名 = self.輸出檔名.get().strip() or "重複檔案.xlsx"
        輸出資料夾 = self.輸出資料夾.get().strip() or os.getcwd()
        輸出資料夾 = os.path.normpath(os.path.abspath(輸出資料夾))

        if not 輸出檔名.lower().endswith(".xlsx"):
            輸出檔名 += ".xlsx"

        if not os.path.isdir(輸出資料夾):
            if 顯示提示:
                messagebox.showwarning("設定未儲存", "Excel 輸出資料夾不存在")
            return

        儲存設定({
            "允許刪除重複檔案": self.允許刪除.get(),
            "Excel輸出檔名": 輸出檔名,
            "Excel輸出資料夾": 輸出資料夾,
            "Excel自動命名": self.Excel自動命名.get(),
            "Excel掃描後自動匯出": self.Excel掃描後自動匯出.get(),
            "掃描模式": self.掃描模式.get(),
            "掃描空資料夾": self.掃描空資料夾.get(),
            "快速刪除模式": self.快速刪除模式.get(),
            "允許勾選保留項目": self.允許勾選保留項目.get(),
            "啟用忽略掃描路徑": self.啟用忽略路徑.get(),
            "忽略掃描路徑": self.忽略路徑列表
        })
        self.輸出檔名.set(輸出檔名)
        self.輸出資料夾.set(輸出資料夾)
        if 顯示提示:
            messagebox.showinfo("提示", "設定已儲存")

    def 自動儲存(self):
        """給 Checkbutton / Entry 使用；失敗時不跳提示避免干擾輸入。"""
        try:
            self.儲存(顯示提示=False)
        except Exception:
            pass

    def 保留項目設定變更(self):
        """允許勾選第 1 個檔案時，立即同步更新主畫面既有結果。"""
        self.自動儲存()
        主頁面 = getattr(self.main_app, "主頁面", None)
        if 主頁面:
            主頁面.套用保留項目設定(self.允許勾選保留項目.get())
