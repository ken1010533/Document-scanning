"""Excel 匯出與輸出路徑產生。

這個模組從 main_window.py 拆出來，讓主視窗檔案維持薄而好讀。
方法仍以 mixin 形式操作主頁面的 self 狀態，避免重寫既有事件流程。
"""

from tkinter import messagebox
import os
from datetime import datetime
from core.excel_export import 輸出Excel


class 匯出Mixin:
    """Excel 匯出與輸出路徑產生。"""

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





