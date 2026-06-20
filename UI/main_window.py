"""主視窗與主要互動流程。

這個檔案負責把路徑管理、掃描結果、預覽、匯出與刪除流程串起來。
較獨立的設定頁、檔案類型常數與視窗工具已拆到其他 UI 模組。
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import json
import os
import mimetypes
import subprocess
import platform
from datetime import datetime
from core.excel_export import 輸出Excel
from PIL import Image, ImageTk
from send2trash import send2trash

from UI.settings import 設定分頁
from UI.file_types import 圖片副檔名集合, 影片副檔名集合, 文字副檔名集合, 文件副檔名集合
from UI.window_utils import 主視窗至中
from core.duplicate_finder import 找出重複檔案, 找出空資料夾
from core.config import 讀取設定


# =========================
# 主應用程式
# =========================
class 主應用程式(tk.Tk):
    """Tk 應用程式根視窗，負責建立左右兩側主要版面。"""

    def __init__(self):
        super().__init__()
        self.title("重複檔案管理工具")
        self.minsize(980, 620)

        self.套用樣式()
        self.建立版面()
        主視窗至中(self)

    def 套用樣式(self):
        style = ttk.Style()

        try:
            if "vista" in style.theme_names():
                style.theme_use("vista")
            elif "clam" in style.theme_names():
                style.theme_use("clam")
        except Exception:
            pass

        style.configure("TButton", padding=(8, 6))
        style.configure("Treeview", rowheight=28)
        style.configure("Treeview.Heading", font=("Microsoft JhengHei UI", 10, "bold"))
        style.configure("狀態列.TLabel", padding=(8, 6))
        style.configure("區塊.TLabelframe", padding=10)
        style.configure("區塊.TLabelframe.Label", font=("Microsoft JhengHei UI", 10, "bold"))

    def 建立版面(self):
        主框架 = ttk.Panedwindow(self, orient="horizontal")
        主框架.pack(fill="both", expand=True, padx=10, pady=10)

        左側框架 = ttk.Frame(主框架)
        右側框架 = ttk.Frame(主框架)
        主框架.add(左側框架, weight=1)
        主框架.add(右側框架, weight=4)

        self.左側分頁 = ttk.Notebook(左側框架)
        self.左側分頁.pack(fill="both", expand=True)

        路徑分頁 = ttk.Frame(self.左側分頁)
        設定分頁框架 = ttk.Frame(self.左側分頁)
        self.左側分頁.add(路徑分頁, text="檔案路徑")
        self.左側分頁.add(設定分頁框架, text="設定")
        self.左側分頁.select(路徑分頁)

        self.設定頁 = 設定分頁(設定分頁框架, self)
        self.設定頁.pack(fill="both", expand=True)

        self.主頁面 = 主頁面區域(右側框架, 路徑分頁)
        self.主頁面.pack(fill="both", expand=True)


# =========================
# 主頁面區域
# =========================
class 主頁面區域(ttk.Frame):
    """主操作區：管理路徑、掃描、結果列表、預覽與刪除。"""

    def __init__(self, parent, 路徑父容器=None):
        super().__init__(parent)

        self.parent = parent
        self.路徑父容器 = 路徑父容器
        self.資料夾路徑列表 = []
        self.路徑框架列表 = []
        self.最後掃描結果 = []
        self.最後空資料夾結果 = []
        self.項目路徑對照 = {}
        self.不可勾選項目 = set()
        self.保留項目集合 = set()
        self.空資料夾項目集合 = set()

        self.掃描中 = False
        self.取消掃描中 = False
        self.刪除進行中 = False
        self.取消刪除中 = False

        self.預覽圖片物件 = None
        self.影片擷取器 = None
        self.影片播放中 = False
        self.影片播放工作 = None
        self.目前影片路徑 = None
        self.影片FPS = 25
        self.影片總影格 = 0
        self.影片進度拖曳中 = False
        self.拖曳前影片播放中 = False

        self.建立介面()
        self.載入上次路徑()

    def 取得設定(self):
        """統一從 config.json 讀取設定，並補上預設值。"""
        設定 = 讀取設定()
        return {
            "允許刪除重複檔案": 設定.get("允許刪除重複檔案", False),
            "Excel輸出檔名": 設定.get("Excel輸出檔名", "重複檔案.xlsx"),
            "Excel輸出資料夾": 設定.get("Excel輸出資料夾", os.getcwd()),
            "Excel自動命名": 設定.get("Excel自動命名", False),
            "Excel掃描後自動匯出": 設定.get("Excel掃描後自動匯出", False),
            "掃描模式": 設定.get("掃描模式", "完整"),
            "掃描空資料夾": 設定.get("掃描空資料夾", False),
            "快速刪除模式": 設定.get("快速刪除模式", False),
            "允許勾選保留項目": 設定.get("允許勾選保留項目", False),
            "啟用忽略掃描路徑": 設定.get("啟用忽略掃描路徑", True),
            "忽略掃描路徑": [
                os.path.normpath(os.path.abspath(路徑))
                for 路徑 in 設定.get("忽略掃描路徑", [])
                if 路徑
            ]
        }

    # =========================
    # 建立介面
    # =========================
    def 建立介面(self):
        上方區域 = ttk.Frame(self)
        上方區域.pack(fill="x")
        self.bind("<Configure>", self.更新自適應尺寸)

        self.建立路徑管理(self.路徑父容器 or 上方區域)

        操作框架 = ttk.LabelFrame(上方區域, text="🛠 操作功能", style="區塊.TLabelframe")
        操作框架.pack(fill="x", pady=(0, 8))

        按鈕框架 = ttk.Frame(操作框架)
        按鈕框架.pack(fill="x")
        批次按鈕框架 = ttk.Frame(操作框架)
        批次按鈕框架.pack(fill="x", pady=(8, 0))
        for 欄位 in range(5):
            按鈕框架.columnconfigure(欄位, weight=1, uniform="主要操作")
        for 欄位 in range(3):
            批次按鈕框架.columnconfigure(欄位, weight=1, uniform="批次操作")

        self.開始掃描按鈕 = ttk.Button(按鈕框架, text="🔍 開始掃描", command=self.開始掃描)
        self.開始掃描按鈕.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        self.取消按鈕 = ttk.Button(按鈕框架, text="⛔ 取消", command=self.取消目前作業, state="disabled")
        self.取消按鈕.grid(row=0, column=1, sticky="ew", padx=4)

        self.開啟結果按鈕 = ttk.Button(按鈕框架, text="📂 開啟上次結果", command=self.開啟上次結果)
        self.開啟結果按鈕.grid(row=0, column=2, sticky="ew", padx=4)

        self.預覽按鈕 = ttk.Button(按鈕框架, text="👁 外部開啟", command=self.即時預覽)
        self.預覽按鈕.grid(row=0, column=3, sticky="ew", padx=4)

        self.匯出按鈕 = ttk.Button(按鈕框架, text="📎 匯出 Excel", command=self.匯出Excel)
        self.匯出按鈕.grid(row=0, column=4, sticky="ew", padx=(4, 0))

        self.全部勾選按鈕 = ttk.Button(批次按鈕框架, text="☑ 全部勾選", command=self.全部勾選)
        self.全部勾選按鈕.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        self.全部取消按鈕 = ttk.Button(批次按鈕框架, text="☐ 全部取消", command=self.全部取消勾選)
        self.全部取消按鈕.grid(row=0, column=1, sticky="ew", padx=4)

        self.刪除按鈕 = ttk.Button(批次按鈕框架, text="🗑 移到回收桶", command=self.刪除已勾選檔案)
        self.刪除按鈕.grid(row=0, column=2, sticky="ew", padx=(4, 0))

        進度框架 = ttk.Frame(操作框架)
        進度框架.pack(fill="x", pady=(10, 0))

        self.進度條 = ttk.Progressbar(進度框架, mode="determinate", maximum=100)
        self.進度條.pack(fill="x", pady=(0, 6))

        self.進度文字標籤 = ttk.Label(進度框架, text="尚未開始掃描")
        self.進度文字標籤.pack(anchor="w")

        中下區域 = ttk.Panedwindow(self, orient="horizontal")
        中下區域.pack(fill="both", expand=True)

        左側結果框 = ttk.Frame(中下區域)
        右側預覽框 = ttk.Frame(中下區域, width=380)

        中下區域.add(左側結果框, weight=3)
        中下區域.add(右側預覽框, weight=2)

        結果框架 = ttk.LabelFrame(左側結果框, text="📋 重複檔案結果", style="區塊.TLabelframe")
        結果框架.pack(fill="both", expand=True)

        結果上方資訊列 = ttk.Frame(結果框架)
        結果上方資訊列.pack(fill="x", pady=(0, 8))
        結果上方資訊列.columnconfigure(0, weight=1)
        結果上方資訊列.columnconfigure(1, weight=1)

        self.結果摘要標籤 = ttk.Label(結果上方資訊列, text="尚未開始掃描")
        self.結果摘要標籤.grid(row=0, column=0, sticky="w", padx=(0, 8))

        self.勾選摘要標籤 = ttk.Label(結果上方資訊列, text="已勾選 0 個項目，總大小 0.00 MB")
        self.勾選摘要標籤.grid(row=0, column=1, sticky="e")

        self.結果樹狀框架 = ttk.Frame(結果框架)
        self.結果樹狀框架.pack(fill="both", expand=True)

        columns = ("選取", "類型", "檔案名稱", "完整路徑", "大小(MB)")
        self.tree = ttk.Treeview(
            self.結果樹狀框架,
            columns=columns,
            show="tree headings",
            selectmode="browse"
        )

        self.tree.heading("#0", text="群組")
        self.tree.heading("選取", text="刪除")
        self.tree.heading("類型", text="類型")
        self.tree.heading("檔案名稱", text="檔案名稱")
        self.tree.heading("完整路徑", text="完整路徑")
        self.tree.heading("大小(MB)", text="大小(MB)")

        self.tree.column("#0", width=92, anchor="w", stretch=False)
        self.tree.column("選取", width=70, anchor="center", stretch=False)
        self.tree.column("類型", width=82, anchor="center", stretch=False)
        self.tree.column("檔案名稱", width=260, anchor="w", minwidth=140)
        self.tree.column("完整路徑", width=460, anchor="w", minwidth=220)
        self.tree.column("大小(MB)", width=100, anchor="center", stretch=False)

        self.tree_y_scroll = ttk.Scrollbar(self.結果樹狀框架, orient="vertical", command=self.tree.yview)
        self.tree_x_scroll = ttk.Scrollbar(self.結果樹狀框架, orient="horizontal", command=self.tree.xview)

        self.tree.configure(
            yscrollcommand=self.tree_y_scroll.set,
            xscrollcommand=self.tree_x_scroll.set
        )

        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree_y_scroll.grid(row=0, column=1, sticky="ns")
        self.tree_x_scroll.grid(row=1, column=0, sticky="ew")

        self.結果樹狀框架.rowconfigure(0, weight=1)
        self.結果樹狀框架.columnconfigure(0, weight=1)

        self.tree.bind("<Button-1>", self.點擊樹狀表格)
        self.tree.bind("<<TreeviewSelect>>", self.更新右側預覽)

        預覽框架 = ttk.LabelFrame(右側預覽框, text="預覽", style="區塊.TLabelframe")
        預覽框架.pack(fill="both", expand=True)

        預覽標頭框架 = ttk.Frame(預覽框架)
        預覽標頭框架.pack(fill="x", pady=(0, 8))

        self.預覽類型標籤 = ttk.Label(預覽標頭框架, text="未選擇", foreground="gray")
        self.預覽類型標籤.pack(anchor="w")

        self.預覽標題標籤 = ttk.Label(
            預覽標頭框架,
            text="請在左側選擇檔案",
            font=("Microsoft JhengHei UI", 10, "bold"),
            wraplength=360
        )
        self.預覽標題標籤.pack(fill="x", anchor="w", pady=(2, 0))

        self.預覽內容框架 = ttk.Frame(預覽框架)
        self.預覽內容框架.pack(fill="both", expand=True, pady=(0, 8))

        self.預覽圖片標籤 = ttk.Label(
            self.預覽內容框架,
            text="尚未選擇檔案",
            anchor="center",
            justify="center",
            background="#f7f7f7",
            relief="solid"
        )
        self.預覽圖片標籤.pack(fill="both", expand=True)

        self.預覽文字框架 = ttk.Frame(self.預覽內容框架)
        self.預覽文字 = tk.Text(
            self.預覽文字框架,
            wrap="none",
            height=12,
            font=("Consolas", 10),
            state="disabled",
            padx=8,
            pady=8
        )
        self.預覽文字Y軸 = ttk.Scrollbar(self.預覽文字框架, orient="vertical", command=self.預覽文字.yview)
        self.預覽文字X軸 = ttk.Scrollbar(self.預覽文字框架, orient="horizontal", command=self.預覽文字.xview)
        self.預覽文字.configure(yscrollcommand=self.預覽文字Y軸.set, xscrollcommand=self.預覽文字X軸.set)
        self.預覽文字.grid(row=0, column=0, sticky="nsew")
        self.預覽文字Y軸.grid(row=0, column=1, sticky="ns")
        self.預覽文字X軸.grid(row=1, column=0, sticky="ew")
        self.預覽文字框架.rowconfigure(0, weight=1)
        self.預覽文字框架.columnconfigure(0, weight=1)

        self.預覽影片框架 = ttk.Frame(self.預覽內容框架)
        self.預覽影片畫面 = ttk.Label(
            self.預覽影片框架,
            text="尚未載入影片",
            anchor="center",
            justify="center",
            background="#111111",
            foreground="white",
            relief="solid"
        )
        self.預覽影片畫面.pack(fill="both", expand=True)

        影片進度列 = ttk.Frame(self.預覽影片框架)
        影片進度列.pack(fill="x", pady=(8, 0))
        影片進度列.columnconfigure(0, weight=1)

        self.影片進度變數 = tk.DoubleVar(value=0)
        self.影片進度滑桿 = ttk.Scale(
            影片進度列,
            from_=0,
            to=0,
            orient="horizontal",
            variable=self.影片進度變數,
            command=self.拖曳影片進度
        )
        self.影片進度滑桿.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.影片時間標籤 = ttk.Label(影片進度列, text="00:00 / 00:00", width=15, anchor="e")
        self.影片時間標籤.grid(row=0, column=1, sticky="e")
        self.影片進度滑桿.bind("<ButtonPress-1>", self.開始拖曳影片進度)
        self.影片進度滑桿.bind("<ButtonRelease-1>", self.完成拖曳影片進度)

        影片控制列 = ttk.Frame(self.預覽影片框架)
        影片控制列.pack(fill="x", pady=(8, 0))
        影片控制列.columnconfigure(0, weight=1)
        影片控制列.columnconfigure(1, weight=1)
        影片控制列.columnconfigure(2, weight=1)

        self.影片播放按鈕 = ttk.Button(影片控制列, text="播放", command=self.播放影片)
        self.影片播放按鈕.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        self.影片暫停按鈕 = ttk.Button(影片控制列, text="暫停", command=self.暫停影片)
        self.影片暫停按鈕.grid(row=0, column=1, sticky="ew", padx=4)
        self.影片停止按鈕 = ttk.Button(影片控制列, text="停止", command=self.停止影片播放)
        self.影片停止按鈕.grid(row=0, column=2, sticky="ew", padx=(4, 0))

        預覽資訊框架 = ttk.LabelFrame(預覽框架, text="檔案資訊")
        預覽資訊框架.pack(fill="both", expand=False)

        self.預覽資訊文字 = tk.Text(
            預覽資訊框架,
            height=7,
            wrap="word",
            font=("Microsoft JhengHei UI", 9),
            state="disabled",
            padx=8,
            pady=6,
            relief="flat"
        )
        self.預覽資訊Y軸 = ttk.Scrollbar(預覽資訊框架, orient="vertical", command=self.預覽資訊文字.yview)
        self.預覽資訊文字.configure(yscrollcommand=self.預覽資訊Y軸.set)
        self.預覽資訊文字.grid(row=0, column=0, sticky="nsew")
        self.預覽資訊Y軸.grid(row=0, column=1, sticky="ns")
        預覽資訊框架.rowconfigure(0, weight=1)
        預覽資訊框架.columnconfigure(0, weight=1)
        self.設定預覽資訊("類型：\n檔名：\n路徑：\n大小：")

        狀態框架 = ttk.Frame(self)
        狀態框架.pack(fill="x", pady=(8, 0))

        self.狀態標籤 = ttk.Label(狀態框架, text="就緒", style="狀態列.TLabel", foreground="gray")
        self.狀態標籤.pack(side="left")

    def 更新自適應尺寸(self, event=None):
        寬度 = max(self.winfo_width(), 320)
        預覽換行寬度 = max(220, min(520, int(寬度 * 0.32)))
        self.預覽標題標籤.configure(wraplength=預覽換行寬度)

    def 建立路徑管理(self, parent):
        路徑管理框架 = ttk.LabelFrame(parent, text="檔案路徑管理", style="區塊.TLabelframe")
        路徑管理框架.pack(fill="both", expand=True, padx=6, pady=6)

        路徑說明 = ttk.Label(
            路徑管理框架,
            text="加入要掃描的資料夾。"
        )
        路徑說明.pack(anchor="w", pady=(0, 8))

        路徑清單外框 = ttk.Frame(路徑管理框架)
        路徑清單外框.pack(fill="both", expand=True)

        self.路徑畫布 = tk.Canvas(路徑清單外框, height=160, highlightthickness=0)
        self.路徑滾動條 = ttk.Scrollbar(路徑清單外框, orient="vertical", command=self.路徑畫布.yview)
        self.路徑畫布.configure(yscrollcommand=self.路徑滾動條.set)

        self.路徑畫布.pack(side="left", fill="both", expand=True)
        self.路徑滾動條.pack(side="right", fill="y")

        self.路徑內部框架 = ttk.Frame(self.路徑畫布)
        self.路徑內部視窗 = self.路徑畫布.create_window((0, 0), window=self.路徑內部框架, anchor="nw")

        self.路徑內部框架.bind(
            "<Configure>",
            lambda e: self.路徑畫布.configure(scrollregion=self.路徑畫布.bbox("all"))
        )
        self.路徑畫布.bind(
            "<Configure>",
            lambda e: self.路徑畫布.itemconfigure(self.路徑內部視窗, width=e.width)
        )

        路徑按鈕列 = ttk.Frame(路徑管理框架)
        路徑按鈕列.pack(fill="x", pady=(8, 0))
        路徑按鈕列.columnconfigure(0, weight=1)
        路徑按鈕列.columnconfigure(1, weight=1)
        ttk.Button(路徑按鈕列, text="新增路徑", command=self.新增路徑).grid(row=0, column=0, sticky="ew", padx=(0, 4))
        ttk.Button(路徑按鈕列, text="批次加入", command=self.加入多個路徑).grid(row=0, column=1, sticky="ew", padx=(4, 0))

    # =========================
    # 路徑管理
    # =========================
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

    def 瀏覽資料夾(self, 路徑變數):
        folder = filedialog.askdirectory()
        if folder:
            路徑變數.set(os.path.normpath(os.path.abspath(folder)))
            self.儲存路徑設定()

    def 刪除路徑(self, 路徑框架, 路徑變數):
        路徑框架.destroy()

        if 路徑框架 in self.路徑框架列表:
            self.路徑框架列表.remove(路徑框架)

        if 路徑變數 in self.資料夾路徑列表:
            self.資料夾路徑列表.remove(路徑變數)

        self.儲存路徑設定()

        if not self.資料夾路徑列表:
            self.新增路徑()

    def 儲存路徑設定(self):
        路徑資料 = []
        for 路徑變數 in self.資料夾路徑列表:
            路徑文字 = 路徑變數.get().strip()
            if 路徑文字:
                路徑資料.append(os.path.normpath(os.path.abspath(路徑文字)))

        with open("last_paths.json", "w", encoding="utf-8") as f:
            json.dump(路徑資料, f, ensure_ascii=False, indent=4)

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
    def 開始掃描(self):
        if self.掃描中 or self.刪除進行中:
            return

        有效路徑 = []
        for 路徑變數 in self.資料夾路徑列表:
            路徑 = 路徑變數.get().strip()
            if 路徑:
                正規路徑 = os.path.normpath(os.path.abspath(路徑))
                if os.path.exists(正規路徑):
                    有效路徑.append(正規路徑)

        if not 有效路徑:
            messagebox.showwarning("警告", "請至少新增一個有效的資料夾路徑")
            return

        設定 = self.取得設定()

        self.掃描中 = True
        self.取消掃描中 = False
        self.設定按鈕狀態(False)
        self.取消按鈕.config(state="normal")
        self.清空列表()
        self.最後掃描結果 = []
        self.最後空資料夾結果 = []
        self.進度條["value"] = 0
        self.進度文字標籤.config(text="準備開始掃描...")
        self.狀態標籤.config(text="掃描中，請稍候...", foreground="blue")
        self.結果摘要標籤.config(text="正在掃描資料夾...")
        self.勾選摘要標籤.config(text="已勾選 0 個項目，總大小 0.00 MB")

        threading.Thread(
            target=self.掃描執行,
            args=(
                有效路徑,
                設定["掃描模式"],
                設定["忽略掃描路徑"] if 設定["啟用忽略掃描路徑"] else [],
                設定["掃描空資料夾"]
            ),
            daemon=True
        ).start()

    def 取消目前作業(self):
        if self.掃描中:
            self.取消掃描中 = True
            self.狀態標籤.config(text="正在取消掃描...", foreground="orange")
            self.進度文字標籤.config(text="正在取消掃描，請稍候...")
        elif self.刪除進行中:
            self.取消刪除中 = True
            self.狀態標籤.config(text="正在取消刪除，已移到回收桶的項目不會還原", foreground="orange")

    def 掃描執行(self, 路徑列表, 掃描模式, 忽略路徑列表, 是否掃描空資料夾):
        """背景執行掃描，避免大量檔案掃描時卡住 Tk UI 執行緒。"""
        try:
            def 掃描進度回呼(目前, 總數, 目前檔案):
                if self.取消掃描中:
                    return

                百分比 = (目前 / 總數) * 100 if 總數 else 100
                self.after(0, self.更新掃描進度, 目前, 總數, 百分比, 目前檔案)

            所有重複 = 找出重複檔案(
                路徑列表,
                進度回呼=掃描進度回呼,
                是否取消=lambda: self.取消掃描中,
                掃描模式=掃描模式,
                忽略路徑列表=忽略路徑列表
            )

            if 所有重複 is None:
                self.after(0, self.掃描已取消)
                return

            空資料夾列表 = []
            if 是否掃描空資料夾:
                空資料夾列表 = 找出空資料夾(
                    路徑列表,
                    是否取消=lambda: self.取消掃描中,
                    忽略路徑列表=忽略路徑列表
                )
                if 空資料夾列表 is None:
                    self.after(0, self.掃描已取消)
                    return

            self.最後掃描結果 = 所有重複
            self.最後空資料夾結果 = 空資料夾列表
            self.after(0, self.顯示結果, 所有重複, 空資料夾列表)

        except Exception as e:
            self.after(0, self.顯示錯誤, str(e))
    def 更新掃描進度(self, 目前, 總數, 百分比, 目前檔案):
        self.進度條["value"] = 百分比
        檔名 = os.path.basename(目前檔案) if 目前檔案 else ""
        self.進度文字標籤.config(
            text=f"掃描進度：{目前}/{總數}（{百分比:.1f}%）  目前檔案：{檔名}"
        )
        self.狀態標籤.config(
            text=f"掃描中：{目前}/{總數}（{百分比:.1f}%）",
            foreground="blue"
        )

    def 掃描已取消(self):
        self.掃描中 = False
        self.取消掃描中 = False
        self.設定按鈕狀態(True)
        self.取消按鈕.config(state="disabled")
        self.進度條["value"] = 0
        self.狀態標籤.config(text="掃描已取消", foreground="orange")
        self.進度文字標籤.config(text="掃描已取消")
        self.更新結果摘要()
        self.更新勾選摘要()
    def 顯示結果(self, 重複組, 空資料夾列表=None):
        """把核心掃描結果轉成 Treeview 群組與可勾選項目。"""
        self.掃描結束()
        空資料夾列表 = 空資料夾列表 or []

        if not 重複組 and not 空資料夾列表:
            self.狀態標籤.config(text="沒有發現重複檔案", foreground="green")
            self.結果摘要標籤.config(text="本次掃描沒有發現重複檔案")
            self.進度條["value"] = 100
            self.進度文字標籤.config(text="掃描完成：沒有發現重複檔案")
            self.更新結果摘要()
            return

        總可刪除數 = 0

        for 索引, 路徑列表 in enumerate(重複組, start=1):
            總可刪除數 += self.插入結果群組(索引, 路徑列表)

        if 空資料夾列表:
            總可刪除數 += self.插入空資料夾群組(空資料夾列表)

        self.狀態標籤.config(
            text=f"找到 {len(重複組)} 組重複、{len(空資料夾列表)} 個空資料夾，共 {總可刪除數} 個可處理項目",
            foreground="black"
        )
        self.結果摘要標籤.config(
            text=f"掃描完成：{len(重複組)} 組重複，{len(空資料夾列表)} 個空資料夾，{總可刪除數} 個可處理項目"
        )
        self.進度條["value"] = 100
        self.進度文字標籤.config(text="掃描完成")
        self.儲存掃描結果(重複組)
        self.更新結果摘要()
        self.更新勾選摘要()
        self.掃描完成自動匯出Excel()

    def 掃描結束(self):
        self.掃描中 = False
        self.取消掃描中 = False
        self.取消刪除中 = False
        self.設定按鈕狀態(True)
        self.取消按鈕.config(state="disabled")

    def 顯示錯誤(self, 錯誤訊息):
        self.掃描結束()
        self.狀態標籤.config(text="掃描失敗", foreground="red")
        self.結果摘要標籤.config(text="掃描失敗，請檢查錯誤訊息")
        self.進度文字標籤.config(text="掃描失敗")
        messagebox.showerror("錯誤", 錯誤訊息)

    def 設定按鈕狀態(self, 啟用):
        狀態 = "normal" if 啟用 else "disabled"
        self.開始掃描按鈕.config(state=狀態)
        self.開啟結果按鈕.config(state=狀態)
        self.預覽按鈕.config(state=狀態)
        self.匯出按鈕.config(state=狀態)
        self.刪除按鈕.config(state=狀態)
        self.全部勾選按鈕.config(state=狀態)
        self.全部取消按鈕.config(state=狀態)

    # =========================
    # 儲存 / 開啟結果
    # =========================
    def 儲存掃描結果(self, 重複組):
        """儲存最近一次掃描結果，讓下次開啟可以還原群組顯示。"""
        掃描結果 = {
            "version": 2,
            "groups": [
                [os.path.normpath(os.path.abspath(路徑)) for 路徑 in 組]
                for 組 in 重複組
                if len(組) > 1
            ],
            "empty_folders": [
                os.path.normpath(os.path.abspath(路徑))
                for 路徑 in self.最後空資料夾結果
            ]
        }

        with open("last_scan_result.json", "w", encoding="utf-8") as f:
            json.dump(掃描結果, f, ensure_ascii=False, indent=4)

    def 開啟上次結果(self):
        if not os.path.exists("last_scan_result.json"):
            messagebox.showinfo("提示", "沒有上一次的掃描結果")
            return

        try:
            with open("last_scan_result.json", "r", encoding="utf-8") as f:
                掃描結果資料 = json.load(f)
        except Exception as e:
            messagebox.showerror("錯誤", f"讀取上次結果失敗：{e}")
            return

        重複組 = self.解析上次掃描結果(掃描結果資料)
        空資料夾列表 = self.解析上次空資料夾結果(掃描結果資料)

        if not 重複組 and not 空資料夾列表:
            messagebox.showinfo("提示", "上一次掃描結果為空")
            return

        self.清空列表()

        載入數量 = 0
        for 索引, 路徑列表 in enumerate(重複組, start=1):
            載入數量 += self.插入結果群組(索引, 路徑列表)
        if 空資料夾列表:
            載入數量 += self.插入空資料夾群組(空資料夾列表)

        self.清空預覽()
        self.進度條["value"] = 0
        self.進度文字標籤.config(text="已載入上次結果")
        self.狀態標籤.config(text=f"已載入上次掃描結果，共 {載入數量} 個可處理項目", foreground="black")
        self.結果摘要標籤.config(text=f"已載入上次掃描結果：{載入數量} 個可處理項目")
        self.更新結果摘要()
        self.更新勾選摘要()

    def 解析上次掃描結果(self, 掃描結果資料):
        if isinstance(掃描結果資料, dict):
            groups = 掃描結果資料.get("groups", [])
            return [
                [os.path.normpath(os.path.abspath(路徑)) for 路徑 in group if 路徑]
                for group in groups
                if isinstance(group, list) and len(group) > 1
            ]

        if isinstance(掃描結果資料, list):
            return [[os.path.normpath(os.path.abspath(路徑)) for 路徑 in 掃描結果資料 if 路徑]]

        return []

    def 解析上次空資料夾結果(self, 掃描結果資料):
        if isinstance(掃描結果資料, dict):
            return [
                os.path.normpath(os.path.abspath(路徑))
                for 路徑 in 掃描結果資料.get("empty_folders", [])
                if 路徑
            ]
        return []

    def 插入結果群組(self, 索引, 路徑列表):
        """新增一組重複檔案；每組第 1 個預設作為保留項目。"""
        允許勾選保留項目 = self.取得設定()["允許勾選保留項目"]
        父項目 = self.tree.insert(
            "",
            "end",
            text=f"群組 {索引}",
            open=True,
            values=("", "", "", "第 1 個為預設保留項目", "")
        )

        插入數量 = 0
        for 項目索引, 路徑 in enumerate(路徑列表):
            正規路徑 = os.path.normpath(os.path.abspath(路徑))
            if not os.path.exists(正規路徑):
                continue

            檔名 = os.path.basename(正規路徑)
            大小 = self.取得檔案大小MB(正規路徑)
            類型 = self.取得檔案類型(正規路徑)
            是保留項目 = 項目索引 == 0
            勾選文字 = "☐" if (not 是保留項目 or 允許勾選保留項目) else "保留"

            子項目 = self.tree.insert(
                父項目,
                "end",
                values=(勾選文字, 類型, 檔名, 正規路徑, f"{大小:.2f}")
            )

            self.項目路徑對照[子項目] = 正規路徑
            if 是保留項目:
                self.保留項目集合.add(子項目)
                if not 允許勾選保留項目:
                    self.不可勾選項目.add(子項目)
            插入數量 += 1

        可處理數量 = 插入數量 if 允許勾選保留項目 else max(插入數量 - 1, 0)

        if 插入數量 < 2 and self.tree.exists(父項目):
            self.tree.delete(父項目)
            for 項目 in list(self.不可勾選項目):
                if not self.tree.exists(項目):
                    self.不可勾選項目.discard(項目)
            for 項目 in list(self.保留項目集合):
                if not self.tree.exists(項目):
                    self.保留項目集合.discard(項目)
            return 0

        return 可處理數量

    def 插入空資料夾群組(self, 空資料夾列表):
        """把掃描到的空資料夾放在同一個群組中，供使用者勾選刪除。"""
        父項目 = self.tree.insert(
            "",
            "end",
            text="空資料夾",
            open=True,
            values=("", "", "", "以下是掃描到的空資料夾", "")
        )

        插入數量 = 0
        for 路徑 in 空資料夾列表:
            正規路徑 = os.path.normpath(os.path.abspath(路徑))
            if not os.path.isdir(正規路徑):
                continue

            子項目 = self.tree.insert(
                父項目,
                "end",
                values=("☐", "資料夾", os.path.basename(正規路徑), 正規路徑, "0.00")
            )

            self.項目路徑對照[子項目] = 正規路徑
            self.空資料夾項目集合.add(子項目)
            插入數量 += 1

        if 插入數量 == 0 and self.tree.exists(父項目):
            self.tree.delete(父項目)

        return 插入數量

    # =========================
    # Treeview 操作
    # =========================
    def 點擊樹狀表格(self, event):
        區域 = self.tree.identify("region", event.x, event.y)
        欄位 = self.tree.identify_column(event.x)
        項目 = self.tree.identify_row(event.y)

        if not 項目:
            return

        if 區域 == "cell" and 欄位 == "#1":
            if 項目 in self.項目路徑對照:
                if 項目 in self.不可勾選項目:
                    messagebox.showinfo(
                        "保留項目不可勾選",
                        "此項目是每組第 1 個預設保留檔案。\n如需勾選，請到設定開啟「允許勾選每組第 1 個檔案」。"
                    )
                    return "break"
                self.切換勾選狀態(項目)
                return "break"

    def 套用保留項目設定(self, 允許勾選保留項目=None):
        if 允許勾選保留項目 is None:
            允許勾選保留項目 = self.取得設定()["允許勾選保留項目"]

        for 項目 in list(self.保留項目集合):
            if not self.tree.exists(項目):
                self.保留項目集合.discard(項目)
                self.不可勾選項目.discard(項目)
                continue

            值 = list(self.tree.item(項目, "values"))
            if not 值:
                continue

            if 允許勾選保留項目:
                self.不可勾選項目.discard(項目)
                if 值[0] == "保留":
                    值[0] = "☐"
                    self.tree.item(項目, values=值)
            else:
                self.不可勾選項目.add(項目)
                值[0] = "保留"
                self.tree.item(項目, values=值)

        self.更新勾選摘要()

    def 切換勾選狀態(self, 項目):
        值 = list(self.tree.item(項目, "values"))
        if not 值:
            return
        值[0] = "☑" if 值[0] == "☐" else "☐"
        self.tree.item(項目, values=值)
        self.更新勾選摘要()

    def 全部勾選(self):
        for 項目 in list(self.項目路徑對照.keys()):
            if 項目 in self.不可勾選項目:
                continue
            值 = list(self.tree.item(項目, "values"))
            if 值:
                值[0] = "☑"
                self.tree.item(項目, values=值)
        self.更新勾選摘要()

    def 全部取消勾選(self):
        for 項目 in list(self.項目路徑對照.keys()):
            值 = list(self.tree.item(項目, "values"))
            if 值:
                值[0] = "☐"
                self.tree.item(項目, values=值)
        self.更新勾選摘要()

    def 取得已勾選項目(self):
        已勾選 = []
        for 項目, 路徑 in self.項目路徑對照.items():
            值 = self.tree.item(項目, "values")
            if 值 and 值[0] == "☑":
                已勾選.append((項目, 路徑))
        return 已勾選

    # =========================
    # 預覽
    # =========================
    def 更新右側預覽(self, event=None):
        """依副檔名選擇圖片、影片、文字或摘要預覽。"""
        選中項目 = self.tree.selection()
        if not 選中項目:
            return

        項目ID = 選中項目[0]
        路徑 = self.項目路徑對照.get(項目ID)

        if not 路徑 or not os.path.exists(路徑):
            self.清空預覽()
            return

        副檔名 = os.path.splitext(路徑)[1].lower()
        檔名 = os.path.basename(路徑)
        大小 = self.取得檔案大小MB(路徑)
        類型 = self.取得檔案類型(路徑)
        self.預覽標題標籤.config(text=檔名)
        self.預覽類型標籤.config(text=f"{類型}  |  {大小:.2f} MB")
        self.停止影片播放()

        if 副檔名 in 圖片副檔名集合:
            try:
                圖片 = Image.open(路徑)
                原始寬, 原始高 = 圖片.size
                預覽寬 = max(220, self.預覽內容框架.winfo_width() - 24)
                預覽高 = max(180, self.預覽內容框架.winfo_height() - 24)
                圖片.thumbnail((預覽寬, 預覽高))
                self.預覽圖片物件 = ImageTk.PhotoImage(圖片)

                self.顯示圖片預覽()
                self.預覽圖片標籤.config(image=self.預覽圖片物件, text="")
                self.設定預覽資訊(self.取得檔案資訊文字(路徑, 類型, f"影像尺寸：{原始寬} x {原始高}"))
            except Exception as e:
                self.顯示圖片預覽()
                self.預覽圖片標籤.config(image="", text="無法預覽此圖片")
                self.設定預覽資訊(self.取得檔案資訊文字(路徑, 類型, f"錯誤：{e}"))
                self.預覽圖片物件 = None

        elif self.可文字預覽(路徑):
            內容, 訊息 = self.讀取文字預覽(路徑)
            self.顯示文字預覽(內容)
            self.設定預覽資訊(self.取得檔案資訊文字(路徑, 類型, 訊息))
            self.預覽圖片物件 = None

        elif 副檔名 in 影片副檔名集合:
            self.顯示影片預覽()
            訊息 = self.載入影片預覽(路徑)
            self.設定預覽資訊(self.取得檔案資訊文字(路徑, 類型, 訊息))

        elif 副檔名 in 文件副檔名集合:
            self.顯示圖片預覽()
            self.預覽圖片標籤.config(image="", text=f"{類型} 文件\n可外部開啟檢視完整內容")
            self.設定預覽資訊(self.取得檔案資訊文字(路徑, 類型, "此格式目前提供檔案摘要。"))
            self.預覽圖片物件 = None

        else:
            self.顯示圖片預覽()
            self.預覽圖片標籤.config(image="", text="檔案摘要\n可使用外部開啟查看內容")
            self.設定預覽資訊(self.取得檔案資訊文字(路徑, 類型, "此類型不適合直接內嵌預覽。"))
            self.預覽圖片物件 = None

    def 清空預覽(self):
        self.停止影片播放()
        self.預覽標題標籤.config(text="請在左側選擇檔案")
        self.預覽類型標籤.config(text="未選擇")
        self.顯示圖片預覽()
        self.預覽圖片標籤.config(image="", text="尚未選擇檔案")
        self.設定預覽資訊("類型：\n檔名：\n路徑：\n大小：")
        self.預覽圖片物件 = None

    def 顯示圖片預覽(self):
        self.預覽影片框架.pack_forget()
        self.預覽文字框架.pack_forget()
        if not self.預覽圖片標籤.winfo_ismapped():
            self.預覽圖片標籤.pack(fill="both", expand=True)
        self.預覽文字.config(state="normal")
        self.預覽文字.delete("1.0", "end")
        self.預覽文字.config(state="disabled")

    def 顯示文字預覽(self, 內容):
        self.預覽影片框架.pack_forget()
        self.預覽圖片標籤.pack_forget()
        self.預覽圖片標籤.config(image="", text="")
        if not self.預覽文字框架.winfo_ismapped():
            self.預覽文字框架.pack(fill="both", expand=True)

        self.預覽文字.config(state="normal")
        self.預覽文字.delete("1.0", "end")
        self.預覽文字.insert("1.0", 內容)
        self.預覽文字.config(state="disabled")

    def 顯示影片預覽(self):
        self.預覽圖片標籤.pack_forget()
        self.預覽文字框架.pack_forget()
        self.預覽圖片標籤.config(image="", text="")
        self.預覽影片畫面.config(image="", text="正在載入影片...")
        self.預覽文字.config(state="normal")
        self.預覽文字.delete("1.0", "end")
        self.預覽文字.config(state="disabled")
        if not self.預覽影片框架.winfo_ismapped():
            self.預覽影片框架.pack(fill="both", expand=True)

    def 載入影片預覽(self, 路徑):
        self.目前影片路徑 = 路徑
        self.重設影片進度()
        try:
            import cv2
        except ImportError:
            self.預覽影片畫面.config(
                image="",
                text="影片預覽需要安裝 opencv-python\n可先使用「外部開啟」播放"
            )
            self.預覽圖片物件 = None
            return "內嵌播放需要 opencv-python；目前可外部開啟播放。"

        self.影片擷取器 = cv2.VideoCapture(路徑)
        if not self.影片擷取器.isOpened():
            self.預覽影片畫面.config(image="", text="無法載入此影片\n可嘗試使用「外部開啟」")
            self.預覽圖片物件 = None
            return "無法載入影片預覽。"

        fps = self.影片擷取器.get(cv2.CAP_PROP_FPS)
        self.影片FPS = fps if fps and fps > 1 else 25
        self.影片總影格 = int(self.影片擷取器.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        寬 = int(self.影片擷取器.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        高 = int(self.影片擷取器.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        秒數 = self.影片總影格 / self.影片FPS if self.影片總影格 else 0

        self.影片進度滑桿.configure(to=max(0, self.影片總影格 - 1))
        self.更新影片時間標籤(0)

        self.顯示下一個影片影格()
        return f"影片尺寸：{寬} x {高}\n影片長度：約 {秒數:.1f} 秒\n可在預覽區播放、暫停或停止。"

    def 播放影片(self):
        if not self.影片擷取器 and self.目前影片路徑:
            self.載入影片預覽(self.目前影片路徑)
        if not self.影片擷取器:
            return

        self.影片播放中 = True
        if self.影片播放工作:
            try:
                self.after_cancel(self.影片播放工作)
            except Exception:
                pass
            self.影片播放工作 = None
        self.排程影片播放()

    def 暫停影片(self):
        self.影片播放中 = False

    def 停止影片播放(self):
        self.影片播放中 = False
        if self.影片播放工作:
            try:
                self.after_cancel(self.影片播放工作)
            except Exception:
                pass
            self.影片播放工作 = None

        if self.影片擷取器:
            try:
                self.影片擷取器.release()
            except Exception:
                pass
            self.影片擷取器 = None
        self.重設影片進度()

    def 排程影片播放(self):
        if not self.影片播放中 or not self.影片擷取器:
            return

        還有影格 = self.顯示下一個影片影格()
        if not 還有影格:
            self.影片播放中 = False
            return

        延遲 = max(10, int(1000 / self.影片FPS))
        self.影片播放工作 = self.after(延遲, self.排程影片播放)

    def 顯示下一個影片影格(self):
        if not self.影片擷取器:
            return False

        try:
            import cv2
            成功, 影格 = self.影片擷取器.read()
            if not 成功:
                return False

            目前影格 = int(self.影片擷取器.get(cv2.CAP_PROP_POS_FRAMES) or 0)
            self.更新影片進度(目前影格)
            影格 = cv2.cvtColor(影格, cv2.COLOR_BGR2RGB)
            圖片 = Image.fromarray(影格)
            預覽寬 = max(220, self.預覽影片畫面.winfo_width() - 12)
            預覽高 = max(180, self.預覽影片畫面.winfo_height() - 12)
            圖片.thumbnail((預覽寬, 預覽高))
            self.預覽圖片物件 = ImageTk.PhotoImage(圖片)
            self.預覽影片畫面.config(image=self.預覽圖片物件, text="")
            return True
        except Exception as e:
            self.預覽影片畫面.config(image="", text=f"影片播放失敗：{e}")
            self.預覽圖片物件 = None
            return False

    def 開始拖曳影片進度(self, event=None):
        self.拖曳前影片播放中 = self.影片播放中
        self.影片進度拖曳中 = True
        self.暫停影片()

    def 拖曳影片進度(self, value):
        if not self.影片進度拖曳中:
            return

        self.更新影片時間標籤(float(value))

    def 完成拖曳影片進度(self, event=None):
        if not self.影片擷取器:
            self.影片進度拖曳中 = False
            return

        目標影格 = int(float(self.影片進度變數.get()))
        self.影片進度拖曳中 = False
        self.跳到影片影格(目標影格)
        if self.拖曳前影片播放中:
            self.播放影片()
        self.拖曳前影片播放中 = False

    def 跳到影片影格(self, 影格位置):
        if not self.影片擷取器:
            return

        try:
            import cv2
            影格位置 = max(0, min(int(影格位置), max(0, self.影片總影格 - 1)))
            self.影片擷取器.set(cv2.CAP_PROP_POS_FRAMES, 影格位置)
            self.顯示下一個影片影格()
        except Exception as e:
            self.預覽影片畫面.config(image="", text=f"無法跳轉影片進度：{e}")

    def 更新影片進度(self, 目前影格):
        if self.影片進度拖曳中:
            return

        顯示影格 = max(0, 目前影格 - 1)
        self.影片進度變數.set(顯示影格)
        self.更新影片時間標籤(顯示影格)

    def 更新影片時間標籤(self, 影格位置):
        目前秒數 = float(影格位置) / self.影片FPS if self.影片FPS else 0
        總秒數 = self.影片總影格 / self.影片FPS if self.影片FPS and self.影片總影格 else 0
        self.影片時間標籤.config(text=f"{self.格式化影片時間(目前秒數)} / {self.格式化影片時間(總秒數)}")

    def 格式化影片時間(self, 秒數):
        秒數 = max(0, int(秒數))
        分鐘, 秒 = divmod(秒數, 60)
        小時, 分鐘 = divmod(分鐘, 60)
        if 小時:
            return f"{小時:02d}:{分鐘:02d}:{秒:02d}"
        return f"{分鐘:02d}:{秒:02d}"

    def 重設影片進度(self):
        self.影片總影格 = 0
        self.影片進度拖曳中 = False
        self.拖曳前影片播放中 = False
        self.影片進度滑桿.configure(to=0)
        self.影片進度變數.set(0)
        self.影片時間標籤.config(text="00:00 / 00:00")

    def 設定預覽資訊(self, 文字):
        self.預覽資訊文字.config(state="normal")
        self.預覽資訊文字.delete("1.0", "end")
        self.預覽資訊文字.insert("1.0", 文字)
        self.預覽資訊文字.config(state="disabled")

    def 可文字預覽(self, 路徑):
        副檔名 = os.path.splitext(路徑)[1].lower()
        if 副檔名 in 文字副檔名集合:
            return True

        mime, _ = mimetypes.guess_type(路徑)
        return bool(mime and mime.startswith("text/"))

    def 讀取文字預覽(self, 路徑, 最大位元組=256 * 1024):
        try:
            檔案大小 = os.path.getsize(路徑)
            with open(路徑, "rb") as f:
                原始內容 = f.read(最大位元組)

            for 編碼 in ("utf-8-sig", "utf-8", "cp950", "big5", "latin-1"):
                try:
                    內容 = 原始內容.decode(編碼)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                內容 = 原始內容.decode("utf-8", errors="replace")

            if 檔案大小 > 最大位元組:
                內容 += "\n\n... 內容過大，僅顯示前 256 KB ..."

            return 內容, "文字預覽：顯示檔案前段內容。"
        except Exception as e:
            return f"無法讀取文字預覽：{e}", f"錯誤：{e}"

    def 取得檔案資訊文字(self, 路徑, 類型, 補充=""):
        try:
            大小 = self.取得檔案大小MB(路徑)
            修改時間 = os.path.getmtime(路徑)
            修改時間文字 = self.tk.call("clock", "format", int(修改時間), "-format", "%Y-%m-%d %H:%M:%S")
        except Exception:
            大小 = 0.0
            修改時間文字 = "無法讀取"

        mime, _ = mimetypes.guess_type(路徑)
        mime = mime or "未知"
        資訊 = [
            f"類型：{類型}",
            f"MIME：{mime}",
            f"大小：{大小:.2f} MB",
            f"修改時間：{修改時間文字}",
            f"路徑：{路徑}"
        ]
        if 補充:
            資訊.append(補充)
        return "\n".join(資訊)

    def 即時預覽(self):
        選中項目 = self.tree.selection()
        if not 選中項目:
            messagebox.showinfo("提示", "請先點選要開啟的檔案")
            return

        項目ID = 選中項目[0]
        路徑 = self.項目路徑對照.get(項目ID)

        if not 路徑:
            messagebox.showinfo("提示", "請選擇實際檔案項目，而不是群組標題")
            return

        if not os.path.exists(路徑):
            messagebox.showerror("錯誤", "檔案不存在")
            return

        try:
            if platform.system() == "Windows":
                os.startfile(路徑)
            elif platform.system() == "Darwin":
                subprocess.call(["open", 路徑])
            else:
                subprocess.call(["xdg-open", 路徑])
        except Exception as e:
            messagebox.showerror("錯誤", f"無法開啟檔案：{e}")

    # =========================
    # 刪除
    # =========================
    def 刪除已勾選檔案(self):
        if self.掃描中 or self.刪除進行中:
            return

        if not self.取得設定()["允許刪除重複檔案"]:
            messagebox.showinfo("提示", "刪除功能目前關閉，請先在左側設定啟用「允許移到回收桶」")
            return

        已勾選 = self.取得已勾選項目()

        if not 已勾選:
            messagebox.showinfo("提示", "請先勾選要移到回收桶的檔案")
            return

        已勾選保留項目 = [
            路徑
            for 項目ID, 路徑 in 已勾選
            if 項目ID in self.保留項目集合
        ]

        if 已勾選保留項目:
            確認保留項目 = messagebox.askyesno(
                "包含每組第 1 個檔案",
                f"你勾選了 {len(已勾選保留項目)} 個每組第 1 個預設保留檔案。\n\n"
                "這些檔案原本是系統建議保留的項目。確定要繼續移到回收桶嗎？"
            )
            if not 確認保留項目:
                return

        確認 = messagebox.askyesno(
            "確認移到回收桶",
            f"共勾選 {len(已勾選)} 個檔案。\n\n確定要移到回收桶嗎？"
        )
        if not 確認:
            return

        self.刪除進行中 = True
        self.取消刪除中 = False
        self.設定按鈕狀態(False)
        self.取消按鈕.config(state="normal")
        self.進度條["value"] = 0
        快速刪除模式 = self.取得設定()["快速刪除模式"]
        if 快速刪除模式:
            self.進度文字標籤.config(text="正在快速刪除中，完成後會一次更新列表...")
            self.狀態標籤.config(text="快速刪除中，請稍候...", foreground="blue")
        else:
            self.進度文字標籤.config(text="準備開始刪除...")
            self.狀態標籤.config(text="刪除中，請稍候...", foreground="blue")

        threading.Thread(target=self.刪除執行, args=(已勾選, 快速刪除模式), daemon=True).start()

    def 刪除執行(self, 已勾選, 快速刪除模式=False):
        """背景執行移到回收桶。

        一般模式會批次刪除但逐步更新列表；快速模式會一次送出所有項目，
        完成後再一次更新 UI，適合大量檔案。
        """
        失敗清單 = []
        總數 = len(已勾選)
        有效項目 = []

        try:
            for 項目ID, 路徑 in 已勾選:
                正規路徑 = os.path.normpath(os.path.abspath(路徑))
                if os.path.exists(正規路徑):
                    有效項目.append((項目ID, 正規路徑))
                else:
                    失敗清單.append(f"{路徑}\n原因：找不到檔案")

            if not 有效項目:
                self.after(0, self.刪除完成, 0, 失敗清單)
                return

            if 快速刪除模式:
                self.after(0, self.更新快速刪除狀態, 總數)
                try:
                    send2trash([路徑 for _, 路徑 in 有效項目])
                    self.after(0, self.快速刪除完成更新UI, [項目ID for 項目ID, _ in 有效項目], 失敗清單)
                    return
                except Exception as e:
                    失敗清單.append(f"快速刪除失敗\n原因：{e}")
                    self.after(0, self.刪除完成, 0, 失敗清單)
                    return

            批次大小 = 100
            批次模式成功 = True
            已批次完成項目 = []
            for 起點 in range(0, len(有效項目), 批次大小):
                if self.取消刪除中:
                    break

                批次 = 有效項目[起點:起點 + 批次大小]
                try:
                    self.after(0, self.狀態標籤.config, {"text": f"批次移到回收桶中：{起點}/{總數}", "foreground": "blue"})
                    send2trash([路徑 for _, 路徑 in 批次])
                    已批次完成項目.extend([項目ID for 項目ID, _ in 批次])
                except Exception:
                    批次模式成功 = False
                    break

            if 批次模式成功:
                if self.取消刪除中:
                    失敗清單.append("使用者取消刪除，尚未處理的項目已保留。")
                self.after(0, self.逐筆移除刪除項目UI, 已批次完成項目, 0, 總數, len(失敗清單), 失敗清單)
                return

            成功項目 = list(已批次完成項目)
            已批次完成集合 = set(已批次完成項目)
            待逐筆處理項目 = [
                (項目ID, 正規路徑)
                for 項目ID, 正規路徑 in 有效項目
                if 項目ID not in 已批次完成集合
            ]

            for 項目ID, 正規路徑 in 待逐筆處理項目:
                if self.取消刪除中:
                    失敗清單.append("使用者取消刪除，尚未處理的項目已保留。")
                    break

                try:
                    send2trash(正規路徑)
                    成功項目.append(項目ID)
                    已處理 = len(失敗清單) + len(成功項目)
                    百分比 = (已處理 / 總數) * 100
                    self.after(0, self.刪除單筆完成更新UI, 項目ID, 已處理, 總數, 百分比)

                except Exception as e:
                    失敗清單.append(f"{正規路徑}\n原因：{e}")

        except Exception as e:
            失敗清單.append(f"刪除流程中斷\n原因：{e}")
        finally:
            if '成功項目' in locals():
                self.after(0, self.刪除完成, len(成功項目), 失敗清單)

    def 更新刪除進度(self, 目前, 總數, 百分比):
        self.進度條["value"] = 百分比
        self.進度文字標籤.config(text=f"刪除進度：{目前}/{總數}（{百分比:.1f}%）")
        self.狀態標籤.config(text=f"刪除中：{目前}/{總數}（{百分比:.1f}%）", foreground="blue")

    def 更新快速刪除狀態(self, 總數):
        self.進度條["value"] = 0
        self.進度文字標籤.config(text=f"正在快速刪除中：共 {總數} 個項目")
        self.狀態標籤.config(text="快速刪除中，請稍候...", foreground="blue")

    def 刪除單筆完成更新UI(self, 項目ID, 目前, 總數, 百分比):
        self.移除結果項目(項目ID)
        self.更新刪除進度(目前, 總數, 百分比)

    def 快速刪除完成更新UI(self, 項目ID列表, 失敗清單):
        for 項目ID in 項目ID列表:
            self.移除結果項目(項目ID)
        self.進度條["value"] = 100
        self.刪除完成(len(項目ID列表), 失敗清單)

    def 逐筆移除刪除項目UI(self, 項目ID列表, 索引, 總數, 已處理基準, 失敗清單):
        if 索引 >= len(項目ID列表):
            self.刪除完成(len(項目ID列表), 失敗清單)
            return

        項目ID = 項目ID列表[索引]
        self.移除結果項目(項目ID)
        目前 = 已處理基準 + 索引 + 1
        百分比 = (目前 / 總數) * 100 if 總數 else 100
        self.更新刪除進度(目前, 總數, 百分比)
        self.after(1, self.逐筆移除刪除項目UI, 項目ID列表, 索引 + 1, 總數, 已處理基準, 失敗清單)

    def 移除結果項目(self, 項目ID):
        if not self.tree.exists(項目ID):
            return

        父項目 = self.tree.parent(項目ID)
        self.項目路徑對照.pop(項目ID, None)
        self.不可勾選項目.discard(項目ID)
        self.保留項目集合.discard(項目ID)
        self.空資料夾項目集合.discard(項目ID)
        self.tree.delete(項目ID)

        if 父項目 and self.tree.exists(父項目) and len(self.tree.get_children(父項目)) == 0:
            self.tree.delete(父項目)

    def 刪除完成(self, 成功數, 失敗清單):
        已取消刪除 = any("使用者取消刪除" in 訊息 for 訊息 in 失敗清單)
        self.刪除進行中 = False
        self.取消刪除中 = False
        self.設定按鈕狀態(True)
        self.取消按鈕.config(state="disabled")
        self.清空預覽()
        self.更新結果摘要()
        self.更新勾選摘要()

        if 已取消刪除:
            self.狀態標籤.config(text=f"刪除已取消，成功 {成功數} 個", foreground="orange")
            self.進度文字標籤.config(text=f"刪除已取消：成功 {成功數} 個，尚未處理的項目已保留")
            messagebox.showinfo(
                "刪除已取消",
                f"已停止後續刪除。\n已成功移到回收桶 {成功數} 個項目，尚未處理的項目已保留。"
            )
        elif 失敗清單:
            self.狀態標籤.config(text=f"刪除完成，成功 {成功數} 個，部分失敗", foreground="orange")
            self.進度文字標籤.config(text=f"刪除完成：成功 {成功數} 個，部分失敗")
            messagebox.showwarning(
                "部分處理失敗",
                f"成功移到回收桶 {成功數} 個檔案。\n\n以下檔案處理失敗：\n\n" + "\n\n".join(失敗清單[:5])
            )
        else:
            self.狀態標籤.config(text=f"刪除完成，成功 {成功數} 個", foreground="green")
            self.進度文字標籤.config(text=f"刪除完成：成功 {成功數} 個")
            messagebox.showinfo("完成", f"已成功移到回收桶 {成功數} 個檔案")

    # =========================
    # 匯出
    # =========================
    def 匯出Excel(self):
        if not self.最後掃描結果:
            messagebox.showinfo("提示", "沒有掃描結果可匯出，請先執行「開始掃描」")
            return

        try:
            輸出路徑 = self.取得Excel輸出路徑()
            輸出Excel(self.最後掃描結果, 輸出路徑, 自動開啟=True)
            messagebox.showinfo("成功", f"Excel 已輸出並自動開啟：\n{輸出路徑}")
        except Exception as e:
            messagebox.showerror("錯誤", f"匯出失敗：{e}")

    def 掃描完成自動匯出Excel(self):
        設定 = self.取得設定()
        if not 設定["Excel掃描後自動匯出"] or not self.最後掃描結果:
            return

        try:
            輸出路徑 = self.取得Excel輸出路徑()
            輸出Excel(self.最後掃描結果, 輸出路徑, 自動開啟=False)
            self.狀態標籤.config(text=f"掃描完成，Excel 已自動匯出：{輸出路徑}", foreground="green")
        except Exception as e:
            self.狀態標籤.config(text="掃描完成，但 Excel 自動匯出失敗", foreground="orange")
            messagebox.showwarning("Excel 自動匯出失敗", str(e))

    def 取得Excel輸出路徑(self):
        設定 = self.取得設定()
        輸出資料夾 = 設定["Excel輸出資料夾"].strip() or os.getcwd()
        輸出資料夾 = os.path.normpath(os.path.abspath(輸出資料夾))

        if not os.path.isdir(輸出資料夾):
            raise FileNotFoundError(f"Excel 輸出資料夾不存在：{輸出資料夾}")

        if 設定["Excel自動命名"]:
            時間文字 = datetime.now().strftime("%Y%m%d_%H%M%S")
            檔名 = f"重複檔案_{時間文字}.xlsx"
        else:
            檔名 = 設定["Excel輸出檔名"].strip() or "重複檔案.xlsx"
            if not 檔名.lower().endswith(".xlsx"):
                檔名 += ".xlsx"

        return os.path.join(輸出資料夾, 檔名)

    # =========================
    # 輔助
    # =========================
    def 取得檔案類型(self, 路徑):
        if os.path.isdir(路徑):
            return "資料夾"

        副檔名 = os.path.splitext(路徑)[1].lower()

        if 副檔名 in 圖片副檔名集合:
            return "圖片"
        elif 副檔名 in 影片副檔名集合:
            return "影片"
        elif 副檔名 in 文字副檔名集合:
            return "文字"
        elif 副檔名 == ".pdf":
            return "PDF"
        elif 副檔名 in {".doc", ".docx", ".odt"}:
            return "文件"
        elif 副檔名 in {".xls", ".xlsx", ".ods"}:
            return "試算表"
        elif 副檔名 in {".ppt", ".pptx", ".odp"}:
            return "簡報"
        elif 副檔名 in {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"}:
            return "壓縮檔"
        elif 副檔名 in {".mp3", ".wav", ".flac", ".aac", ".m4a", ".ogg", ".wma"}:
            return "音訊"
        elif 副檔名:
            return 副檔名.replace(".", "").upper()
        else:
            return "無副檔名"

    def 取得檔案大小MB(self, 路徑):
        try:
            if os.path.isdir(路徑):
                return 0.0
            return round(os.path.getsize(路徑) / 1024 / 1024, 2)
        except Exception:
            return 0.0

    def 更新勾選摘要(self):
        已勾選數量 = 0
        已勾選總大小 = 0.0

        for 項目, 路徑 in self.項目路徑對照.items():
            值 = self.tree.item(項目, "values")
            if 值 and 值[0] == "☑":
                已勾選數量 += 1
                if os.path.exists(路徑):
                    已勾選總大小 += self.取得檔案大小MB(路徑)

        self.勾選摘要標籤.config(
            text=f"已勾選 {已勾選數量} 個項目，總大小 {已勾選總大小:.2f} MB"
        )

    def 清空列表(self):
        for 項目 in self.tree.get_children():
            self.tree.delete(項目)

        self.項目路徑對照.clear()
        self.不可勾選項目.clear()
        self.保留項目集合.clear()
        self.空資料夾項目集合.clear()
        self.結果摘要標籤.config(text="尚未開始掃描")
        self.勾選摘要標籤.config(text="已勾選 0 個項目，總大小 0.00 MB")
        self.清空預覽()

    def 更新結果摘要(self):
        群組數 = 0
        檔案數 = 0
        總大小MB = 0.0

        for 項目 in self.tree.get_children():
            子項目列表 = self.tree.get_children(項目)
            if 子項目列表:
                群組數 += 1

            for 子項目 in 子項目列表:
                檔案數 += 1
                路徑 = self.項目路徑對照.get(子項目)
                if 路徑 and os.path.exists(路徑):
                    總大小MB += self.取得檔案大小MB(路徑)

        if 群組數 == 0 and 檔案數 == 0:
            self.結果摘要標籤.config(text="目前沒有結果項目")
            self.狀態標籤.config(text="列表已更新", foreground="black")
        else:
            self.結果摘要標籤.config(
                text=f"目前剩餘 {群組數} 組，{檔案數} 個項目，總大小 {總大小MB:.2f} MB"
            )
            self.狀態標籤.config(
                text=f"目前剩餘 {群組數} 組，{檔案數} 個可處理檔案",
                foreground="black"
            )

        self.更新勾選摘要()
