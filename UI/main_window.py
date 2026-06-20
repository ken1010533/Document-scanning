"""主視窗與主要互動流程。

這個檔案負責把路徑管理、掃描結果、預覽、匯出與刪除流程串起來。
較獨立的設定頁、檔案類型常數與視窗工具已拆到其他 UI 模組。
"""

import tkinter as tk
from tkinter import ttk
import os

from UI.settings import 設定分頁
from UI.window_utils import 主視窗至中
from core.config import 讀取設定
from UI.main_window_layout import 主頁面版面Mixin
from UI.main_window_paths import 路徑管理Mixin
from UI.main_window_scan_results import 掃描結果Mixin
from UI.main_window_tree import 結果樹狀表格Mixin
from UI.main_window_preview import 預覽Mixin
from UI.main_window_delete import 刪除Mixin
from UI.main_window_export import 匯出Mixin
from UI.main_window_helpers import 主頁輔助Mixin


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
class 主頁面區域(
    主頁面版面Mixin,
    路徑管理Mixin,
    掃描結果Mixin,
    結果樹狀表格Mixin,
    預覽Mixin,
    刪除Mixin,
    匯出Mixin,
    主頁輔助Mixin,
    ttk.Frame
):
    """主操作區：管理路徑、掃描、結果列表、預覽與刪除。"""

    def __init__(self, parent, 路徑父容器=None):
        super().__init__(parent)

        # 父層與路徑頁容器：版面 mixin 會用它決定路徑管理區放在哪裡。
        self.parent = parent
        self.路徑父容器 = 路徑父容器

        # 路徑與掃描結果狀態：多個 mixin 會共同讀寫這些集合。
        self.資料夾路徑列表 = []
        self.路徑框架列表 = []
        self.最後掃描結果 = []
        self.最後空資料夾結果 = []
        self.項目路徑對照 = {}
        self.不可勾選項目 = set()
        self.保留項目集合 = set()
        self.空資料夾項目集合 = set()

        # 背景工作旗標：避免掃描與刪除流程互相踩到 UI 狀態。
        self.掃描中 = False
        self.取消掃描中 = False
        self.刪除進行中 = False
        self.取消刪除中 = False

        # 預覽狀態：圖片物件與影片播放進度必須保留引用，Tk 才能穩定顯示。
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
