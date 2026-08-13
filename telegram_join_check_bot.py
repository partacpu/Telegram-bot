"""
Telegram bot that requires users to join a channel before using it.

Setup:
1. pip install python-telegram-bot --upgrade
2. Create your bot with @BotFather, get the BOT_TOKEN.
3. Create/have a channel, get its @username or numeric chat_id (e.g. -1001234567890).
4. IMPORTANT: Add your bot as an ADMIN of the channel (it needs admin rights
   to check membership status of other users via get_chat_member).
5. Fill in BOT_TOKEN and CHANNEL_ID below.
6. Run: python telegram_join_check_bot.py
"""

import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatMemberStatus
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ---------------- CONFIG ----------------
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
CHANNEL_ID = os.environ.get("CHANNEL_ID", "@your_channel_username")   # or numeric id like -1001234567890
CHANNEL_INVITE_LINK = os.environ.get("CHANNEL_INVITE_LINK", "https://t.me/your_channel_username")  # link shown to users
# -----------------------------------------

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Statuses that count as "joined"
JOINED_STATUSES = {
    ChatMemberStatus.MEMBER,
    ChatMemberStatus.ADMINISTRATOR,
    ChatMemberStatus.OWNER,
}


async def is_user_member(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check whether the user is currently a member of CHANNEL_ID."""
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in JOINED_STATUSES
    except Exception as e:
        # Common cause: bot isn't admin in the channel, or user never started a chat with the bot
        logger.warning(f"Membership check failed for user {user_id}: {e}")
        return False


def join_prompt_markup() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_INVITE_LINK)],
        [InlineKeyboardButton("✅ I've Joined", callback_data="check_membership")],
    ]
    return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if await is_user_member(user_id, context):
        await update.message.reply_text(
            "✅ خوش آمدید! شما عضو کانال هستید — حالا می‌توانید از ربات استفاده کنید.\n\n"
            "برای دیدن قابلیت‌ها /help را بزنید."
        )
    else:
        await update.message.reply_text(
            "🚫 برای استفاده از این ربات، ابتدا باید عضو کانال ما شوید.\n\n"
            "۱. روی دکمه زیر بزنید و عضو شوید.\n"
            "۲. سپس روی '✅ عضو شدم' بزنید تا ادامه دهید.",
            reply_markup=join_prompt_markup(),
        )


async def check_membership_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()  # stop the loading spinner on the button

    if await is_user_member(user_id, context):
        await query.edit_message_text("✅ Thanks for joining! You can now use the bot. Try /help.")
    else:
        await query.answer(
            "❌ You haven't joined yet. Please join the channel first.",
            show_alert=True,
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_user_member(user_id, context):
        await update.message.reply_text(
            "🚫 Please join our channel first with /start.",
        )
        return
    await update.message.reply_text(
        "Here's what I can do:\n"
        "/start - Check membership / restart\n"
        "/help - Show this help message"
    )


async def gate_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Runs on any normal text message; blocks non-members from using the bot."""
    user_id = update.effective_user.id
    if await is_user_member(user_id, context):
        await update.message.reply_text(f"You said: {update.message.text}")
    else:
        await update.message.reply_text(
            "🚫 You need to join our channel before using this bot.",
            reply_markup=join_prompt_markup(),
        )


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(check_membership_callback, pattern="^check_membership$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, gate_all_messages))

    logger.info("Bot started. Press Ctrl+C to stop.")
    app.run_polling()


if __name__ == "__main__":
    main()
