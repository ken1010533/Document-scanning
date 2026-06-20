"""檔案類型分類設定。

主視窗會用這些集合判斷預覽方式與顯示類型。
只要日後要支援更多副檔名，優先改這個檔案。
"""

圖片副檔名集合 = {
    ".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp", ".tiff"
}

影片副檔名集合 = {
    ".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".webm", ".m4v", ".mpeg", ".mpg"
}

文字副檔名集合 = {
    ".txt", ".log", ".md", ".csv", ".tsv", ".json", ".xml", ".html", ".htm",
    ".css", ".js", ".ts", ".py", ".java", ".c", ".cpp", ".h", ".hpp", ".cs",
    ".go", ".rs", ".php", ".rb", ".sh", ".bat", ".ps1", ".ini", ".cfg", ".conf",
    ".yaml", ".yml", ".toml", ".sql", ".rtf"
}

文件副檔名集合 = {
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".odt", ".ods", ".odp"
}
