import os
import sqlite3
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
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

# Constants and Configuration
LEAVING_BLESSING = 1
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
WEDDING_INFO = {
    "date": "ሚያዝያ 26 2017",
    "venue": "Program የት አንደሚደረግ እስካሁን ምንም መረጃ የለም! ነገር ግን በቅርቡ Update እናረጎታለን😊",
    "location": " ይህ ደብረዘይት የሚገኘው ቤቱ ነው!  https://maps.app.goo.gl/pZo4yuWB9gDPhikC8"
}

# HTTP Server for Render
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot is running!  yonas woldeyohannis and his favor    ")

def run_http_server():
    server = HTTPServer(("0.0.0.0", 10000), HealthCheckHandler)
    print("HTTP server running on port 10000")
    server.serve_forever()

# Database Functions
def init_db():
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
    user = update.effective_user
    print(f"[{datetime.now()}] User: {user.first_name} (@{user.username}, ID: {user.id}) -> {message}")
    conn = sqlite3.connect('wedding_bot.db')
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO chats (user_id, message, timestamp) VALUES (?, ?, ?)',
        (user.id, message, datetime.now())
    )
    conn.commit()
    conn.close()

# Bot Command Handlers
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
    if update.effective_user.id != 5873042615:
        await update.message.reply_text("⛔ You don't have permission to export blessings.")
        return
    conn = sqlite3.connect('wedding_bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT message FROM chats WHERE message != ""')
    blessings = cursor.fetchall()
    conn.close()
    with open("blessings.txt", "w", encoding="utf-8") as file:
        for blessing in blessings:
            file.write(f"{blessing[0]}\n\n")
    with open("blessings.txt", "rb") as file:
        await update.message.reply_document(file, caption="Here are all the blessings! 💌")

async def handle_blessing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text
    log_message(update, f"Blessing: {message}")
    await update.message.reply_text(" ለመልካም ምኞቶ እና ባርኮት አጅግ አናመሰግናለን 💖 Thank you for your blessing! It means a lot to us.መልክቶት ለባለ ትዳሮቹ ሳይሸራረፍ እናደርሳለን❤️")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    log_message(update, f"Clicked: {query.data}")
    
    if query.data == "info_date":
        text = f"📅 Date: {WEDDING_INFO['date']}\n🏨 Venue: {WEDDING_INFO['venue']}"
        await context.bot.send_message(chat_id=query.message.chat_id, text=text)
    elif query.data == "info_location":
        await context.bot.send_message(chat_id=query.message.chat_id, text=f"📍 Location: {WEDDING_INFO['location']}")
    elif query.data == "view_photos":
        os.makedirs("photos", exist_ok=True)
        photos = [f for f in os.listdir("photos") if f.endswith(('.jpg', '.png', '.jpeg'))]
        if not photos:
            await context.bot.send_message(chat_id=query.message.chat_id, text="📸 No photos yet.")
            return
        for photo in photos:
            with open(f"photos/{photo}", "rb") as p:
                await context.bot.send_photo(chat_id=query.message.chat_id, photo=InputFile(p))
    elif query.data == "countdown":
        wedding_day = datetime(2025, 5, 4)
        now = datetime.now()
        diff = wedding_day - now
        days = diff.days
        hours, remainder = divmod(diff.seconds, 3600)
        minutes = remainder // 60
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=f"⏳ እእእ..🙄🙄የቀረው {days} ቀን, {hours} ሰአት, እና {minutes} ደቂቃ ነው😁😁 አይ ግን የምር እንደዛ ነው! 💍"
        )
    elif query.data == "dress_code":
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="👗 Dress code:\nወንዶች: እባካችሁን በድንብ ልበሱ!! እና ደሞ ሱፍ ቢሆን ይመረጣል🥸..\nሴቶች:ወይዛዝርት ደሞ ቆንጀት ብላቹ ኑ። ግን ከሙሽራዋ በላይ መዋብ በጥብቅ የተከለከለ ነው-(for the sake of🙄😅)። እና ደሞ የሀገር ልብስ ካለበሳቹ  ምንም አትሰሩም! አትምጡ😡--\n✨"
        )
        
    elif query.data == "leave_blessing":
        await context.bot.send_message(chat_id=query.message.chat_id, text="💬 እባክዎን ምኝትዎን ይጻፉልን:")
        return LEAVING_BLESSING
    await query.edit_message_reply_markup(reply_markup=query.message.reply_markup)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log_message(update, "📸 Uploaded a photo")
    os.makedirs("photos", exist_ok=True)
    photo = await update.message.photo[-1].get_file()
    filename = f"photos/{update.message.photo[-1].file_id}.jpg"
    await photo.download_to_drive(filename)
    await update.message.reply_text("✅ ምስሉን ተቀብለናል.ወደ ምስል ዝርዝር ውስጥ አሁኑኑ እንጨምረዋለን።ለማረጋገጥ ደግምው 'view photo' የሚለውን ይንኩ። አናመሰግናለን!😊😊 ")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    print(f"⚠️ Error: {context.error}")
    if isinstance(update, Update) and update.message:
        await update.message.reply_text("Oops! Something went wrong.")

# Main Application
def main():
    init_db()
    http_thread = threading.Thread(target=run_http_server)
    http_thread.daemon = True
    http_thread.start()
    
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("export", export_blessings))
    
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler)],
        states={LEAVING_BLESSING: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_blessing)]},
        fallbacks=[],
        allow_reentry=True
    )
    
    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_error_handler(error_handler)
    
    print("🤖 Bot running with HTTP server! Press Ctrl+C to stop.")
    app.run_polling()

if __name__ == "__main__":
    main()