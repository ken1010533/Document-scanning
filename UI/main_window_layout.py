"""主頁面版面建立與預覽區元件配置。

這個模組從 main_window.py 拆出來，讓主視窗檔案維持薄而好讀。
方法仍以 mixin 形式操作主頁面的 self 狀態，避免重寫既有事件流程。
"""

import tkinter as tk
from tkinter import ttk


class 主頁面版面Mixin:
    """主頁面版面建立與預覽區元件配置。"""

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


    def 更新自適應尺寸(self, event=None):
        寬度 = max(self.winfo_width(), 320)
        預覽換行寬度 = max(220, min(520, int(寬度 * 0.32)))
        self.預覽標題標籤.configure(wraplength=預覽換行寬度)





