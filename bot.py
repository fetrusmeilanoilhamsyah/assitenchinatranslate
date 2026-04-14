#!/usr/bin/env python3
"""
Personal Translator Assistant Bot
Commands: /t (translate reply to ID), /c (translate to CN and send)
"""

import logging
import asyncio
import sys
from datetime import datetime
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)
from deep_translator import GoogleTranslator, MyMemoryTranslator
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

# Simple in-memory translation cache: {(text, target_lang): result}
_translation_cache: dict = {}
CACHE_MAX_SIZE = 200  # max entries to avoid memory bloat


def is_admin(user_id: int) -> bool:
    """Check if user is authorized."""
    return user_id in Config.ADMIN_IDS


async def _auto_delete(bot, chat_id: int, *message_ids: int, delay: int = 10):
    """Background task: delete messages after a delay. Non-blocking."""
    await asyncio.sleep(delay)
    for msg_id in message_ids:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=msg_id)
        except Exception as e:
            logger.debug(f"Auto-delete skipped (msg {msg_id}): {e}")


def _get_from_cache(text: str, target: str):
    """Retrieve cached translation if available."""
    return _translation_cache.get((text, target))


def _set_cache(text: str, target: str, result: str):
    """Store translation in cache. Evict oldest entry if full."""
    if len(_translation_cache) >= CACHE_MAX_SIZE:
        oldest_key = next(iter(_translation_cache))
        del _translation_cache[oldest_key]
    _translation_cache[(text, target)] = result


def _translate_sync(text: str, target: str) -> str:
    """
    Perform translation with automatic fallback:
    1. Try Google Translate
    2. Fall back to MyMemory if Google fails
    """
    # Step 1: Try Google Translate
    try:
        result = GoogleTranslator(source='auto', target=target).translate(text)
        if result and result.strip():
            return result.strip()
    except Exception as e:
        logger.warning(f"Google Translate failed: {e}. Trying MyMemory...")

    # Step 2: Fallback to MyMemory
    try:
        # MyMemory uses different lang codes for Chinese
        my_memory_target = 'zh-CN' if target == 'zh-CN' else target
        result = MyMemoryTranslator(source='auto', target=my_memory_target).translate(text)
        if result and result.strip():
            return result.strip()
    except Exception as e:
        logger.warning(f"MyMemory also failed: {e}")

    raise Exception("All translation providers failed.")


async def _smart_translate(text: str, target: str) -> str:
    """
    Full translation pipeline:
    1. Check cache
    2. Try translation with retries
    3. Store result in cache
    """
    # Check cache first
    cached = _get_from_cache(text, target)
    if cached:
        logger.info(f"Cache hit for target={target}")
        return cached

    # Retry loop (up to 3 attempts)
    last_exception = None
    for attempt in range(3):
        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(_translate_sync, text, target),
                timeout=Config.TRANSLATION_TIMEOUT
            )
            # Store in cache and return
            _set_cache(text, target, result)
            return result
        except asyncio.TimeoutError:
            last_exception = Exception("Translation timed out.")
            logger.warning(f"Attempt {attempt + 1}: translation timed out.")
        except Exception as e:
            last_exception = e
            logger.warning(f"Attempt {attempt + 1} failed: {e}")

        if attempt < 2:
            await asyncio.sleep(0.5)  # Short pause before retry

    raise last_exception


# ==================== COMMAND HANDLERS ====================

@error_handler
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command (Admin only)"""
    user = update.effective_user
    if not is_admin(user.id):
        return

    stats['total_users'] = stats.get('total_users', 0) + 1
    stats['last_activity'] = datetime.now().isoformat()
    save_stats(stats)

    await update.message.reply_text(
        "Personal Translator Assistant Ready.\n\n"
        "Commands:\n"
        "/t [reply] - Translate replied message to Indonesian.\n"
        "/c <text>  - Translate to Chinese and send."
    )


@error_handler
@rate_limit_check
async def command_t(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Translate replied message to Indonesian"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return

    # Must be a reply to a message
    reply = update.message.reply_to_message
    source_text = (reply.text or reply.caption or "").strip() if reply else ""

    if not reply or not source_text:
        await update.message.reply_text("[Error] Balas sebuah pesan teks dengan /t.")
        return

    if len(source_text) > Config.MAX_TEXT_LENGTH:
        await update.message.reply_text(f"[Error] Teks terlalu panjang (maks {Config.MAX_TEXT_LENGTH} karakter).")
        return

    await update.message.chat.send_action('typing')

    try:
        result = await _smart_translate(source_text, 'id')

        sent_message = await context.bot.send_message(
            chat_id=update.message.chat_id,
            text=result,
            reply_to_message_id=reply.message_id,       # Quote pesan China asli
            allow_sending_without_reply=True             # Tetap kirim walau reply gagal
        )

        stats['total_translations'] = stats.get('total_translations', 0) + 1
        save_stats(stats)

        # Non-blocking auto-delete: command message + translation after 10 seconds
        asyncio.create_task(_auto_delete(
            context.bot,
            update.message.chat_id,
            sent_message.message_id,
            update.message.message_id,
            delay=10
        ))

    except asyncio.TimeoutError:
        logger.warning(f"Translation timed out for user {user_id}")
        await update.message.reply_text("[Error] Waktu habis. Coba lagi.")
    except Exception as e:
        logger.error(f"Translation error (user {user_id}): {e}")
        await update.message.reply_text("[Error] Gagal menerjemahkan. Coba lagi.")


@error_handler
@rate_limit_check
async def command_c(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Translate text to Chinese, delete user's message, and send translated version."""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return

    if not context.args:
        return

    source_text = " ".join(context.args)
    if len(source_text) > Config.MAX_TEXT_LENGTH:
        await update.message.reply_text(f"[Error] Teks terlalu panjang (maks {Config.MAX_TEXT_LENGTH} karakter).")
        return

    await update.message.chat.send_action('typing')

    # Delete user's original /c message immediately
    try:
        await context.bot.delete_message(
            chat_id=update.message.chat_id,
            message_id=update.message.message_id
        )
    except Exception as e:
        logger.warning(f"Could not delete /c command message (needs Admin rights): {e}")

    try:
        result = await _smart_translate(source_text, 'zh-CN')

        # Jika /c dipakai sambil reply ke seseorang, kirim sebagai balasan ke pesan mereka
        reply_to = update.message.reply_to_message
        reply_msg_id = reply_to.message_id if reply_to else None

        await context.bot.send_message(
            chat_id=update.message.chat_id,
            text=result,
            reply_to_message_id=reply_msg_id,
            allow_sending_without_reply=True
        )

        stats['total_translations'] = stats.get('total_translations', 0) + 1
        save_stats(stats)

    except asyncio.TimeoutError:
        logger.warning(f"Translation timed out for user {user_id}")
        await context.bot.send_message(
            chat_id=update.message.chat_id,
            text="[Error] Waktu habis. Coba lagi."
        )
    except Exception as e:
        logger.error(f"Translation error (user {user_id}): {e}")
        await context.bot.send_message(
            chat_id=update.message.chat_id,
            text="[Error] Gagal menerjemahkan. Coba lagi."
        )


async def global_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Global error handler to prevent crashes."""
    logger.error(f"Unhandled error: {context.error}", exc_info=context.error)


def shutdown_handler(signum, frame):
    logger.info(f"Received signal {signum}, shutting down...")
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

    logger.info("Bot started. Personal assistant mode active.")
    application.run_polling(drop_pending_updates=True, close_loop=False)


if __name__ == '__main__':
    main()
