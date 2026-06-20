"""重複檔案與空資料夾掃描核心。

UI 只負責顯示結果；實際掃描、忽略路徑、hash 比對都集中在這裡。
"""

import os
import hashlib
from collections import defaultdict


def 正規化路徑(路徑):
    """把路徑轉成可比較格式，避免大小寫或斜線差異造成誤判。"""
    return os.path.normcase(os.path.normpath(os.path.abspath(路徑)))


def 是否在忽略路徑內(路徑, 忽略路徑列表):
    """判斷目前路徑是否位於任一個忽略路徑底下。"""
    if not 忽略路徑列表:
        return False

    正規路徑 = 正規化路徑(路徑)
    for 忽略路徑 in 忽略路徑列表:
        try:
            if os.path.commonpath([正規路徑, 忽略路徑]) == 忽略路徑:
                return True
        except ValueError:
            continue
    return False


def 取得多個資料夾內所有檔案路徑(資料夾路徑列表, 允許副檔名=None, 是否取消=None, 忽略路徑列表=None):
    """遞迴取得所有檔案；支援副檔名過濾、忽略路徑與取消掃描。"""
    檔案列表 = []
    允許副檔名 = {ext.lower() for ext in 允許副檔名} if 允許副檔名 else None
    忽略路徑列表 = [正規化路徑(路徑) for 路徑 in (忽略路徑列表 or []) if 路徑]

    for 資料夾 in 資料夾路徑列表:
        for 根目錄, 子目錄們, 檔案們 in os.walk(資料夾):
            if 是否取消 and 是否取消():
                return None

            if 是否在忽略路徑內(根目錄, 忽略路徑列表):
                子目錄們[:] = []
                檔案們[:] = []
                continue

            子目錄們[:] = [
                子目錄
                for 子目錄 in 子目錄們
                if not 是否在忽略路徑內(os.path.join(根目錄, 子目錄), 忽略路徑列表)
            ]

            for 檔名 in 檔案們:
                if 允許副檔名:
                    副檔名 = os.path.splitext(檔名)[1].lower()
                    if 副檔名 not in 允許副檔名:
                        continue

                完整路徑 = os.path.normpath(os.path.abspath(os.path.join(根目錄, 檔名)))
                檔案列表.append(完整路徑)

    return 檔案列表


def 找出空資料夾(資料夾路徑列表, 是否取消=None, 忽略路徑列表=None):
    """找出所有空資料夾。

    掃描方向由底層往上，因此如果 A/B/C 都沒有檔案，C、B、A 都會列入。
    """
    空資料夾列表 = []
    空資料夾集合 = set()
    忽略路徑列表 = [正規化路徑(路徑) for 路徑 in (忽略路徑列表 or []) if 路徑]

    for 資料夾 in 資料夾路徑列表:
        for 根目錄, 子目錄們, 檔案們 in os.walk(資料夾, topdown=False):
            if 是否取消 and 是否取消():
                return None

            if 是否在忽略路徑內(根目錄, 忽略路徑列表):
                continue

            可見子目錄 = [
                os.path.join(根目錄, 子目錄)
                for 子目錄 in 子目錄們
                if not 是否在忽略路徑內(os.path.join(根目錄, 子目錄), 忽略路徑列表)
            ]

            正規根目錄 = 正規化路徑(根目錄)
            子目錄全為空 = all(正規化路徑(子目錄) in 空資料夾集合 for 子目錄 in 可見子目錄)

            if not 檔案們 and 子目錄全為空:
                空資料夾集合.add(正規根目錄)
                空資料夾列表.append(os.path.normpath(os.path.abspath(根目錄)))

    return 空資料夾列表


def 計算檔案雜湊值(檔案路徑, 區塊大小=1024 * 1024, 是否取消=None, 掃描模式="完整"):
    """計算檔案 hash；快速模式只取檔案頭尾區塊來提升速度。"""
    md5 = hashlib.md5()
    檔案大小 = os.path.getsize(檔案路徑)

    with open(檔案路徑, "rb") as f:
        if 掃描模式 == "快速" and 檔案大小 > 區塊大小 * 2:
            開頭 = f.read(區塊大小)
            if 是否取消 and 是否取消():
                return None

            f.seek(max(檔案大小 - 區塊大小, 0))
            結尾 = f.read(區塊大小)
            md5.update(str(檔案大小).encode("ascii"))
            md5.update(開頭)
            md5.update(結尾)
            return md5.hexdigest()

        while True:
            if 是否取消 and 是否取消():
                return None

            data = f.read(區塊大小)
            if not data:
                break
            md5.update(data)

    return md5.hexdigest()


def 找出重複檔案(資料夾路徑列表, 進度回呼=None, 是否取消=None, 允許副檔名=None, 掃描模式="完整", 忽略路徑列表=None):
    """
    回傳：
    [
        [檔案1, 檔案2, 檔案3],
        [檔案A, 檔案B]
    ]
    """

    所有檔案 = 取得多個資料夾內所有檔案路徑(資料夾路徑列表, 允許副檔名, 是否取消, 忽略路徑列表)
    if 所有檔案 is None:
        return None

    總數 = len(所有檔案)
    if 總數 == 0:
        if 進度回呼:
            進度回呼(0, 0, "")
        return []

    # ===== 1️⃣ 先用「檔案大小」分組（效能關鍵）
    大小分組 = defaultdict(list)

    for 路徑 in 所有檔案:
        if 是否取消 and 是否取消():
            return None

        try:
            size = os.path.getsize(路徑)
            大小分組[size].append(路徑)
        except:
            continue

    # ===== 2️⃣ 再做 hash
    雜湊分組 = defaultdict(list)
    已處理 = 0

    for 同大小列表 in 大小分組.values():

        # 只有一個 → 不可能重複
        if len(同大小列表) < 2:
            已處理 += len(同大小列表)
            if 進度回呼:
                進度回呼(已處理, 總數, 同大小列表[-1])
            continue

        for 路徑 in 同大小列表:
            if 是否取消 and 是否取消():
                return None

            try:
                h = 計算檔案雜湊值(路徑, 是否取消=是否取消, 掃描模式=掃描模式)
                if h is None:
                    return None

                雜湊分組[h].append(路徑)

            except:
                pass

            已處理 += 1

            if 進度回呼:
                進度回呼(已處理, 總數, 路徑)

    if 進度回呼 and 已處理 < 總數:
        進度回呼(總數, 總數, 所有檔案[-1] if 所有檔案 else "")

    # ===== 3️⃣ 整理結果
    結果 = []

    for group in 雜湊分組.values():
        if len(group) > 1:
            結果.append(group)

    return 結果
