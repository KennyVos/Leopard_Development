
import os
import shutil
import subprocess
import tempfile
from dotenv import load_dotenv

load_dotenv()

# === CONFIGURATIE UIT .env ===
GITHUB_USER = os.getenv("GITHUB_USER")
GITHUB_PAT = os.getenv("GITHUB_PAT")
SOURCE_REPO_NAME = os.getenv("SOURCE_REPO_NAME")
TARGET_REPO_NAME = os.getenv("TARGET_REPO_NAME")


SOURCE_REPO = f"https://{GITHUB_USER}:{GITHUB_PAT}@github.com/{GITHUB_USER}/{SOURCE_REPO_NAME}.git"
TARGET_REPO = f"https://{GITHUB_USER}:{GITHUB_PAT}@github.com/{GITHUB_USER}/{TARGET_REPO_NAME}.git"

def run(cmd, cwd=None):
    result = subprocess.run(cmd, cwd=cwd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Fout bij commando: {cmd}\n{result.stderr}")
    return result.stdout.strip()

def mirror_first_parent():
    with tempfile.TemporaryDirectory() as temp_dir:
        source_path = os.path.join(temp_dir, "source")
        mirror_path = os.path.join(temp_dir, "mirror")

        print("📥 Clone source-repo...")
        run(f"git clone {SOURCE_REPO} {source_path}")
        run("git fetch origin master", cwd=source_path)

        print("📥 Clone mirror-repo...")
        run(f"git clone {TARGET_REPO} {mirror_path}")

        commits = run("git log --first-parent --reverse --format=%H origin/master", cwd=source_path).splitlines()

        for commit_hash in commits:
            print(f"🔁 Mirror commit: {commit_hash}")
            # Checkout de commit
            run(f"git checkout {commit_hash}", cwd=source_path)

            # Clear mirror repo (behalve .git)
            for item in os.listdir(mirror_path):
                if item == ".git":
                    continue
                item_path = os.path.join(mirror_path, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)

            # Copy files van source naar mirror
            for item in os.listdir(source_path):
                if item == ".git":
                    continue
                src_item = os.path.join(source_path, item)
                dst_item = os.path.join(mirror_path, item)
                if os.path.isdir(src_item):
                    shutil.copytree(src_item, dst_item)
                else:
                    shutil.copy2(src_item, dst_item)

            # Commit in mirror met commit message bestand
            message = run("git log -1 --pretty=%B", cwd=source_path).strip()
            author_name = run("git log -1 --pretty=%an", cwd=source_path).strip()
            author_email = run("git log -1 --pretty=%ae", cwd=source_path).strip()

            commit_file = os.path.join(mirror_path, "commit_msg.txt")
            with open(commit_file, "w", encoding="utf-8") as f:
                f.write(message)

            run("git add .", cwd=mirror_path)
            run(f'git -c user.name="{author_name}" -c user.email="{author_email}" commit -F "{commit_file}"', cwd=mirror_path)

        print("🚀 Push alle mirrored commits...")
        run("git push origin master", cwd=mirror_path)
        print("✅ Volledige mirror van first-parent master voltooid.")

if __name__ == "__main__":
    try:
        mirror_first_parent()
    except Exception as e:
        print(f"❌ Fout tijdens mirroring: {e}")
