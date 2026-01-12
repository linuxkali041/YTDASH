
import sys
import os

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
from models.settings import AppSetting, DEFAULT_SETTINGS
from utils.logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)

def update_settings():
    db = SessionLocal()
    try:
        logger.info("Checking for missing default settings...")
        count = 0
        for default in DEFAULT_SETTINGS:
            existing = db.query(AppSetting).filter(AppSetting.key == default['key']).first()
            if not existing:
                logger.info(f"Adding missing setting: {default['key']}")
                setting = AppSetting(
                    key=default['key'],
                    value=default['value'],
                    category=default['category'],
                    description=default['description'],
                    value_type=default['value_type']
                )
                db.add(setting)
                count += 1
            else:
                # Optional: Update description or type if changed
                if existing.value_type != default['value_type']:
                     logger.info(f"Updating type for setting: {default['key']}")
                     existing.value_type = default['value_type']
                     count += 1
        
        if count > 0:
            db.commit()
            logger.info(f"Successfully added/updated {count} settings.")
        else:
            logger.info("All settings are up to date.")
            
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    update_settings()
