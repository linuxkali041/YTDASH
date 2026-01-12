"""
Helper script to add YouTube cookies to the database.
This allows authenticated video downloads without bot detection.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from database import SessionLocal
from models import YouTubeCredential, User
from auth.cookie_manager import CookieManager
from config import settings

def add_youtube_cookies():
    """Add YouTube cookies for a user."""
    db = SessionLocal()
    
    try:
        # Get admin user (or you can specify username)
        print("\n=== Add YouTube Cookies ===\n")
        username = input("Enter your username (default: admin): ").strip() or "admin"
        
        user = db.query(User).filter(User.username == username).first()
        if not user:
            print(f"❌ User '{username}' not found!")
            return
        
        print(f"✅ Found user: {user.username} ({user.email})")
        
        # Get cookies file path
        cookies_file = input("\nEnter path to cookies.txt file: ").strip()
        
        if not Path(cookies_file).exists():
            print(f"❌ File not found: {cookies_file}")
            return
        
        # Read cookies
        print(f"\n📂 Reading cookies from: {cookies_file}")
        with open(cookies_file, 'r', encoding='utf-8') as f:
            cookies_content = f.read()
        
        # Initialize cookie manager
        if not settings.cookie_encryption_key:
            print("⚠️  WARNING: No encryption key configured!")
            print("Generating temporary encryption key...")
            from cryptography.fernet import Fernet
            encryption_key = Fernet.generate_key().decode()
            cookie_manager = CookieManager(encryption_key)
            print(f"\n🔑 Add this to your .env file:")
            print(f"COOKIE_ENCRYPTION_KEY={encryption_key}\n")
        else:
            cookie_manager = CookieManager(settings.cookie_encryption_key)
        
        # Encrypt cookies
        encrypted_cookies = cookie_manager.encrypt_cookies(cookies_content)
        
        # Check if credential already exists
        existing = db.query(YouTubeCredential).filter(
            YouTubeCredential.user_id == user.id
        ).first()
        
        if existing:
            print(f"\n♻️  Updating existing YouTube credentials...")
            existing.encrypted_cookies = encrypted_cookies
            existing.is_valid = True
            existing.validation_error = None
        else:
            print(f"\n➕ Adding new YouTube credentials...")
            credential = YouTubeCredential(
                user_id=user.id,
                account_email=user.email,
                account_name=f"{user.username}'s YouTube",
                encrypted_cookies=encrypted_cookies,
                is_valid=True
            )
            db.add(credential)
        
        db.commit()
        
        print("\n" + "=" * 50)
        print("✅ SUCCESS! YouTube cookies added!")
        print("=" * 50)
        print("\nYou can now download videos without bot detection!")
        print("The app will automatically use these cookies for downloads.")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    add_youtube_cookies()
