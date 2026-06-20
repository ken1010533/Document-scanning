"""掃描啟停、背景掃描、結果儲存與結果列表插入。

這個模組從 main_window.py 拆出來，讓主視窗檔案維持薄而好讀。
方法仍以 mixin 形式操作主頁面的 self 狀態，避免重寫既有事件流程。
"""

from tkinter import messagebox
import json
import os
import threading
from UI.file_types import 圖片副檔名集合, 影片副檔名集合, 文字副檔名集合
from core.duplicate_finder import 找出重複檔案, 找出空資料夾


class 掃描結果Mixin:
    """掃描啟停、背景掃描、結果儲存與結果列表插入。"""

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


    def 掃描結束(self):
        self.掃描中 = False
        self.取消掃描中 = False
        self.取消刪除中 = False
        self.設定按鈕狀態(True)
        self.取消按鈕.config(state="disabled")



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



    def 顯示錯誤(self, 錯誤訊息):
        self.掃描結束()
        self.狀態標籤.config(text="掃描失敗", foreground="red")
        self.結果摘要標籤.config(text="掃描失敗，請檢查錯誤訊息")
        self.進度文字標籤.config(text="掃描失敗")
        messagebox.showerror("錯誤", 錯誤訊息)





