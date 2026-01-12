"""
Automated installation and run script for Windows
"""

import sys
import subprocess
from pathlib import Path


# ----------------------------
# Paths (single source of truth)
# ----------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
VENV_DIR = SCRIPT_DIR / "venv"
SCRIPTS_DIR = VENV_DIR / "Scripts"
VENV_PYTHON = SCRIPTS_DIR / "python.exe"

REQUIREMENTS_FILE = SCRIPT_DIR / "requirements.txt"
SETUP_SCRIPT = SCRIPT_DIR / "setup.py"
INIT_DB_SCRIPT = SCRIPT_DIR / "init_db.py"
MAIN_SCRIPT = SCRIPT_DIR / "main.py"
ENV_FILE = SCRIPT_DIR / ".env"


# ----------------------------
# Helpers
# ----------------------------

def print_header(message):
    print("\n" + "=" * 70)
    print(f"  {message}")
    print("=" * 70)


def print_step(step_num, message):
    print(f"\n[{step_num}] {message}")


# ----------------------------
# Checks
# ----------------------------

def check_python_version():
    print_step("✓", "Checking Python version...")
    v = sys.version_info
    if v < (3, 8):
        print(f"❌ Python 3.8+ required. Found {v.major}.{v.minor}")
        return False
    print(f"✅ Python {v.major}.{v.minor}.{v.micro} detected")
    return True


def check_ffmpeg():
    print_step("ℹ", "Checking for ffmpeg...")
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        print("✅ ffmpeg is installed")
        return True
    except Exception:
        print("⚠️  ffmpeg not found (optional)")
        print("   https://ffmpeg.org/download.html")
        return False


# ----------------------------
# Virtual environment
# ----------------------------

def create_venv():
    print_step("1", "Creating virtual environment...")

    if VENV_DIR.exists():
        print("⚠️  Virtual environment already exists. Skipping.")
        return True

    try:
        subprocess.run([sys.executable, "-m", "venv", str(VENV_DIR)], check=True)
        print("✅ Virtual environment created")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create venv: {e}")
        return False


def get_venv_python():
    if not VENV_PYTHON.exists():
        raise FileNotFoundError(f"venv python not found at {VENV_PYTHON}")
    return str(VENV_PYTHON)


# ----------------------------
# Dependencies
# ----------------------------

def install_dependencies():
    print_step("2", "Installing dependencies...")

    if not REQUIREMENTS_FILE.exists():
        print(f"❌ requirements.txt not found: {REQUIREMENTS_FILE}")
        return False

    python = get_venv_python()

    try:
        print("   Upgrading pip...")
        subprocess.run([python, "-m", "pip", "install", "--upgrade", "pip"], check=True)

        print("   Installing requirements...")
        subprocess.run([python, "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)], check=True)

        print("✅ Dependencies installed successfully")
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Dependency installation failed: {e}")
        return False


# ----------------------------
# Setup & database
# ----------------------------

def run_setup():
    print_step("3", "Running setup...")

    if ENV_FILE.exists():
        print("⚠️  .env already exists. Skipping setup.")
        return True

    if not SETUP_SCRIPT.exists():
        print(f"❌ setup.py not found: {SETUP_SCRIPT}")
        return False

    try:
        subprocess.run([get_venv_python(), str(SETUP_SCRIPT)], check=True)
        print("✅ Configuration generated")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Setup failed: {e}")
        return False


def init_database():
    print_step("4", "Initializing database...")

    if not INIT_DB_SCRIPT.exists():
        print(f"❌ init_db.py not found: {INIT_DB_SCRIPT}")
        return False

    try:
        subprocess.run([get_venv_python(), str(INIT_DB_SCRIPT)], check=True)
        print("✅ Database initialized")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Database init failed: {e}")
        return False


# ----------------------------
# Run app
# ----------------------------

def start_application():
    print_step("5", "Starting application...")

    if not MAIN_SCRIPT.exists():
        print(f"❌ main.py not found: {MAIN_SCRIPT}")
        return False

    print("\n🚀 Application running at http://localhost:8000")
    print("⌨️  Press Ctrl+C to stop\n")

    try:
        subprocess.run([get_venv_python(), str(MAIN_SCRIPT)], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Application stopped")
    except subprocess.CalledProcessError as e:
        print(f"❌ Application crashed: {e}")
        return False

    return True


# ----------------------------
# Main
# ----------------------------

def main():
    print_header("YouTube Video Downloader - Windows Installer")

    if not check_python_version():
        sys.exit(1)

    check_ffmpeg()

    if not create_venv():
        sys.exit(1)

    if not install_dependencies():
        sys.exit(1)

    if not run_setup():
        sys.exit(1)

    if not init_database():
        sys.exit(1)

    print_header("Installation Complete!")

    response = input("\n🚀 Start the application now? (Y/n): ").strip().lower()
    if response in ("", "y", "yes"):
        start_application()
    else:
        print(f"\nRun later with:\n{get_venv_python()} {MAIN_SCRIPT}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️  Installation cancelled")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
