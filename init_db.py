"""
Database initialization and seeding.
"""

import sys
from pathlib import Path
from sqlalchemy.orm import Session
from database import engine, Base, SessionLocal
from models import User, AppSetting, DEFAULT_SETTINGS, UserRole
from auth.auth_utils import get_password_hash
import secrets
from utils.logging_config import get_logger

logger = get_logger(__name__)


def init_database():
    """Initialize database tables."""
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")


def seed_default_settings(db: Session):
    """Seed default application settings."""
    logger.info("Checking for default settings...")
    
    for setting_data in DEFAULT_SETTINGS:
        existing = db.query(AppSetting).filter(AppSetting.key == setting_data['key']).first()
        
        if not existing:
            setting = AppSetting(**setting_data)
            db.add(setting)
            logger.info(f"Added default setting: {setting_data['key']}")
    
    db.commit()
    logger.info("Default settings seeded")


def create_admin_user(db: Session) -> tuple[str, str]:
    """
    Create default admin user if none exists.
    
    Returns:
        Tuple of (username, password)
    """
    # Check if any admin user exists
    admin_exists = db.query(User).filter(User.role == UserRole.ADMIN).first()
    
    if admin_exists:
        logger.info("Admin user already exists")
        return None, None
    
    # Generate random password (limit to 16 chars to stay under bcrypt's 72 byte limit)
    password = secrets.token_urlsafe(12)[:16]  # 12 bytes -> ~16 chars, then truncate to be safe
    
    # Create admin user
    admin = User(
        username="admin",
        email="admin@localhost",
        password_hash=get_password_hash(password),
        role=UserRole.ADMIN,
        is_active=True,
        is_email_verified=True,
        storage_quota=107374182400,  # 100GB for admin
        download_limit_daily=1000,
        concurrent_downloads=10
    )
    
    db.add(admin)
    db.commit()
    db.refresh(admin)
    
    logger.info(f"Created admin user: {admin.username}")
    
    return "admin", password


def initialize_app():
    """
    Full application initialization.
    Called on first run or when database is empty.
    """
    print("=" * 70)
    print("  YouTube Downloader - Database Initialization")
    print("=" * 70)
    print()
    
    # Create tables
    print("Step 1: Creating database tables...")
    init_database()
    print("✅ Database tables created")
    print()
    
    # Create session
    db = SessionLocal()
    
    try:
        # Seed default settings
        print("Step 2: Seeding default settings...")
        seed_default_settings(db)
        print("✅ Default settings created")
        print()
        
        # Create admin user
        print("Step 3: Creating admin user...")
        username, password = create_admin_user(db)
        
        if username and password:
            print("✅ Admin user created")
            print()
            print("=" * 70)
            print("  ADMIN CREDENTIALS")
            print("=" * 70)
            print(f"  Username: {username}")
            print(f"  Password: {password}")
            print("=" * 70)
            print()
            print("⚠️  IMPORTANT: Save these credentials securely!")
            print("⚠️  Change the password after first login!")
            print()
        else:
            print("ℹ️  Admin user already exists")
            print()
        
        print("=" * 70)
        print("  Initialization Complete!")
        print("=" * 70)
        print()
        
    finally:
        db.close()


if __name__ == "__main__":
    """Run initialization from command line."""
    initialize_app()
