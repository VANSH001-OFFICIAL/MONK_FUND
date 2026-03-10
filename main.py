import os
import re
import json
import logging
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# --- FLASK SERVER (Keep-Alive) ---
app = Flask('')
@app.route('/')
def home(): return "Bot is Running!"
def run_web(): app.run(host='0.0.0.0', port=8080)

# --- CONFIGURATION ---
TOKEN = "8767780772:AAEEL8erNKK8jc5lakgQuQS4FVaMYdK-tss"
ADMIN_IDS = [6450199112, 7117775366, 1872848003]
DB_FILE = "fund_data.json"

# --- DATABASE ---
def load_fund():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f: return json.load(f).get("total_fund", 0.0)
        except: return 0.0
    return 0.0

def save_fund(amount):
    with open(DB_FILE, "w") as f: json.dump({"total_fund": amount}, f)

TOTAL_FUND = load_fund()

def esc(text): return re.sub(r'([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', str(text))

# --- BUTTONS & MENU ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    
    keyboard = [
        [InlineKeyboardButton("💰 Check Balance", callback_data='check_balance')],
        [InlineKeyboardButton("➕ Add Fund", callback_data='add_fund_prompt'),
         InlineKeyboardButton("➖ Remove Fund", callback_data='remove_fund_prompt')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🏦 *Admin Dashboard*", reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN_V2)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'check_balance':
        await query.edit_message_text(f"💰 *Current Balance:* `₹{esc(TOTAL_FUND)}`", parse_mode=ParseMode.MARKDOWN_V2)
    
    elif query.data == 'add_fund_prompt':
        await query.edit_message_text("✍️ *Reply to this message with the amount to add*\nExample: `100`", parse_mode=ParseMode.MARKDOWN_V2)
        context.user_data['action'] = 'adding'
    
    elif query.data == 'remove_fund_prompt':
        await query.edit_message_text("✍️ *Reply to this message with the amount to remove*\nExample: `50`", parse_mode=ParseMode.MARKDOWN_V2)
        context.user_data['action'] = 'removing'

# --- LOGIC TO HANDLE INPUTS ---
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global TOTAL_FUND
    if update.effective_user.id not in ADMIN_IDS: return
    
    msg_text = update.effective_message.text
    
    # Payout Detection (Priority)
    if msg_text.startswith("⚠️ New UPI Payout Request!"):
        match = re.search(r"Request Amount\s*:\s*₹([\d.]+)", msg_text)
        if match:
            amount = float(match.group(1))
            TOTAL_FUND -= amount
            save_fund(TOTAL_FUND)
            await update.message.reply_text(f"⚠️ *Payout Detected*\n📉 *Debit:* `₹{esc(amount)}`\n💰 *New Balance:* `₹{esc(TOTAL_FUND)}`", parse_mode=ParseMode.MARKDOWN_V2)
    
    # Manual Add/Remove Logic
    elif 'action' in context.user_data:
        try:
            amount = float(msg_text)
            if context.user_data['action'] == 'adding':
                TOTAL_FUND += amount
            else:
                TOTAL_FUND -= amount
            save_fund(TOTAL_FUND)
            await update.message.reply_text(f"✅ *Success*\n💰 *New Balance:* `₹{esc(TOTAL_FUND)}`", parse_mode=ParseMode.MARKDOWN_V2)
        except ValueError:
            await update.message.reply_text("❌ *Invalid Number*")
        finally:
            context.user_data.clear()

def main():
    Thread(target=run_web).start()
    app_bot = Application.builder().token(TOKEN).build()
    
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CallbackQueryHandler(button_handler))
    app_bot.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))
    
    app_bot.run_polling()

if __name__ == '__main__':
    main()
