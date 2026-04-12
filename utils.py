"""
Utility functions for Translator Bot
Rate limiting, logging, stats, etc.
"""

import logging
import time
import json
from functools import wraps
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
from telegram import Update
from telegram.ext import ContextTypes

from config import Config

# ==================== LOGGING SETUP ====================

def setup_logging():
    """Setup logging configuration"""
    # Create formatters
    file_formatter = logging.Formatter(Config.LOG_FORMAT)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Setup file handler
    file_handler = logging.FileHandler(
        Config.LOG_FILE,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    
    # Setup console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, Config.LOG_LEVEL))
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Suppress noisy loggers
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('telegram').setLevel(logging.WARNING)

# ==================== RATE LIMITER ====================

class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        self.limits: Dict[int, float] = {}
        self.last_cleanup = time.time()
    
    def check_limit(self, user_id: int) -> bool:
        """
        Check if user can make request
        Returns True if allowed, False if rate limited
        """
        current_time = time.time()
        
        # Cleanup old entries periodically
        if current_time - self.last_cleanup > Config.RATE_LIMIT_CLEANUP:
            self._cleanup()
        
        # Check user limit
        if user_id in self.limits:
            time_passed = current_time - self.limits[user_id]
            if time_passed < Config.RATE_LIMIT_SECONDS:
                return False
        
        # Update limit
        self.limits[user_id] = current_time
        return True
    
    def _cleanup(self):
        """Remove old rate limit entries"""
        current_time = time.time()
        cutoff = current_time - Config.RATE_LIMIT_CLEANUP
        
        # Remove entries older than cleanup time
        self.limits = {
            uid: ts for uid, ts in self.limits.items()
            if ts > cutoff
        }
        
        self.last_cleanup = current_time
        logging.getLogger(__name__).debug(
            f"Rate limiter cleanup: {len(self.limits)} active entries"
        )

# ==================== STATS MANAGEMENT ====================

def load_stats() -> Dict[str, Any]:
    """Load stats from file"""
    try:
        if Config.STATS_FILE.exists():
            with open(Config.STATS_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to load stats: {e}")
    
    return {
        'total_translations': 0,
        'total_users': 0,
        'uptime_start': datetime.now().isoformat(),
        'last_activity': datetime.now().isoformat()
    }

def save_stats(stats: Dict[str, Any]):
    """Save stats to file"""
    try:
        with open(Config.STATS_FILE, 'w') as f:
            json.dump(stats, f, indent=2)
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to save stats: {e}")

# ==================== DECORATORS ====================

def error_handler(func):
    """
    Decorator to catch all errors and prevent crashes
    Also logs errors for debugging
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            return await func(update, context)
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(
                f"Error in {func.__name__}: {str(e)}",
                exc_info=True
            )
            
            # Try to notify user
            try:
                if update.message:
                    await update.message.reply_text(
                        "❌ Terjadi error sementara.\n"
                        "Coba lagi dalam beberapa detik.",
                        reply_to_message_id=update.message.message_id
                    )
                elif update.callback_query:
                    await update.callback_query.answer(
                        "Error! Coba lagi.",
                        show_alert=True
                    )
            except Exception as notify_error:
                logger.error(f"Failed to notify user of error: {notify_error}")
    
    return wrapper

def rate_limit_check(func):
    """
    Decorator for rate limiting
    Note: Actual rate check is done in the handler
    This is just a marker for documentation
    """
    return func

def admin_only(func):
    """Decorator to restrict command to admins only"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        
        if Config.ADMIN_IDS and user_id not in Config.ADMIN_IDS:
            await update.message.reply_text(
                "❌ Command ini hanya untuk admin!"
            )
            return
        
        return await func(update, context)
    
    return wrapper

# ==================== HELPER FUNCTIONS ====================

def format_number(num: int) -> str:
    """Format number with thousand separators"""
    return f"{num:,}".replace(',', '.')

def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."

def get_user_info(update: Update) -> str:
    """Get formatted user info for logging"""
    user = update.effective_user
    username = f"@{user.username}" if user.username else "NoUsername"
    return f"User {user.id} ({username})"
