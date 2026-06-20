import json
import os

設定檔案 = "設定.json"

# 讀取設定
def 讀取設定():
    if not os.path.exists(設定檔案):
        return {}  # 檔案不存在時回傳空字典
    try:
        with open(設定檔案, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}  # JSON 解析失敗時回傳空字典

# 寫入設定
def 寫入設定(**kwargs):
    設定 = 讀取設定()
    設定.update(kwargs)
    with open(設定檔案, "w", encoding="utf-8") as f:
        json.dump(設定, f, ensure_ascii=False, indent=4)
