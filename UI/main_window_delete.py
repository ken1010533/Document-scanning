"""勾選檔案移到回收桶與刪除後 UI 同步。

這個模組從 main_window.py 拆出來，讓主視窗檔案維持薄而好讀。
方法仍以 mixin 形式操作主頁面的 self 狀態，避免重寫既有事件流程。
"""

from tkinter import messagebox
import os
import threading
from send2trash import send2trash


class 刪除Mixin:
    """勾選檔案移到回收桶與刪除後 UI 同步。"""

    def 刪除單筆完成更新UI(self, 項目ID, 目前, 總數, 百分比):
        self.移除結果項目(項目ID)
        self.更新刪除進度(目前, 總數, 百分比)



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



    def 快速刪除完成更新UI(self, 項目ID列表, 失敗清單):
        for 項目ID in 項目ID列表:
            self.移除結果項目(項目ID)
        self.進度條["value"] = 100
        self.刪除完成(len(項目ID列表), 失敗清單)



    def 更新刪除進度(self, 目前, 總數, 百分比):
        self.進度條["value"] = 百分比
        self.進度文字標籤.config(text=f"刪除進度：{目前}/{總數}（{百分比:.1f}%）")
        self.狀態標籤.config(text=f"刪除中：{目前}/{總數}（{百分比:.1f}%）", foreground="blue")



    def 更新快速刪除狀態(self, 總數):
        self.進度條["value"] = 0
        self.進度文字標籤.config(text=f"正在快速刪除中：共 {總數} 個項目")
        self.狀態標籤.config(text="快速刪除中，請稍候...", foreground="blue")



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





