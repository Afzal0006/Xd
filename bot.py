import random
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ================= CONFIG =================
BOT_TOKEN = "8423240758:AAE6gyDHVjs-Y0TQET0ayfUJhmCUQN1WnEk"  # Replace with your bot token
LOG_CHANNEL_ID = -1002829010235  # Replace with your log channel ID
OWNER_ID = 8290519229  # Replace with your Telegram user ID (owner)

# Admin & user data storage
ADMINS = set()
USER_STATS = {}  # {user_id: {"deals": int, "amount": float}}
GLOBAL_STATS = {}  # {admin_id: {"deals": int, "amount": float, "timestamp": int}}
TRADE_ID = 1
TRADES = {}

# ==========================================
logging.basicConfig(level=logging.INFO)

# Utility function: send DM with footer
async def send_dm_with_footer(user_id: int, text: str, context: ContextTypes.DEFAULT_TYPE):
    footer = ("\n\nTHIS BOT CREATED BY THE ISLAND MANAGEMENT TEAM\n"
              "OWNER @DEFIGURED\n"
              "MANAGEMENT HEAD @DAK8H9T\n"
              "JOIN GROUP LINK @ESCROW_IW ⚠️")
    try:
        await context.bot.send_message(chat_id=user_id, text=text + footer, parse_mode=ParseMode.MARKDOWN)
    except:
        pass

# Utility: update stats
def update_stats(user_id, amount, admin_id):
    # User stats
    if user_id not in USER_STATS:
        USER_STATS[user_id] = {"deals": 0, "amount": 0.0}
    USER_STATS[user_id]["deals"] += 1
    USER_STATS[user_id]["amount"] += amount

    # Global stats
    if admin_id not in GLOBAL_STATS:
        GLOBAL_STATS[admin_id] = {"deals": 0, "amount": 0.0, "timestamp": int(time.time())}
    # reset if 24h passed
    if time.time() - GLOBAL_STATS[admin_id]["timestamp"] > 86400:
        GLOBAL_STATS[admin_id] = {"deals": 0, "amount": 0.0, "timestamp": int(time.time())}
    GLOBAL_STATS[admin_id]["deals"] += 1
    GLOBAL_STATS[admin_id]["amount"] += amount

# Command: /add
async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global TRADE_ID
    if update.effective_user.id not in ADMINS and update.effective_user.id != OWNER_ID:
        return

    if len(context.args) < 3:
        await update.message.reply_text("Usage: /add buyer seller amount")
        return

    buyer, seller, amount = context.args[0], context.args[1], float(context.args[2])
    tid = f"#TID{TRADE_ID}"
    TRADE_ID += 1

    text = f"""✅ PAYMENT RECEIVED 
────────────────
👤 Buyer  : {buyer}
👤 Seller : {seller}
💸 Received : ₹{amount}
🆔 Trade ID : {tid}
💰 Fee     : ₹0
   CONTINUE DEAL ❤️
──────────────"""

    await update.message.reply_text(text)
    await send_dm_with_footer(buyer, text, context)
    await send_dm_with_footer(seller, text, context)

