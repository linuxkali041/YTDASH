"""
Automatic YouTube Cookie Getter - Uses Your Existing Browser!
Works with Chrome, Edge, Brave, or any Chromium-based browser.
"""

import sys
import subprocess
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from database import SessionLocal
from models import YouTubeCredential, User
from auth.cookie_manager import CookieManager
from config import settings

def find_browser():
    """Find installed Chromium-based browser."""
    browsers = {
        'Chrome': [
            Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
            Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
        ],
        'Brave': [
            Path(r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"),
            Path(r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe"),
        ],
        'Edge': [
            Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
            Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
        ],
        'Chromium': [
            Path(r"C:\Program Files\Chromium\Application\chrome.exe"),
            Path(r"C:\Program Files (x86)\Chromium\Application\chrome.exe"),
        ]
    }
    
    for name, paths in browsers.items():
        for path in paths:
            if path.exists():
                return name, str(path)
    
    return None, None

def get_youtube_cookies_auto():
    """
    Automatically get YouTube cookies using your existing browser.
    """
    print("\n" + "=" * 60)
    print("🍪 Automatic YouTube Cookie Getter (Using Your Browser!)")
    print("=" * 60)
    
    # Find browser
    browser_name, browser_path = find_browser()
    
    if not browser_path:
        print("\n❌ No Chromium-based browser found!")
        print("Please install Chrome, Brave, or Edge")
        return
    
    print(f"\n✅ Found: {browser_name}")
    print(f"   Location: {browser_path}")
    
    # Check if playwright is installed
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("\n❌ Playwright not installed!")
        print("Installing Playwright...")
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "playwright"], check=True)
        print("✅ Playwright installed! Please run this script again.")
        return
    
    db = SessionLocal()
    
    try:
        # Get username
        print("\n📝 Setup")
        username = input("Enter your app username (default: admin): ").strip() or "admin"
        
        user = db.query(User).filter(User.username == username).first()
        if not user:
            print(f"❌ User '{username}' not found!")
            return
        
        print(f"✅ User: {user.username}")
        
        # Instructions
        print("\n" + "=" * 60)
        print("INSTRUCTIONS:")
        print(f"1. Your {browser_name} browser will open")
        print("2. Go to YouTube and login if you're not already")
        print("3. After logging in, come back here and press ENTER")
        print("=" * 60)
        input("\nPress ENTER to open browser...")
        
        # Launch browser with remote debugging
        debug_port = 9222
        user_data_dir = Path.home() / "youtube_downloader_browser_data"
        user_data_dir.mkdir(exist_ok=True)
        
        print(f"\n🌐 Launching {browser_name}...")
        
        # Start browser process
        browser_process = subprocess.Popen([
            browser_path,
            f"--remote-debugging-port={debug_port}",
            f"--user-data-dir={user_data_dir}",
            "https://www.youtube.com"
        ])
        
        # Wait for browser to start
        time.sleep(3)
        
        # Connect with Playwright
        with sync_playwright() as p:
            try:
                # Connect to existing browser
                browser = p.chromium.connect_over_cdp(f"http://localhost:{debug_port}")
                contexts = browser.contexts
                
                if not contexts:
                    print("❌ No browser context found!")
                    browser_process.terminate()
                    return
                
                context = contexts[0]
                
                # Wait for user to login
                input("\n👉 Press ENTER after you've logged into YouTube...")
                
                # Extract cookies
                print("\n🍪 Extracting cookies from your browser...")
                cookies = context.cookies()
                
                if not cookies:
                    print("❌ No cookies found!")
                    browser.close()
                    browser_process.terminate()
                    return
                
                print(f"✅ Found {len(cookies)} cookies")
                
                # Convert to Netscape format
                netscape_cookies = "# Netscape HTTP Cookie File\n\n"
                
                youtube_cookies = 0
                for cookie in cookies:
                    domain = cookie.get('domain', '')
                    if 'youtube.com' in domain or 'google.com' in domain:
                        youtube_cookies += 1
                        flag = 'TRUE' if domain.startswith('.') else 'FALSE'
                        path = cookie.get('path', '/')
                        secure = 'TRUE' if cookie.get('secure', False) else 'FALSE'
                        expiration = str(int(cookie.get('expires', -1)))
                        name = cookie.get('name', '')
                        value = cookie.get('value', '')
                        
                        netscape_cookies += f"{domain}\t{flag}\t{path}\t{secure}\t{expiration}\t{name}\t{value}\n"
                
                print(f"✅ Found {youtube_cookies} YouTube/Google cookies")
                
                # Close browser
                browser.close()
                browser_process.terminate()
                
                if youtube_cookies == 0:
                    print("\n⚠️  No YouTube cookies found! Make sure you logged into YouTube.")
                    return
                
                # Initialize cookie manager
                if not settings.cookie_encryption_key:
                    print("\n⚠️  No encryption key configured!")
                    print("Generating encryption key...")
                    from cryptography.fernet import Fernet
                    encryption_key = Fernet.generate_key().decode()
                    cookie_manager = CookieManager(encryption_key)
                    
                    print(f"\n🔑 Add this to your .env file:")
                    print(f"COOKIE_ENCRYPTION_KEY={encryption_key}\n")
                else:
                    cookie_manager = CookieManager(settings.cookie_encryption_key)
                
                # Encrypt cookies
                print("🔒 Encrypting cookies...")
                encrypted_cookies = cookie_manager.encrypt_cookies(netscape_cookies)
                
                # Save to database
                existing = db.query(YouTubeCredential).filter(
                    YouTubeCredential.user_id == user.id
                ).first()
                
                if existing:
                    print("♻️  Updating credentials...")
                    existing.encrypted_cookies = encrypted_cookies
                    existing.is_valid = True
                    existing.validation_error = None
                else:
                    print("➕ Adding credentials...")
                    credential = YouTubeCredential(
                        user_id=user.id,
                        account_email=user.email,
                        account_name=f"{user.username}'s YouTube",
                        encrypted_cookies=encrypted_cookies,
                        is_valid=True
                    )
                    db.add(credential)
                
                db.commit()
                
                print("\n" + "=" * 60)
                print("✅ SUCCESS! YouTube cookies saved from your browser!")
                print("=" * 60)
                print("\n🎉 You can now download videos!")
                print(f"💡 Using cookies from: {browser_name}")
                
            except Exception as e:
                print(f"\n❌ Error connecting to browser: {e}")
                browser_process.terminate()
                raise
                
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    get_youtube_cookies_auto()
