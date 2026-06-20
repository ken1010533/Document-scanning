# -*- coding: utf-8 -*-
"""
編輯器設定管理模組
功能：管理程式碼編輯器的各項設定，包括字型、主題和功能選項
"""

import json
from typing import Dict, Any

class 編輯器設定管理器:
    """管理編輯器設定的類別"""
    
    def __init__(self):
        # 預設編輯器設定
        self.設定 = {
            # 字型設定
            "字型": {
                "名稱": "Consolas",  # 建議使用等寬字型方便程式碼對齊
                "大小": 14,         # 字型大小(單位:像素)
                "行高": 1.5,        # 行距倍數
                "啟用連字": True    # 是否啟用程式設計連字(如=>, !=等符號連接)
            },
            
            # 語法高亮主題設定
            "主題": {
                "名稱": "Dracula",  # 主題名稱
                "前景色": "#F8F8F2",  # 預設文字顏色
                "背景色": "#282A36",   # 編輯器背景顏色
                "關鍵字顏色": "#FF79C6",  # Python關鍵字顏色(如if, def等)
                "函數顏色": "#50FA7B",    # 函數名稱顏色
                "字串顏色": "#F1FA8C",    # 字串文字顏色
                "註釋顏色": "#6272A4",   # 註釋文字顏色
                "數字顏色": "#BD93F9",     # 數字顏色
                "行號顏色": "#44475A"     # 行號區顏色
            },
            
            # 編輯器功能設定
            "功能": {
                "顯示行號": True,          # 是否顯示行號
                "高亮當前行": True,        # 是否高亮游標所在行
                "括號匹配": True,          # 是否高亮匹配的括號
                "自動縮排": True,          # 是否自動根據語法縮排
                "程式碼折疊": True,        # 是否啟用程式碼折疊功能
                "自動完成": True,          # 是否啟用自動完成提示
                "即時錯誤檢查": True,      # 是否啟用即時語法檢查
                "右邊界": 80,              # 程式碼右邊界參考線位置
                "Tab大小": 4,              # Tab鍵的空白格數
                "轉換Tab為空格": True      # 是否將Tab轉換為空格
            },
            
            # 其他進階設定
            "進階": {
                "字型平滑": "次像素",      # 字型平滑方式(無/標準/次像素)
                "縮排參考線": True,        # 顯示縮排參考虛線
                "懸浮提示延遲": 300,       # 懸浮提示延遲(毫秒)
                "啟用GPU加速": True,       # 是否啟用GPU硬體加速
                "自動儲存": False,         # 是否啟用自動儲存功能
                "備份間隔": 30000          # 自動備份間隔(毫秒)
            }
        }
    
    def 顯示設定(self) -> None:
        """以易讀格式顯示當前編輯器設定"""
        print("當前編輯器設定:")
        for 分類, 選項 in self.設定.items():
            print(f"\n[{分類}]")
            for 項目, 值 in 選項.items():
                print(f"  {項目}: {值}")
    
    def 儲存設定(self, 檔案路徑: str) -> None:
        """將當前設定儲存到JSON檔案"""
        try:
            with open(檔案路徑, 'w', encoding='utf-8') as 檔案:
                json.dump(self.設定, 檔案, indent=4, ensure_ascii=False)
            print(f"\n設定已成功儲存至 {檔案路徑}")
        except Exception as 錯誤:
            print(f"\n儲存設定時發生錯誤: {錯誤}")
    
    def 載入設定(self, 檔案路徑: str) -> bool:
        """從JSON檔案載入設定"""
        try:
            with open(檔案路徑, 'r', encoding='utf-8') as 檔案:
                self.設定 = json.load(檔案)
            print(f"\n設定已從 {檔案路徑} 成功載入")
            return True
        except Exception as 錯誤:
            print(f"\n載入設定時發生錯誤: {錯誤}")
            return False
    
    def 取得設定值(self, 分類: str, 項目: str) -> Any:
        """取得特定設定值"""
        try:
            return self.設定[分類][項目]
        except KeyError:
            print(f"找不到設定: {分類}/{項目}")
            return None
    
    def 更新設定值(self, 分類: str, 項目: str, 值: Any) -> bool:
        """更新特定設定值"""
        try:
            self.設定[分類][項目] = 值
            return True
        except KeyError:
            print(f"找不到設定: {分類}/{項目}")
            return False
    
    def 重設為預設值(self) -> None:
        """將所有設定恢復為預設值"""
        self.__init__()
        print("\n所有設定已重設為預設值")

def 主選單():
    """顯示主選單"""
    print("\n=== 編輯器設定管理 ===")
    print("1. 顯示當前設定")
    print("2. 修改設定值")
    print("3. 儲存設定到檔案")
    print("4. 從檔案載入設定")
    print("5. 重設為預設值")
    print("0. 離開程式")
    return input("請選擇操作: ")

if __name__ == "__main__":
    # 建立設定管理器實例
    管理器 = 編輯器設定管理器()
    
    while True:
        選擇 = 主選單()
        
        if 選擇 == "1":
            # 顯示當前設定
            管理器.顯示設定()
        
        elif 選擇 == "2":
            # 修改設定值
            print("\n可用的設定分類:")
            for 分類 in 管理器.設定.keys():
                print(f"- {分類}")
            
            分類 = input("\n請輸入要修改的分類名稱: ")
            項目 = input("請輸入要修改的項目名稱: ")
            
            if 分類 in 管理器.設定 and 項目 in 管理器.設定[分類]:
                當前值 = 管理器.取得設定值(分類, 項目)
                print(f"\n當前 {分類}/{項目} = {當前值} (類型: {type(當前值).__name__})")
                新值 = input("請輸入新值: ")
                
                # 嘗試轉換輸入值為正確類型
                try:
                    if isinstance(當前值, bool):
                        新值 = 新值.lower() in ('true', '1', 't', 'y', 'yes')
                    elif isinstance(當前值, int):
                        新值 = int(新值)
                    elif isinstance(當前值, float):
                        新值 = float(新值)
                    
                    if 管理器.更新設定值(分類, 項目, 新值):
                        print("設定已更新!")
                except ValueError:
                    print("錯誤: 輸入值類型不匹配!")
            else:
                print("錯誤: 找不到指定的分類或項目!")
        
        elif 選擇 == "3":
            # 儲存設定到檔案
            檔案路徑 = input("\n請輸入要儲存的檔案路徑: ")
            管理器.儲存設定(檔案路徑)
        
        elif 選擇 == "4":
            # 從檔案載入設定
            檔案路徑 = input("\n請輸入要載入的設定檔案路徑: ")
            管理器.載入設定(檔案路徑)
        
        elif 選擇 == "5":
            # 重設為預設值
            管理器.重設為預設值()
        
        elif 選擇 == "0":
            # 離開程式
            print("\n感謝使用編輯器設定管理工具!")
            break
        
        else:
            print("\n無效的選擇，請重新輸入!")
        
        input("\n按 Enter 鍵繼續...")