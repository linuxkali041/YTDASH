"""
Setup script to configure the YouTube Downloader application.
Generates encryption keys, creates .env file, and prepares directories.
"""

from pathlib import Path
from cryptography.fernet import Fernet


# --------------------------------------------------
# Paths (single source of truth)
# --------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent

ENV_EXAMPLE = SCRIPT_DIR / ".env.example"
ENV_FILE = SCRIPT_DIR / ".env"

DOWNLOADS_DIR = SCRIPT_DIR / "downloads"
TEMP_DIR = SCRIPT_DIR / "temp"
LOGS_DIR = SCRIPT_DIR / "logs"


# --------------------------------------------------
# Helpers
# --------------------------------------------------

def generate_encryption_key():
    """Generate a new Fernet encryption key."""
    return Fernet.generate_key().decode()


def create_env_file():
    """Create .env file from template."""
    print("   Creating environment configuration...")

    if not ENV_EXAMPLE.exists():
        print(f"❌ .env.example not found at: {ENV_EXAMPLE}")
        return False

    if ENV_FILE.exists():
        response = input(".env file already exists. Overwrite? (y/N): ").strip().lower()
        if response != "y":
            print("⚠️  Setup cancelled. Existing .env kept.")
            return False

    encryption_key = generate_encryption_key()

    # Read template
    content = ENV_EXAMPLE.read_text(encoding="utf-8")

    # Replace encryption key placeholder
    content = content.replace(
        "COOKIE_ENCRYPTION_KEY=",
        f"COOKIE_ENCRYPTION_KEY={encryption_key}"
    )

    # Write .env file
    ENV_FILE.write_text(content, encoding="utf-8")

    print("✅ .env file created successfully!")
    print(f"🔑 Encryption key: {encryption_key}")
    print("\n⚠️  IMPORTANT: Keep this key secure and never commit it to version control!")

    return True


def create_directories():
    """Create necessary directories."""
    for directory in (DOWNLOADS_DIR, TEMP_DIR, LOGS_DIR):
        directory.mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory.name}")


# --------------------------------------------------
# Main
# --------------------------------------------------

def main():
    print("=" * 60)
    print("YouTube Video Downloader - Setup")
    print("=" * 60)
    print()

    print("1. Creating environment configuration...")
    if not create_env_file():
        return

    print("\n2. Creating necessary directories...")
    create_directories()

    print("\n" + "=" * 60)
    print("Setup Complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Edit .env file to add Google OAuth credentials (optional)")
    print("2. Install ffmpeg if not already installed")
    print("3. Run: python main.py")
    print()
    print("For OAuth setup instructions, see README.md")
    print()


if __name__ == "__main__":
    main()
