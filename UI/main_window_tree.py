"""Treeview 勾選、保留項目與批次選取行為。

這個模組從 main_window.py 拆出來，讓主視窗檔案維持薄而好讀。
方法仍以 mixin 形式操作主頁面的 self 狀態，避免重寫既有事件流程。
"""

from tkinter import messagebox


class 結果樹狀表格Mixin:
    """Treeview 勾選、保留項目與批次選取行為。"""

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



    def 切換勾選狀態(self, 項目):
        值 = list(self.tree.item(項目, "values"))
        if not 值:
            return
        值[0] = "☑" if 值[0] == "☐" else "☐"
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
                        "此項目是每組第 1 個預設保留檔案。\n"
                        "如需勾選，請到設定開啟「允許勾選每組第 1 個檔案」。"
                    )
                    return "break"
                self.切換勾選狀態(項目)
                return "break"