# Command: /add+fee
async def add_fee(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global TRADE_ID
    if update.effective_user.id not in ADMINS and update.effective_user.id != OWNER_ID:
        return

    if len(context.args) < 3:
        await update.message.reply_text("Usage: /add+fee buyer seller amount")
        return

    buyer, seller, amount = context.args[0], context.args[1], float(context.args[2])
    tid = f"#TID{TRADE_ID}"
    TRADE_ID += 1

    fee = round(amount * 0.03, 2)
    total = amount + fee

    text = f"""✅ PAYMENT RECEIVED 
────────────────
👤 Buyer  : {buyer}
👤 Seller : {seller}
💸 Received : ₹{amount}
🆔 Trade ID : {tid}
💰 Fee     : 3%
🧤 TOTAL   : ₹{total}
   CONTINUE DEAL ❤️
──────────────"""

    await update.message.reply_text(text)
    await send_dm_with_footer(buyer, text, context)
    await send_dm_with_footer(seller, text, context)

# Command: /done
async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS and update.effective_user.id != OWNER_ID:
        return

    if len(context.args) < 3:
        await update.message.reply_text("Usage: /done buyer seller amount")
        return

    buyer, seller, amount = context.args[0], context.args[1], float(context.args[2])
    tid = f"#TID{TRADE_ID}"

    text = f"""✅ DEAL COMPLETED 
────────────────
👤 Buyer : {buyer}
👤 Seller : {seller}
💰 Amount : ₹{amount}
🆔 Trade ID : {tid}
────────────────
🛡️ Escrowed by @{update.effective_user.username}"""

    await update.message.reply_text(text)
    await send_dm_with_footer(buyer, text, context)
    await send_dm_with_footer(seller, text, context)

    # Log in channel
    await context.bot.send_message(LOG_CHANNEL_ID, f"📜 Deal Completed (Log)\n{text}")

    # Stats update
    update_stats(buyer, amount, update.effective_user.id)
    update_stats(seller, amount, update.effective_user.id)

# Command: /done+fee
async def done_fee(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS and update.effective_user.id != OWNER_ID:
        return

    if len(context.args) < 3:
        await update.message.reply_text("Usage: /done+fee buyer seller amount")
        return

    buyer, seller, amount = context.args[0], context.args[1], float(context.args[2])
    tid = f"#TID{TRADE_ID}"

    fee = round(amount * 0.03, 2)
    total = amount + fee

    text = f"""✅ Deal Completed!
────────────────
👤 Buyer  : {buyer}
👤 Seller : {seller}
💸 Released : ₹{amount}
🆔 Trade ID : {tid}
💰 Fee     : 3%
🧤 TOTAL   : ₹{total}
────────────────
🛡️ Escrowed by @{update.effective_user.username}"""

    await update.message.reply_text(text)
    await send_dm_with_footer(buyer, text, context)
    await send_dm_with_footer(seller, text, context)

    # Log in channel
    await context.bot.send_message(LOG_CHANNEL_ID, f"📜 Deal Completed (Log)\n{text}")

    # Stats update
    update_stats(buyer, amount, update.effective_user.id)
    update_stats(seller, amount, update.effective_user.id)

# Command: /stats
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    stats = USER_STATS.get(uid, {"deals": 0, "amount": 0.0})
    await update.message.reply_text(f"📊 Your Stats\n────────────────\nDeals: {stats['deals']}\nAmount Escrowed: ₹{stats['amount']}")

# Command: /gstats (admin only)
async def gstats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS and update.effective_user.id != OWNER_ID:
        return

    text = "📊 Global Admin Stats (24h)\n────────────────\n"
    for admin_id, data in GLOBAL_STATS.items():
        text += f"👮 Admin: {admin_id}\nDeals: {data['deals']}\nAmount: ₹{data['amount']}\n\n"
    await update.message.reply_text(text)

# Command: /addadmin
async def addadmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    if not context.args:
        return await update.message.reply_text("Usage: /addadmin user_id")
    uid = int(context.args[0])
    ADMINS.add(uid)
    await update.message.reply_text(f"Added admin: {uid}")

# Command: /removeadmin
async def removeadmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    if not context.args:
        return await update.message.reply_text("Usage: /removeadmin user_id")
    uid = int(context.args[0])
    ADMINS.discard(uid)
    await update.message.reply_text(f"Removed admin: {uid}")

# Command: /removeadmins
async def removeadmins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    ADMINS.clear()
    await update.message.reply_text("All admins removed.")

# =============== MAIN ===============
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("add+fee", add_fee))
    app.add_handler(CommandHandler("done", done))
    app.add_handler(CommandHandler("done+fee", done_fee))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("gstats", gstats))
    app.add_handler(CommandHandler("addadmin", addadmin))
    app.add_handler(CommandHandler("removeadmin", removeadmin))
    app.add_handler(CommandHandler("removeadmins", removeadmins))

    app.run_polling()

if __name__ == "__main__":
    main()
