from collections import defaultdict
import os
from hash import 計算檔案hash

def 快速hash(檔案路徑):
    import hashlib
    h = hashlib.md5()
    with open(檔案路徑, 'rb') as f:
        h.update(f.read(4096))
    return h.hexdigest()

def 找出重複檔案(檔案列表, 進度回呼=None):
    總數 = len(檔案列表)
    已處理 = 0

    # 1️⃣ 檔案大小分組
    大小字典 = defaultdict(list)
    for 檔案 in 檔案列表:
        try:
            大小 = os.path.getsize(檔案)
            大小字典[大小].append(檔案)
        except Exception:
            continue

    # 2️⃣ 快速hash
    快速字典 = defaultdict(list)
    for 檔案群 in 大小字典.values():
        if len(檔案群) < 2:
            continue

        for 檔案 in 檔案群:
            try:
                h = 快速hash(檔案)
                快速字典[h].append(檔案)
            except Exception:
                pass

            已處理 += 1
            if 進度回呼:
                進度回呼(已處理, 總數)

    # 3️⃣ 完整hash（只針對可疑）
    最終字典 = defaultdict(list)
    for 檔案群 in 快速字典.values():
        if len(檔案群) < 2:
            continue

        for 檔案 in 檔案群:
            try:
                h = 計算檔案hash(檔案)
                最終字典[h].append(檔案)
            except Exception:
                pass

    return [v for v in 最終字典.values() if len(v) > 1]