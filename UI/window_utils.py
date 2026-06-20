"""視窗相關工具函式。"""


def 主視窗至中(窗口):
    """依螢幕尺寸設定主視窗大小並置中。"""
    窗口.update_idletasks()
    螢幕寬 = 窗口.winfo_screenwidth()
    螢幕高 = 窗口.winfo_screenheight()
    視窗寬 = int(螢幕寬 * 0.9)
    視窗高 = int(螢幕高 * 0.88)
    左上x軸 = int((螢幕寬 - 視窗寬) / 2)
    左上y軸 = int((螢幕高 - 視窗高) / 2)
    窗口.geometry(f"{視窗寬}x{視窗高}+{左上x軸}+{左上y軸}")
