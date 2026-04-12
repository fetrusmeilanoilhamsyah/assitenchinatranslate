"""
Configuration for Translator Bot
All settings in one place
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Bot configuration"""
    
    # Bot settings
    BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
    
    # Rate limiting
    RATE_LIMIT_SECONDS = int(os.getenv('RATE_LIMIT_SECONDS', '2'))
    RATE_LIMIT_CLEANUP = int(os.getenv('RATE_LIMIT_CLEANUP', '300'))  # 5 min cleanup
    
    # Translation settings
    MAX_TEXT_LENGTH = int(os.getenv('MAX_TEXT_LENGTH', '1000'))
    TRANSLATION_TIMEOUT = int(os.getenv('TRANSLATION_TIMEOUT', '10'))
    
    # Paths
    BASE_DIR = Path(__file__).parent
    LOG_DIR = BASE_DIR / 'logs'
    DATA_DIR = BASE_DIR / 'data'
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE = LOG_DIR / 'bot.log'
    
    # Stats file
    STATS_FILE = DATA_DIR / 'stats.json'
    
    # Create directories if not exist
    LOG_DIR.mkdir(exist_ok=True)
    DATA_DIR.mkdir(exist_ok=True)
    
    # Admin settings (optional)
    ADMIN_IDS = [int(x) for x in os.getenv('ADMIN_IDS', '').split(',') if x.strip()]
    
    @classmethod
    def validate(cls):
        """Validate configuration"""
        errors = []
        
        if not cls.BOT_TOKEN or cls.BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
            errors.append("BOT_TOKEN is not set")
        
        if cls.RATE_LIMIT_SECONDS < 1:
            errors.append("RATE_LIMIT_SECONDS must be >= 1")
        
        if cls.MAX_TEXT_LENGTH < 100 or cls.MAX_TEXT_LENGTH > 4096:
            errors.append("MAX_TEXT_LENGTH must be between 100-4096")
        
        return errors
