from 檔案掃描 import 掃描資料夾
from core.duplicate_finder import 找出重複檔案
from core.excel_export import 輸出Excel
from tkinter import filedialog, Tk
from 自動更新 import 檢查更新
def 顯示進度(目前, 總數):
    百分比 = (目前 / 總數) * 100
    print(f"\r比對進度: {目前}/{總數} ({百分比:.2f}%)", end="", flush=True)
 
 
def 選擇多資料夾():
    root = Tk()
    root.withdraw()

    路徑列表 = []

    while True:
        路徑 = filedialog.askdirectory(title="選擇資料夾（取消結束）")
        if not 路徑:
            break
        路徑列表.append(路徑)

    return 路徑列表


def 主程式():
    路徑列表 = 選擇多資料夾()

    if not 路徑列表:
        print("未選擇任何資料夾")
        return

    print("選擇的資料夾：")
    for p in 路徑列表:
        print(p)

    全部檔案 = [] 

    print("掃描中...")
    for 路徑 in 路徑列表:
        檔案列表 = 掃描資料夾(路徑)
        全部檔案.extend(檔案列表)

    print(f"共找到 {len(全部檔案)} 個檔案")

    print("比對中（Hash）...")
    重複結果 = 找出重複檔案(全部檔案, 顯示進度)

    print("\n完成")

    輸出Excel(重複結果)


if __name__ == "__main__":
    檢查更新()
    主程式()