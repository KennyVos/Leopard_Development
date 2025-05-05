import os
import shutil
import subprocess
import tempfile
import stat
from dotenv import load_dotenv


load_dotenv()

# === CONFIGURATIE UIT .env ===
GITHUB_USER = os.getenv("GITHUB_USER")
GITHUB_PAT = os.getenv("GITHUB_PAT")
SOURCE_REPO_NAME = os.getenv("SOURCE_REPO_NAME")
TARGET_REPO_NAME = os.getenv("TARGET_REPO_NAME")


SOURCE_REPO = f"https://{GITHUB_USER}:{GITHUB_PAT}@github.com/{GITHUB_USER}/{SOURCE_REPO_NAME}.git"
TARGET_REPO = f"https://{GITHUB_USER}:{GITHUB_PAT}@github.com/{GITHUB_USER}/{TARGET_REPO_NAME}.git"

# === COMMANDO-HULPFUNCTIE ===
def run(command, cwd=None):
    print(f"⚙️  {command}")
    result = subprocess.run(command, shell=True, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"❌ Fout bij commando: {command}\n{result.stderr}")
    return result.stdout.strip()

# === BESTANDEN VEILIG VERWIJDEREN (WINDOWS) ===
def on_rm_error(func, path, exc_info):
    os.chmod(path, stat.S_IWRITE)
    func(path)

# === SNAPSHOT MIRRORING ===
def snapshot_mirror():
    temp_dir = tempfile.mkdtemp()
    clone_path = os.path.join(temp_dir, "clone")
    clean_path = os.path.join(temp_dir, "clean")

    try:
        print("📥 Cloning volledige master branch...")
        run(f"git clone --branch master {SOURCE_REPO} clone", cwd=temp_dir)

        print("📤 Extract laatste snapshot (zonder .git)...")
        shutil.copytree(clone_path, clean_path, ignore=shutil.ignore_patterns('.git'))

        print("🧾 Haal originele commit-boodschap op...")
        commit_message = run("git log -1 --pretty=%B", cwd=clone_path)

        print("🧱 Initialiseer nieuwe Git-repo in clean folder...")
        run("git init", cwd=clean_path)
        run("git config user.name \"YPTF-Engineering\"", cwd=clean_path)
        run("git config user.email \"Engineering@yYPTF-Engineering.be\"", cwd=clean_path)

        run("git add .", cwd=clean_path)
        run(f'git commit -m "{commit_message.strip()}"', cwd=clean_path)

        print("🔗 Push naar mirror-repo...")
        run(f"git remote add origin {TARGET_REPO}", cwd=clean_path)
        run("git branch -M master", cwd=clean_path)
        run("git push -f origin master", cwd=clean_path)

        print("✅ Laatste snapshot succesvol gepusht.")
    finally:
        print("🧹 Opruimen...")
        shutil.rmtree(temp_dir, onerror=on_rm_error)


# === UITVOERING ===
if __name__ == "__main__":
    try:
        snapshot_mirror()
    except Exception as e:
        print(f"❌ Fout tijdens mirroren: {e}")
