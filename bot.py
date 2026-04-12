#!/usr/bin/env python3
"""
Professional Translator Bot (Personal Assistant Mode)
Support: Auto->ID, Auto->CN
"""

import logging
import asyncio
import html
import sys
from pathlib import Path
from datetime import datetime
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)
from telegram.constants import ParseMode
from deep_translator import GoogleTranslator
import signal

from config import Config
from utils import (
    setup_logging,
    RateLimiter,
    error_handler,
    save_stats,
    load_stats,
    rate_limit_check
)

# Initialize
logger = logging.getLogger(__name__)
rate_limiter = RateLimiter()
stats = load_stats()

def is_admin(user_id: int) -> bool:
    """Check if the user is authorized to use the bot."""
    return user_id in Config.ADMIN_IDS

@error_handler
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command (Admin only)"""
    user = update.effective_user
    if not is_admin(user.id):
        return

    stats['total_users'] = stats.get('total_users', 0) + 1
    stats['last_activity'] = datetime.now().isoformat()
    save_stats(stats)
    
    welcome_text = (
        "Personal Translator Assistant Ready.\n\n"
        "Commands:\n"
        "/t [in reply] - Translate message to Indonesian.\n"
        "/c <text>     - Translate to Chinese and send."
    )
    
    await update.message.reply_text(welcome_text)

@error_handler
@rate_limit_check
async def command_t(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Translate replied message to Indonesian"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return

    # Check if this is a reply
    reply = update.message.reply_to_message
    if not reply or not reply.text:
        await update.message.reply_text("[Error] Mohon balas sebuah pesan teks dengan /t.")
        return

    source_text = reply.text.strip()
    
    if len(source_text) > Config.MAX_TEXT_LENGTH:
        await update.message.reply_text(f"[Error] Teks melebihi batas {Config.MAX_TEXT_LENGTH} karakter.")
        return

    # Indicate processing
    await update.message.chat.send_action('typing')

    try:
        translator = GoogleTranslator(source='auto', target='id')
        result = await asyncio.wait_for(
            asyncio.to_thread(translator.translate, source_text),
            timeout=Config.TRANSLATION_TIMEOUT
        )
        
        # Format the response in plain text
        response_text = result
        
        await context.bot.send_message(
            chat_id=update.message.chat_id,
            text=response_text,
            reply_to_message_id=reply.message_id
        )
        
        stats['total_translations'] = stats.get('total_translations', 0) + 1
        save_stats(stats)
        
    except asyncio.TimeoutError:
        logger.warning(f"Timeout translating for user {user_id}")
        await update.message.reply_text("[Error] Waktu proses habis. Silakan coba lagi.")
    except Exception as e:
        logger.error(f"Translation error: {e}")
        await update.message.reply_text(f"[Error] Gagal menerjemahkan teks.")

@error_handler
@rate_limit_check
async def command_c(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Translate text to Chinese and replace the original user's message"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return

    if not context.args:
        # Ignore empty /c command or ask for input
        return

    # Join the arguments back to string
    source_text = " ".join(context.args)
    if len(source_text) > Config.MAX_TEXT_LENGTH:
        await update.message.reply_text(f"[Error] Teks melebihi batas {Config.MAX_TEXT_LENGTH} karakter.")
        return

    await update.message.chat.send_action('typing')

    try:
        # Delete original user message first if possible
        try:
            await context.bot.delete_message(
                chat_id=update.message.chat_id, 
                message_id=update.message.message_id
            )
        except Exception as e:
            logger.warning(f"Could not delete message. Ensure bot is group Admin with Delete rights. Err: {e}")
        
        translator = GoogleTranslator(source='auto', target='zh-CN')
        result = await asyncio.wait_for(
            asyncio.to_thread(translator.translate, source_text),
            timeout=Config.TRANSLATION_TIMEOUT
        )
        
        # Send translated text directly without quoting
        await context.bot.send_message(
            chat_id=update.message.chat_id,
            text=result
        )

        stats['total_translations'] = stats.get('total_translations', 0) + 1
        save_stats(stats)

    except asyncio.TimeoutError:
        logger.warning(f"Timeout translating for user {user_id}")
        await context.bot.send_message(
            chat_id=update.message.chat_id,
            text="[Error] Waktu proses terjemahan habis."
        )
    except Exception as e:
        logger.error(f"Translation error: {e}")
        await context.bot.send_message(
            chat_id=update.message.chat_id,
            text="[Error] Peringatan: sistem gagal memproses."
        )

async def global_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Global error handler"""
    logger.error(f"Critical error occurred: {context.error}", exc_info=context.error)

def shutdown_handler(signum, frame):
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    save_stats(stats)
    sys.exit(0)

def main():
    setup_logging()
    
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)
    
    if not Config.BOT_TOKEN or Config.BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
        logger.error("BOT_TOKEN not set!")
        sys.exit(1)
    
    if 'uptime_start' not in stats:
        stats['uptime_start'] = datetime.now().isoformat()
        save_stats(stats)
    
    logger.info("Initializing Agent Bot...")
    
    application = (
        Application.builder()
        .token(Config.BOT_TOKEN)
        .concurrent_updates(True)
        .connect_timeout(30)
        .read_timeout(30)
        .write_timeout(30)
        .build()
    )
    
    application.add_handler(CommandHandler('start', start_command))
    application.add_handler(CommandHandler('t', command_t))
    application.add_handler(CommandHandler('c', command_c))
    application.add_error_handler(global_error_handler)
    
    logger.info("Bot started directly as personal assistant.")
    application.run_polling(drop_pending_updates=True, close_loop=False)

if __name__ == '__main__':
    main()
