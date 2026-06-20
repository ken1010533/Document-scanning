# UI/help.py
from tkinter import ttk


class 幫助分頁(ttk.Frame):
    def __init__(self, parent, main_app):
        super().__init__(parent)
        self.main_app = main_app  # 儲存主應用程式參考

        ttk.Label(self, text="使用說明", font=("Arial", 14)).pack(pady=10)

        說明 = """
【使用步驟】

1. 新增要掃描的資料夾路徑
2. 點擊「開始掃描」找出重複圖片、影片
3. 勾選要刪除的檔案
4. 點擊「刪除選取的重複檔案」

【注意事項】
- 刪除的檔案無法復原，請謹慎操作
        """

        ttk.Label(self, text=說明, justify="left").pack(padx=20, pady=10)

        # ttk.Button(self, text="返回首頁",
        #            command=lambda: self.main_app.notebook.select(0)).pack(pady=10)