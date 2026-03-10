import os
import re
import json
import logging
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- FLASK SERVER FOR RENDER (Keep-Alive) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is Running!"

def run_web():
    app.run(host='0.0.0.0', port=8080)

# --- CONFIGURATION ---
TOKEN = "8767780772:AAEEL8erNKK8jc5lakgQuQS4FVaMYdK-tss"
ADMIN_IDS = [6450199112, 7117775366, 1872848003] # Add your IDs
DB_FILE = "fund_data.json"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- DATABASE FUNCTIONS ---
def load_fund():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f).get("total_fund", 0.0)
    return 0.0

def save_fund(amount):
    with open(DB_FILE, "w") as f:
        json.dump({"total_fund": amount}, f)

TOTAL_FUND = load_fund()

# Helper to escape MarkdownV2 special characters
def esc(text):
    return re.sub(r'([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', str(text))

# --- COMMANDS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    msg = f"🏦 *Dashboard Active*\n\n💰 *Current Balance:* `₹{esc(TOTAL_FUND)}`"
    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN_V2)

async def add_fund(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global TOTAL_FUND
    if update.effective_user.id not in ADMIN_IDS: return
    try:
        amount = float(context.args[0])
        TOTAL_FUND += amount
        save_fund(TOTAL_FUND)
        msg = (f"✅ *Fund Credited*\n"
               f"╼╼╼╼╼╼╼╼╼╼╼╼╼╼╼╼\n"
               f"➕ *Added:* `₹{esc(amount)}` \n"
               f"💰 *New Balance:* `₹{esc(TOTAL_FUND)}` ")
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN_V2)
    except:
        await update.message.reply_text("❌ *Usage:* `/addfund 100`", parse_mode=ParseMode.MARKDOWN_V2)

async def remove_fund(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global TOTAL_FUND
    if update.effective_user.id not in ADMIN_IDS: return
    try:
        amount = float(context.args[0])
        TOTAL_FUND -= amount
        save_fund(TOTAL_FUND)
        msg = (f"🔻 *Fund Debited*\n"
               f"╼╼╼╼╼╼╼╼╼╼╼╼╼╼╼╼\n"
               f"➖ *Removed:* `₹{esc(amount)}` \n"
               f"💰 *New Balance:* `₹{esc(TOTAL_FUND)}` ")
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN_V2)
    except:
        await update.message.reply_text("❌ *Usage:* `/removefund 100`", parse_mode=ParseMode.MARKDOWN_V2)

# --- AUTO-DETECTION ---
async def handle_payout_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global TOTAL_FUND
    msg_text = update.effective_message.text or update.effective_message.caption
    if not msg_text: return

    if "New UPI Payout Request!" in msg_text:
        match = re.search(r"Request Amount\s*:\s*₹?([\d.]+)", msg_text)
        if match:
            amount = float(match.group(1))
            TOTAL_FUND -= amount
            save_fund(TOTAL_FUND)
            
            response = (
                f"⚠️ *Payout Detected*\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"📉 *Debit Amount:* `₹{esc(amount)}` \n"
                f"💳 *Remaining:* `₹{esc(TOTAL_FUND)}` \n"
                f"━━━━━━━━━━━━━━━━━━"
            )
            await context.bot.send_message(chat_id=update.effective_chat.id, text=response, parse_mode=ParseMode.MARKDOWN_V2)

def main():
    # Keep alive thread
    Thread(target=run_web).start()

    app_bot = Application.builder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("addfund", add_fund))
    app_bot.add_handler(CommandHandler("removefund", remove_fund))
    app_bot.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_payout_msg))

    print("Bot is LIVE for Render...")
    app_bot.run_polling()

if __name__ == '__main__':
    main()
