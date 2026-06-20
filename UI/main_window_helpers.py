"""檔案類型、大小、摘要與列表清理等共用工具。

這個模組從 main_window.py 拆出來，讓主視窗檔案維持薄而好讀。
方法仍以 mixin 形式操作主頁面的 self 狀態，避免重寫既有事件流程。
"""

import os
from UI.file_types import 圖片副檔名集合, 影片副檔名集合, 文字副檔名集合


class 主頁輔助Mixin:
    """檔案類型、大小、摘要與列表清理等共用工具。"""

    def 取得檔案大小MB(self, 路徑):
        try:
            if os.path.isdir(路徑):
                return 0.0
            return round(os.path.getsize(路徑) / 1024 / 1024, 2)
        except Exception:
            return 0.0



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





