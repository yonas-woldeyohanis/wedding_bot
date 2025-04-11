import os
import sqlite3
import logging
import asyncio # Added for running async main
import traceback # Added for better error logging
from datetime import datetime
# Removed: from http.server import BaseHTTPRequestHandler, HTTPServer
# Removed: import threading
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import (
    Application,
    CommandHandler,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from dotenv import load_dotenv

# --- Constants and Configuration ---
LEAVING_BLESSING = 1
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
# !!! IMPORTANT: Add this to your .env file and Render Environment Variables !!!
WEBHOOK_URL = os.getenv("WEBHOOK_URL") # e.g., https://your-app-name.onrender.com
PORT = int(os.getenv("PORT", 10000)) # Render sets PORT env var, default to 10000
ADMIN_USER_ID = 5873042615 # Consider moving this to .env too

WEDDING_INFO = {
    "date": "ሚያዝያ 26 2017",
    "venue": "Program የት አንደሚደረግ እስካሁን ምንም መረጃ የለም! ነገር ግን በቅርቡ Update እናረጎታለን😊",
    "location": " ይህ ደብረዘይት የሚገኘው ቤቱ ነው!  https://maps.app.goo.gl/pZo4yuWB9gDPhikC8"
}

# --- Logging Setup ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Removed HTTP Server Section ---
# The HealthCheckHandler class and run_http_server function are removed.
# PTB's built-in webhook server will handle requests.

# --- Database Functions (Unchanged) ---
def init_db():
    # ... (same as before)
    conn = sqlite3.connect('wedding_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            message TEXT,
            timestamp DATETIME
        )
    ''')
    conn.commit()
    conn.close()

def log_message(update: Update, message: str):
    # ... (same as before, but using logger)
    user = update.effective_user
    log_entry = f"User: {user.first_name} (@{user.username}, ID: {user.id}) -> {message}"
    logger.info(log_entry)
    # Database logging remains the same
    conn = sqlite3.connect('wedding_bot.db')
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO chats (user_id, message, timestamp) VALUES (?, ?, ?)',
        (user.id, message, datetime.now())
    )
    conn.commit()
    conn.close()

# --- Bot Command Handlers (Mostly Unchanged) ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log_message(update, "/start")
    keyboard = [
        [InlineKeyboardButton("🗕 Date & Venue", callback_data="info_date")],
        [InlineKeyboardButton("📍 Location", callback_data="info_location")],
        [InlineKeyboardButton("📸 View Photos", callback_data="view_photos")],
        [InlineKeyboardButton("⏳ Countdown to the ሰርግ", callback_data="countdown")],
        [InlineKeyboardButton("👗 Dress Code Info", callback_data="dress_code")],
        [InlineKeyboardButton("📝 Leave a Blessing", callback_data="leave_blessing")]
    ]
    await update.message.reply_text(
        """👋 hey,ሰላም አንደምን ኖት? በመጀመርያ ወደ Dr. ታምራት አያሌው እና ከአርያም ሀይሌ ሰርግ ላይ ሊታደሙ በጎ ፈቃድዎ ስለሆነ እጅግ በጣም THANK YOU ማለት አንፈልጋለን😊😊😊😊-----በቀጣይነት ምርጫዎትን ይንኩ!""",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def export_blessings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_USER_ID:
        await update.message.reply_text("⛔ You don't have permission to export blessings.")
        return
    logger.info(f"Admin {update.effective_user.id} requested export.")
    conn = sqlite3.connect('wedding_bot.db')
    cursor = conn.cursor()
    # Consider refining this query if you only want actual blessings
    cursor.execute('SELECT user_id, message, timestamp FROM chats WHERE message LIKE "Blessing:%" OR callback_query = "leave_blessing"') # Example refinement
    # Or keep original: cursor.execute('SELECT message FROM chats WHERE message != ""')
    blessings_data = cursor.fetchall()
    conn.close()

    if not blessings_data:
        await update.message.reply_text("No blessings found to export.")
        return

    filename = "blessings_export.txt"
    with open(filename, "w", encoding="utf-8") as file:
        for row in blessings_data:
             # Adjust format based on your SELECT query
             # Example if selecting user_id, message, timestamp:
             # file.write(f"User ID: {row[0]} ({row[2]})\nMessage: {row[1]}\n\n")
             # If using original query:
             file.write(f"{row[0]}\n\n") # Assuming original 'SELECT message...'

    try:
        with open(filename, "rb") as file:
            await update.message.reply_document(file, caption="Here are the exported blessings! 💌")
    except Exception as e:
        logger.error(f"Failed to send blessings file: {e}")
        await update.message.reply_text("Error exporting blessings.")
    finally:
        if os.path.exists(filename):
            os.remove(filename) # Clean up the temporary file

async def handle_blessing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text
    log_message(update, f"Blessing: {message}") # Log the actual blessing text
    await update.message.reply_text(" ለመልካም ምኞቶ እና ባርኮት አጅግ አናመሰግናለን 💖 Thank you for your blessing! It means a lot to us.መልክቶት ለባለ ትዳሮቹ ሳይሸራረፍ እናደርሳለን❤️")
    return ConversationHandler.END # Explicitly end the conversation

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    # Log the callback data itself
    log_message(update, f"Callback Query: {query.data}")

    if query.data == "info_date":
        text = f"📅 Date: {WEDDING_INFO['date']}\n🏨 Venue: {WEDDING_INFO['venue']}"
        await context.bot.send_message(chat_id=query.message.chat_id, text=text)
    elif query.data == "info_location":
        await context.bot.send_message(chat_id=query.message.chat_id, text=f"📍 Location: {WEDDING_INFO['location']}")
    elif query.data == "view_photos":
        photo_dir = "photos"
        os.makedirs(photo_dir, exist_ok=True)
        try:
            photos = [f for f in os.listdir(photo_dir) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
            if not photos:
                await context.bot.send_message(chat_id=query.message.chat_id, text="📸 No photos available yet.")
                return

            # Consider sending photos in batches if there are many
            sent_count = 0
            for photo_name in photos:
                photo_path = os.path.join(photo_dir, photo_name)
                try:
                    with open(photo_path, "rb") as p:
                        await context.bot.send_photo(chat_id=query.message.chat_id, photo=InputFile(p))
                    sent_count += 1
                    # Optional: Add a small delay if hitting rate limits
                    # await asyncio.sleep(0.5)
                except Exception as e:
                    logger.error(f"Failed to send photo {photo_name}: {e}")
            if sent_count == 0 and photos: # Handle case where all sends failed
                 await context.bot.send_message(chat_id=query.message.chat_id, text="📸 Could not send photos due to an error.")

        except Exception as e:
            logger.error(f"Error accessing photos directory: {e}")
            await context.bot.send_message(chat_id=query.message.chat_id, text="📸 Error retrieving photos.")

    elif query.data == "countdown":
        try:
            # Note: Ensure this date calculation remains correct for the Ethiopian Calendar date
            wedding_day = datetime(2025, 5, 4, 0, 0, 0) # Set time to midnight for clearer countdown
            now = datetime.now()
            if now >= wedding_day:
                await context.bot.send_message(chat_id=query.message.chat_id, text="🎉 The wedding day is here or has passed!")
            else:
                diff = wedding_day - now
                days = diff.days
                hours, remainder = divmod(diff.seconds, 3600)
                minutes = remainder // 60
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=f"⏳ እእእ..🙄🙄የቀረው {days} ቀን, {hours} ሰአት, እና {minutes} ደቂቃ ነው😁😁 አይ ግን የምር እንደዛ ነው! 💍"
                )
        except Exception as e:
            logger.error(f"Error calculating countdown: {e}")
            await context.bot.send_message(chat_id=query.message.chat_id, text="⏳ Error calculating countdown.")

    elif query.data == "dress_code":
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="👗 Dress code:\nወንዶች: እባካችሁን በድንብ ልበሱ!! እና ደሞ ሱፍ ቢሆን ይመረጣል🥸..\nሴቶች:ወይዛዝርት ደሞ ቆንጀት ብላቹ ኑ። ግን ከሙሽራዋ በላይ መዋብ በጥብቅ የተከለከለ ነው-(for the sake of🙄😅)። እና ደሞ የሀገር ልብስ ካለበሳቹ  ምንም አትሰሩም! አትምጡ😡--\n✨"
        )

    elif query.data == "leave_blessing":
        await context.bot.send_message(chat_id=query.message.chat_id, text="💬 እባክዎን ምኝትዎን ይጻፉልን:")
        return LEAVING_BLESSING # Enter the blessing state

    # Don't edit message reply markup here for webhook, let the state handle it or send new messages
    # await query.edit_message_reply_markup(reply_markup=query.message.reply_markup) # Removed


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log_message(update, "📸 Received a photo")
    photo_dir = "photos"
    os.makedirs(photo_dir, exist_ok=True)
    try:
        photo_file = await update.message.photo[-1].get_file()
        # Use a more unique filename if needed, e.g., including user_id or timestamp
        filename = os.path.join(photo_dir, f"{photo_file.file_id}.jpg")
        await photo_file.download_to_drive(filename)
        logger.info(f"Photo saved to {filename}")
        await update.message.reply_text("✅ ምስሉን ተቀብለናል. ወደ ምስል ዝርዝር ውስጥ አሁኑኑ እንጨምረዋለን። ለማረጋገጥ ደግምው 'view photo' የሚለውን ይንኩ። አናመሰግናለን!😊😊 ")
    except Exception as e:
        logger.error(f"Failed to download/save photo: {e}")
        await update.message.reply_text("❌ Sorry, there was an error saving the photo.")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Log the error and send a telegram message to notify the developer."""
    logger.error(f"Exception while handling an update: {context.error}", exc_info=context.error)

    # Optionally traceback.format_exception... but avoid sending full tracebacks to users
    # tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    # tb_string = "".join(tb_list)
    # logger.error(tb_string) # Log the full traceback

    # Send simplified error message to the user if possible
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text("😟 Oops! Something went wrong processing your request. Please try again later.")
        except Exception as e:
            logger.error(f"Failed to send error message to user: {e}")

# --- Main Application ---
async def main():
    if not TOKEN:
        logger.critical("BOT_TOKEN environment variable not found!")
        return
    if not WEBHOOK_URL:
        logger.critical("WEBHOOK_URL environment variable not found!")
        return

    init_db()

    # Use TOKEN as a secret path segment for the webhook
    # IMPORTANT: Make sure this path is kept secret and not easily guessable if TOKEN is public
    secret_path = TOKEN

    app = Application.builder().token(TOKEN).build()

    # --- Add Handlers ---
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("export", export_blessings))

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="^leave_blessing$")], # Make pattern specific
        states={
            LEAVING_BLESSING: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_blessing)]
        },
        fallbacks=[CommandHandler("start", start)], # Allow restarting convo with /start
        # No allow_reentry needed if conversation ends properly
    )

    # Handler for other buttons that don't start conversations
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^(info_date|info_location|view_photos|countdown|dress_code)$"))

    # Handler for photos outside conversations
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    # Error handler
    app.add_error_handler(error_handler)

    # --- Set up Webhook ---
    logger.info(f"Setting webhook for URL: {WEBHOOK_URL}/{secret_path}")
    try:
        await app.bot.set_webhook(url=f"{WEBHOOK_URL}/{secret_path}", allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.critical(f"Failed to set webhook: {e}")
        return

    # --- Run Webhook Server ---
    # PTB's run_webhook includes a /health endpoint by default for health checks
    logger.info(f"Starting webhook listener on 0.0.0.0:{PORT}")
    await app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=secret_path, # The secret path Telegram will POST updates to
        # webhook_url parameter here is not strictly needed as we set it above
    )

    logger.info("Bot webhook server finished.") # This line might not be reached if run_webhook runs forever

if __name__ == "__main__":
    # Use asyncio.run() to execute the async main function
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped manually.")
    except Exception as e:
        logger.critical(f"Application failed to start or crashed: {e}", exc_info=True)