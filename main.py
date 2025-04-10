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
        self.wfile.write("""Bot is running!      \n Made Alive in Christ
2 As for you, you were dead in your transgressions and sins, 2 in which you used to live when you followed the ways of this world and of the ruler of the kingdom of the air, the spirit who is now at work in those who are disobedient. 3 All of us also lived among them at one time, gratifying the cravings of our flesh[a] and following its desires and thoughts. Like the rest, we were by nature deserving of wrath. 4 But because of his great love for us, God, who is rich in mercy, 5 made us alive with Christ even when we were dead in transgressions—it is by grace you have been saved. 6 And God raised us up with Christ and seated us with him in the heavenly realms in Christ Jesus, 7 in order that in the coming ages he might show the incomparable riches of his grace, expressed in his kindness to us in Christ Jesus. 8 For it is by grace you have been saved, through faith—and this is not from yourselves, it is the gift of God— 9 not by works, so that no one can boast. 10 For we are God’s handiwork, created in Christ Jesus to do good works, which God prepared in advance for us to do.

Jew and Gentile Reconciled Through Christ
11 Therefore, remember that formerly you who are Gentiles by birth and called “uncircumcised” by those who call themselves “the circumcision” (which is done in the body by human hands)— 12 remember that at that time you were separate from Christ, excluded from citizenship in Israel and foreigners to the covenants of the promise, without hope and without God in the world. 13 But now in Christ Jesus you who once were far away have been brought near by the blood of Christ.

14 For he himself is our peace, who has made the two groups one and has destroyed the barrier, the dividing wall of hostility, 15 by setting aside in his flesh the law with its commands and regulations. His purpose was to create in himself one new humanity out of the two, thus making peace, 16 and in one body to reconcile both of them to God through the cross, by which he put to death their hostility. 17 He came and preached peace to you who were far away and peace to those who were near. 18 For through him we both have access to the Father by one Spirit.

19 Consequently, you are no longer foreigners and strangers, but fellow citizens with God’s people and also members of his household, 20 built on the foundation of the apostles and prophets, with Christ Jesus himself as the chief cornerstone. 21 In him the whole building is joined together and rises to become a holy temple in the Lord. 22 And in him you too are being built together to become a dwelling in which God lives by his Spirit.

Footnotes
Ephesians 2:3 In contexts like this, the Greek word for flesh (sarx) refers to the sinful state of human beings, often presented as a power in opposition to the Spirit.""")

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
        "👋 hey,ሰላም አንደምን ኖት? በመጀመርያ ወደ Dr. ታምራት አያሌው እና ከአርያም ----ሰርግ ላይ ሊታደሙ በጎ ፈቃድዎ ስለሆነ እጅግ በጣም THANK YOU ማለት አንፈልጋለን😊😊😊😊-----በቀጣይነት ምርጫዎትን ይንኩ!",
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
    await update.message.reply_text(" ለመልካም ምኞቶ እና ባርኮት አጅግ አናመሰግናለን 💖 Thank you for your blessing! It means a lot to us.")

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
    await update.message.reply_text("✅ ምስሉን ተቀብለናል.ወደ ምስል ዝርዝር ውስጥ አሁኑኑ እንጨምረዋለን።😊😊 አናመሰግናለን!")

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