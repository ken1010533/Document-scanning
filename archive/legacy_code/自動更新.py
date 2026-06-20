import subprocess
import os
import sys


def 執行指令(cmd):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

 
def 檢查更新():
    repo_path = os.path.abspath(os.path.dirname(__file__))

    try:
        # 1️⃣ 確認是 git 專案
        if not os.path.exists(os.path.join(repo_path, ".git")):
            print("❌ 非 Git 專案，無法更新")
            return

        print("🔍 檢查更新中...")

        # 2️⃣ 更新遠端資訊
        執行指令(['git', 'remote', 'update'])

        # 3️⃣ 檢查是否落後
        result = 執行指令(['git', 'status', '-uno'])
        status = result.stdout

        if 'behind' in status:
            print("🔄 發現更新，開始同步...")

            # 4️⃣ 強制同步（最穩）
            執行指令(['git', 'fetch', '--all'])
            執行指令(['git', 'reset', '--hard', 'origin/main'])  # ⚠️ 如果不是 main 要改

            print("✅ 更新完成，重新啟動中...")

            # 5️⃣ 自動重啟
            os.execl(sys.executable, sys.executable, *sys.argv)

        else:
            print("✅ 已是最新版本")

    except subprocess.CalledProcessError as e:
        output = e.stderr if e.stderr else str(e)

        # 修正 safe.directory 問題
        if "dubious ownership" in output:
            print("⚠️ 修正 Git 安全目錄...")
            subprocess.run([
                'git', 'config', '--global',
                '--add', 'safe.directory', repo_path
            ])
            檢查更新()
        else:
            print("⚠️ 更新失敗：", output)

    except Exception as e:
        print("⚠️ 更新失敗：", e)