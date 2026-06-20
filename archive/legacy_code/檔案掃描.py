import os

def 掃描資料夾(路徑):
    檔案列表 = []
    for 根目錄, _, 檔案們 in os.walk(路徑):
        for 檔案 in 檔案們:
            完整路徑 = os.path.join(根目錄, 檔案)
            檔案列表.append(完整路徑)
    return 檔案列表