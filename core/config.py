"""設定檔讀寫工具。

目前設定集中存放在根目錄 config.json。
UI/settings.py 寫入設定，UI/main_window.py 讀取設定。
"""

import json
import os

設定檔 = "config.json"


def 讀取設定():
    """讀取 config.json；檔案不存在時回傳空 dict，呼叫端負責補預設值。"""
    if not os.path.exists(設定檔):
        return {}

    with open(設定檔, "r", encoding="utf-8") as f:
        return json.load(f)


def 儲存設定(data):
    """把設定 dict 寫回 config.json。"""
    with open(設定檔, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
