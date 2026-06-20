"""應用程式啟動入口。

實際的主視窗與頁面邏輯放在 UI/main_window.py。
保留這個薄入口，之後啟動方式仍可使用：

    python UI.py
"""

from UI.main_window import 主應用程式


if __name__ == "__main__":
    app = 主應用程式()
    app.mainloop()
