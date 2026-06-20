# 專案結構說明

## 現役程式

- `UI.py`：應用程式啟動入口。
- `UI/main_window.py`：主視窗、路徑管理、掃描結果、預覽、刪除與匯出流程。
- `UI/settings.py`：設定頁，負責讀寫 `config.json`。
- `UI/file_types.py`：副檔名分類，供預覽與檔案類型判斷使用。
- `UI/window_utils.py`：視窗工具，目前負責主視窗置中。
- `core/duplicate_finder.py`：掃描重複檔案與空資料夾的核心邏輯。
- `core/excel_export.py`：Excel 匯出。
- `core/config.py`：設定檔讀寫。

## 本機資料

- `config.json`：使用者設定。
- `last_paths.json`：上次使用的掃描路徑。
- `last_scan_result.json`：上次掃描結果。

## 封存資料

- `archive/legacy_code/`：舊版或目前未使用的根目錄腳本。
- `archive/legacy_ui/`：舊版或目前未使用的 UI 模組。
- `archive/exports/`：過去匯出的 Excel 檔案。
- `archive/cache/`：舊的 Python 快取檔。

## 啟動方式

```powershell
python UI.py
```

如果缺少套件，先安裝：

```powershell
pip install openpyxl Pillow send2trash
```
