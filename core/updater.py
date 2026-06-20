import subprocess
import os
import sys


def 執行指令(cmd):
    return subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )


def 檢查更新():
    repo_path = os.path.abspath(os.path.dirname(sys.argv[0]))

    try:
        # 1️⃣ 確認是 git 專案
        if not os.path.exists(os.path.join(repo_path, ".git")):
            return "❌ 非 Git 專案"

        # 2️⃣ 更新遠端資訊
        執行指令(['git', 'remote', 'update'])

        # 3️⃣ 檢查狀態
        result = 執行指令(['git', 'status', '-uno'])
        status = result.stdout.lower()

        if 'behind' in status:
            # 4️⃣ 抓預設分支（避免 main / master 問題）
            branch_result = 執行指令(['git', 'rev-parse', '--abbrev-ref', 'HEAD'])
            branch = branch_result.stdout.strip()

            # 5️⃣ 同步
            執行指令(['git', 'fetch', '--all'])
            執行指令(['git', 'reset', '--hard', f'origin/{branch}'])

            # 6️⃣ 重啟程式
            重啟程式()

            return "🔄 已更新並重新啟動"

        else:
            return "✅ 已是最新版本"

    except Exception as e:
        # 修正 safe.directory
        if "dubious ownership" in str(e):
            subprocess.run([
                'git', 'config', '--global',
                '--add', 'safe.directory', repo_path
            ])
            return 檢查更新()

        return f"⚠️ 更新失敗: {e}"


def 重啟程式():
    python = sys.executable
    os.execl(python, python, *sys.argv)