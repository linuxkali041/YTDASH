
import sys
import subprocess

def upgrade_ytdlp():
    print(f"Using Python executable: {sys.executable}")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"])
        print("Successfully upgraded yt-dlp")
    except subprocess.CalledProcessError as e:
        print(f"Failed to upgrade yt-dlp: {e}")

if __name__ == "__main__":
    upgrade_ytdlp()
