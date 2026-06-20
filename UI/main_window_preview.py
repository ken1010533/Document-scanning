"""圖片、文字、影片與外部開啟預覽流程。

這個模組從 main_window.py 拆出來，讓主視窗檔案維持薄而好讀。
方法仍以 mixin 形式操作主頁面的 self 狀態，避免重寫既有事件流程。
"""

import mimetypes
import os
import platform
import subprocess
from tkinter import messagebox
from PIL import Image, ImageTk
from UI.file_types import 圖片副檔名集合, 影片副檔名集合, 文字副檔名集合, 文件副檔名集合


class 預覽Mixin:
    """圖片、文字、影片與外部開啟預覽流程。"""

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



    def 可文字預覽(self, 路徑):
        副檔名 = os.path.splitext(路徑)[1].lower()
        if 副檔名 in 文字副檔名集合:
            return True

        mime, _ = mimetypes.guess_type(路徑)
        return bool(mime and mime.startswith("text/"))



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



    def 拖曳影片進度(self, value):
        if not self.影片進度拖曳中:
            return

        self.更新影片時間標籤(float(value))



    def 排程影片播放(self):
        if not self.影片播放中 or not self.影片擷取器:
            return

        還有影格 = self.顯示下一個影片影格()
        if not 還有影格:
            self.影片播放中 = False
            return

        延遲 = max(10, int(1000 / self.影片FPS))
        self.影片播放工作 = self.after(延遲, self.排程影片播放)



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



    def 更新影片時間標籤(self, 影格位置):
        目前秒數 = float(影格位置) / self.影片FPS if self.影片FPS else 0
        總秒數 = self.影片總影格 / self.影片FPS if self.影片FPS and self.影片總影格 else 0
        self.影片時間標籤.config(text=f"{self.格式化影片時間(目前秒數)} / {self.格式化影片時間(總秒數)}")



    def 更新影片進度(self, 目前影格):
        if self.影片進度拖曳中:
            return

        顯示影格 = max(0, 目前影格 - 1)
        self.影片進度變數.set(顯示影格)
        self.更新影片時間標籤(顯示影格)



    def 格式化影片時間(self, 秒數):
        秒數 = max(0, int(秒數))
        分鐘, 秒 = divmod(秒數, 60)
        小時, 分鐘 = divmod(分鐘, 60)
        if 小時:
            return f"{小時:02d}:{分鐘:02d}:{秒:02d}"
        return f"{分鐘:02d}:{秒:02d}"



    def 清空預覽(self):
        self.停止影片播放()
        self.預覽標題標籤.config(text="請在左側選擇檔案")
        self.預覽類型標籤.config(text="未選擇")
        self.顯示圖片預覽()
        self.預覽圖片標籤.config(image="", text="尚未選擇檔案")
        self.設定預覽資訊("類型：\n檔名：\n路徑：\n大小：")
        self.預覽圖片物件 = None



    def 設定預覽資訊(self, 文字):
        self.預覽資訊文字.config(state="normal")
        self.預覽資訊文字.delete("1.0", "end")
        self.預覽資訊文字.insert("1.0", 文字)
        self.預覽資訊文字.config(state="disabled")



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



    def 重設影片進度(self):
        self.影片總影格 = 0
        self.影片進度拖曳中 = False
        self.拖曳前影片播放中 = False
        self.影片進度滑桿.configure(to=0)
        self.影片進度變數.set(0)
        self.影片時間標籤.config(text="00:00 / 00:00")



    def 開始拖曳影片進度(self, event=None):
        self.拖曳前影片播放中 = self.影片播放中
        self.影片進度拖曳中 = True
        self.暫停影片()



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



    def 顯示圖片預覽(self):
        self.預覽影片框架.pack_forget()
        self.預覽文字框架.pack_forget()
        if not self.預覽圖片標籤.winfo_ismapped():
            self.預覽圖片標籤.pack(fill="both", expand=True)
        self.預覽文字.config(state="normal")
        self.預覽文字.delete("1.0", "end")
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





