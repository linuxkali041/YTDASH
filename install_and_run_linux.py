"""
Automated installation and run script for Linux/macOS
This script will:
1. Check Python version
2. Create virtual environment
3. Install dependencies
4. Run setup to generate config
5. Start the application
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


def print_header(message):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {message}")
    print("=" * 70)


def print_step(step_num, message):
    """Print a formatted step."""
    print(f"\n[{step_num}] {message}")


def check_python_version():
    """Check if Python version is 3.8 or higher."""
    print_step("✓", "Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Error: Python 3.8+ required. Current version: {version.major}.{version.minor}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected")
    return True


def check_ffmpeg():
    """Check if ffmpeg is installed."""
    print_step("ℹ", "Checking for ffmpeg...")
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        print("✅ ffmpeg is installed")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  ffmpeg not found. Video merging may not work.")
        
        if platform.system() == "Darwin":
            print("   Install with: brew install ffmpeg")
        else:
            print("   Install with:")
            print("     - Ubuntu/Debian: sudo apt-get install ffmpeg")
            print("     - CentOS/RHEL: sudo yum install ffmpeg")
            print("     - Fedora: sudo dnf install ffmpeg")
        
        return False


def create_venv():
    """Create virtual environment."""
    print_step("1", "Creating virtual environment...")
    
    venv_path = Path("venv")
    if venv_path.exists():
        print("⚠️  Virtual environment already exists. Skipping creation.")
        return True
    
    try:
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("✅ Virtual environment created")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create virtual environment: {e}")
        return False


def get_venv_python():
    """Get path to Python executable in venv."""
    return str(Path("venv") / "bin" / "python")



def install_dependencies():
    """Install Python dependencies."""
    print_step("2", "Installing dependencies...")

    python_exe = get_venv_python()

    # Absolute path to requirements.txt (relative to this script)
    script_dir = Path(__file__).resolve().parent
    requirements_path = script_dir / "requirements.txt"

    if not requirements_path.exists():
        print(f"❌ requirements.txt not found: {requirements_path}")
        return False

    try:
        # Upgrade pip
        print("   Upgrading pip...")
        subprocess.run(
            [python_exe, "-m", "pip", "install", "--upgrade", "pip"],
            check=True
        )

        # Install requirements
        print("   Installing requirements...")
        subprocess.run(
            [python_exe, "-m", "pip", "install", "-r", str(requirements_path)],
            check=True
        )

        print("✅ Dependencies installed successfully")
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False


def run_setup():
    """Run setup script to generate config."""
    print_step("3", "Running setup to generate configuration...")
    
    python_exe = get_venv_python()
    env_file = Path(".env")
    
    if env_file.exists():
        print("⚠️  .env file already exists. Skipping setup.")
        return True
    
    try:
        subprocess.run([python_exe, "setup.py"], check=True)
        print("✅ Configuration generated")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Setup failed: {e}")
        return False


def init_database():
    """Initialize database and create admin user."""
    print_step("4", "Initializing database...")
    
    python_exe = get_venv_python()
    
    try:
        subprocess.run([python_exe, "init_db.py"], check=True)
        print("✅ Database initialized")
        print("\n⚠️  IMPORTANT: Save the admin credentials shown above!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Database initialization failed: {e}")
        return False


def start_application():
    """Start the FastAPI application."""
    print_step("5", "Starting application...")
    
    python_exe = get_venv_python()
    
    print("\n" + "=" * 70)
    print("  🚀 STARTING YOUTUBE DOWNLOADER")
    print("=" * 70)
    print("\n📍 Access the application at: http://localhost:8000")
    print("📍 Login page: http://localhost:8000/login")
    print("📍 Admin panel: http://localhost:8000/admin")
    print("📍 API documentation: http://localhost:8000/docs")
    print("\n⌨️  Press Ctrl+C to stop the server\n")
    print("=" * 70 + "\n")
    
    try:
        # Run the application
        subprocess.run([python_exe, "main.py"], check=True)
    except KeyboardInterrupt:
        print("\n\n" + "=" * 70)
        print("  🛑 Application stopped by user")
        print("=" * 70)
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Application crashed: {e}")
        return False
    
    return True


def main():
    """Main installation and run function."""
    print_header("YouTube Video Downloader - Linux/macOS Installer")
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Check ffmpeg (warning only)
    check_ffmpeg()
    
    # Create virtual environment
    if not create_venv():
        print("\n❌ Installation failed at virtual environment creation")
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Installation failed at dependency installation")
        sys.exit(1)
    
    # Run setup
    if not run_setup():
        print("\n❌ Installation failed at configuration setup")
        sys.exit(1)
    
    # Initialize database
    if not init_database():
        print("\n❌ Installation failed at database initialization")
        sys.exit(1)
    
    print_header("Installation Complete!")
    
    # Ask user if they want to configure OAuth
    print("\n📝 OPTIONAL: Configure OAuth for authenticated downloads")
    print("   1. Get credentials from: https://console.cloud.google.com/")
    print("   2. Edit .env file and add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET")
    print("   3. See README.md for detailed OAuth setup instructions")
    
    print("\n🎉 Your application is ready!")
    print("   - Admin Panel: http://localhost:8000/admin")
    print("   - Login Page: http://localhost:8000/login") 
    print("   - Main App: http://localhost:8000")
    
    response = input("\n🚀 Start the application now? (Y/n): ").strip().lower()
    
    if response == '' or response == 'y' or response == 'yes':
        # Start application
        start_application()
    else:
        print("\n✅ Setup complete! Run the application later with:")
        print(f"   {get_venv_python()} main.py")
        print("\n   or simply run this script again.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Installation cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
