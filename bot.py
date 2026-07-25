import sqlite3
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler, 
    ChatJoinRequestHandler, MessageHandler, filters, ContextTypes
)

# 🌐 Keep Alive for 24/7 Hosting
from keep_alive import keep_alive

# --- Configuration ---
BOT_TOKEN = "YOUR_NEW_BOT_TOKEN_HERE"  # ⚠️ Replace this with your new Bot Token

ADMIN_USERNAME = "saddamadmin"
ADMIN_PASSWORD = "saddamadmin1234"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
DB_NAME = "fast_accepter.db"

# --- Database Setup ---
def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS bot_users (user_id INTEGER PRIMARY KEY, first_name TEXT)")
        conn.commit()
init_db()

def save_user(user_id, first_name):
    with sqlite3.connect(DB_NAME) as conn: 
        conn.execute("INSERT OR IGNORE INTO bot_users (user_id, first_name) VALUES (?, ?)", (user_id, first_name))
        conn.commit()

# --- Start Command (Premium Design) ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    save_user(user.id, user.first_name)
    context.user_data['state'] = None
    bot_uname = context.bot.username

    txt = (
        f"✨ <b>I'm Alive and Super Fast!</b> 🚀\n\n"
        f"I can approve new join requests in your chats automatically in <b>0.1 seconds</b>.\n\n"
        f"✅ Just add me as an Administrator in your channel or group with <i>'Invite Users'</i> permission.\n\n"
        f"🔥 <b>For downloading any Video/Music without watermark, use our Premium Bot:</b>\n"
        f"👉 @AllInOneDL_AIBot\n\n"
        f"👇 <b>Use the below buttons to add me to your chat:</b>"
    )
    
    # Direct Add Buttons with Auto Permissions
    kb = [
        [InlineKeyboardButton("↗️ Add me to a channel!", url=f"https://t.me/{bot_uname}?startchannel=true&admin=invite_users")],
        [InlineKeyboardButton("➕ Add me to a group!", url=f"https://t.me/{bot_uname}?startgroup=true&admin=invite_users")]
    ]
    
    await update.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

# --- Super Fast Auto-Accept Logic ---
async def handle_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Accepts request instantly (0.1s)
    try:
        await context.bot.approve_chat_join_request(
            chat_id=update.chat_join_request.chat.id, 
            user_id=update.chat_join_request.from_user.id
        )
    except Exception as e:
        pass # Silently ignore if bot lacks admin rights

# --- Admin Panel ---
async def saddamadmin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['state'] = 'WAITING_ADMIN_USER'
    await update.message.reply_text("👑 <b>Secret Admin Login:</b>\nEnter Username:", parse_mode=ParseMode.HTML)

async def show_admin_panel(update_or_message, context):
    context.user_data['is_admin'] = True
    context.user_data['state'] = None
    
    with sqlite3.connect(DB_NAME) as conn:
        usr = conn.execute("SELECT COUNT(*) FROM bot_users").fetchone()[0]

    text = f"👑 <b>Super Admin Dashboard</b>\n━━━━━━━━━━━━━━━━━━\n👥 Total Users: <b>{usr}</b>\n━━━━━━━━━━━━━━━━━━\n👇 <i>Select an action:</i>"
    kb = [
        [InlineKeyboardButton("📣 User Broadcast", callback_data="admin_bc")],
        [InlineKeyboardButton("❌ Logout", callback_data="admin_logout")]
    ]
    
    if hasattr(update_or_message, 'reply_text'): 
        await update_or_message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)
    else: 
        await update.message.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

# --- Admin Broadcast Handler ---
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    state = context.user_data.get('state')
    is_admin = context.user_data.get('is_admin')

    if state == 'WAITING_ADMIN_USER':
        if text == ADMIN_USERNAME:
            context.user_data['state'] = 'WAITING_ADMIN_PASS'
            await update.message.reply_text("✅ Username correct! Enter Password:")
        else:
            context.user_data['state'] = None
            await update.message.reply_text("❌ Incorrect Username!")
        return
            
    elif state == 'WAITING_ADMIN_PASS':
        if text == ADMIN_PASSWORD: 
            await show_admin_panel(update.message, context)
        else:
            context.user_data['state'] = None
            await update.message.reply_text("❌ Incorrect Password!")
        return

    if state == 'WAITING_BC_MSG' and is_admin:
        with sqlite3.connect(DB_NAME) as conn: 
            users = [u[0] for u in conn.execute("SELECT user_id FROM bot_users").fetchall()]
        
        msg = await update.message.reply_text(f"⏳ Sending to {len(users)} users...")
        success = 0
        for uid in users:
            try:
                await context.bot.copy_message(chat_id=uid, from_chat_id=update.effective_chat.id, message_id=update.message.message_id)
                success += 1
                await asyncio.sleep(0.05) # Anti-spam delay
            except: pass
        await msg.edit_text(f"✅ Broadcast Successful! (Sent to {success}/{len(users)} users)")
        await show_admin_panel(update.message, context)

# --- Button Handler ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data == "admin_bc":
        context.user_data['state'] = 'WAITING_BC_MSG'
        await query.edit_message_text("📣 <b>User Broadcast:</b>\n\nSend the message, photo, or video you want to broadcast to all users:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="admin_cancel")]]), parse_mode=ParseMode.HTML)

    elif data == "admin_cancel":
        await show_admin_panel(query, context)
        
    elif data == "admin_logout":
        context.user_data['is_admin'] = False
        await query.edit_message_text("✅ <b>Logout Successful.</b>", parse_mode=ParseMode.HTML)

def main():
    # 🌐 Keep server awake 24/7
    keep_alive()
    
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("saddamadmin", saddamadmin_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(ChatJoinRequestHandler(handle_join_request))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_text))
    
    print("🚀 Super Fast Auto Accepter Bot is running 24/7...")
    app.run_polling()

if __name__ == '__main__':
    main()
