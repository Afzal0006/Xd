import telebot
from telebot import types
from datetime import datetime, timedelta

# === CONFIG ===
TOKEN = "YOUR_BOT_TOKEN"
target_channel = "@your_channel"
OWNER_ID = 123456789

bot = telebot.TeleBot(TOKEN)

# === DATA STORAGE ===
admins = {OWNER_ID: 'Owner'}  # admin_id: username
trade_id = 1

# Daily stats (24h reset for completed/refund)
daily_completed = {}
daily_refunded = {}
hold_counts = {}
deal_history = {}  # trade_id: deal_info

# Record time for daily reset
last_reset = datetime.now()

# Store mapping username to user_id for DMs
user_ids = {}  # '@username': user_id

# === HELP FUNCTIONS ===
def is_admin(user_id):
    return user_id in admins

def reset_daily_stats():
    global daily_completed, daily_refunded, last_reset
    now = datetime.now()
    if now - last_reset >= timedelta(days=1):
        daily_completed = {}
        daily_refunded = {}
        last_reset = now

# Calculate fee automatically based on bio
def calculate_fee(buyer_bio_added=True, seller_bio_added=True, amount=0):
    if buyer_bio_added and seller_bio_added:
        fee = 0
    else:
        fee = amount * 0.03  # 3%
    return round(fee,2)

# Send DM to users if user_id known
def send_dm(username, text):
    user_id = user_ids.get(username)
    if user_id:
        bot.send_message(user_id, text)

# === COMMANDS ===
@bot.message_handler(commands=["start"])
def start(msg):
    user_ids[f"@{msg.from_user.username}"] = msg.from_user.id
    bot.reply_to(msg, "👋 Welcome to Escrow Bot! Use /add, /done, /refund commands (Admins only). Please save your username to receive DM notifications.")

# === ADD ADMIN ===
@bot.message_handler(commands=["addAdmin"])
def add_admin(msg):
    if msg.from_user.id != OWNER_ID:
        bot.reply_to(msg, "⛔ Permission Denied! Sirf Owner Admin add kar sakta hai.")
        return
    try:
        username = msg.text.split()[1]
        if username.startswith("@"): username = username[1:]
        new_id = int(msg.text.split()[2])  # admin_id pass karna hoga
        if new_id not in admins:
            admins[new_id] = username
            bot.reply_to(msg, f"✅ @{username} ab Escrow Admin ban gaya hai.")
        else:
            bot.reply_to(msg, f"⚠️ @{username} already Admin hai.")
    except:
        bot.reply_to(msg, "❌ Usage: /addAdmin @username user_id")

# === REMOVE ADMIN ===
@bot.message_handler(commands=["removeAdmin"])
def remove_admin(msg):
    if msg.from_user.id != OWNER_ID:
        bot.reply_to(msg, "⛔ Sirf Owner Admin hata sakta hai.")
        return
    try:
        remove_id = int(msg.text.split()[1])
        if remove_id in admins:
            username = admins.pop(remove_id)
            bot.reply_to(msg, f"❌ @{username} ab Admin nahi raha.")
        else:
            bot.reply_to(msg, "⚠️ Ye user Admin list me nahi hai.")
    except:
        bot.reply_to(msg, "❌ Usage: /removeAdmin user_id")

# === ADD DEAL ===
@bot.message_handler(commands=["add"])
def add_deal(msg):
    global trade_id
    if not is_admin(msg.from_user.id):
        bot.reply_to(msg, "⛔ Sirf Admin Deal Add kar sakta hai.")
        return

    parts = msg.text.split(" ")
    if len(parts) < 6:
        bot.reply_to(msg, "❌ Usage: /add buyer seller amount buyerBio(yes/no) sellerBio(yes/no)")
        return

    buyer, seller = parts[1], parts[2]
    amount = float(parts[3])
    buyer_bio = parts[4].lower() == 'yes'
    seller_bio = parts[5].lower() == 'yes'

    fee = calculate_fee(buyer_bio, seller_bio, amount)
    total = amount + fee
    admin_name = admins[msg.from_user.id]

    # Save deal in history
    deal_history[trade_id] = {
        'buyer': buyer, 'seller': seller, 'amount': amount, 'fee': fee, 'total': total,
        'admin': admin_name, 'status': 'hold', 'timestamp': datetime.now()
    }

    text = f"""✅ PAYMENT RECEIVED
────────────────
👤 Buyer  : {buyer}
👤 Seller : {seller}
💸 Amount : ₹{amount}
💰 Fee    : ₹{fee}
🧤 TOTAL : ₹{total}
🆔 Trade ID : #TID{trade_id}
CONTINUE DEAL ❤️
────────────────"""

    bot.send_message(msg.chat.id, text)
    # DM Notification
    send_dm(buyer, text)
    send_dm(seller, text)

    hold_counts[admin_name] = hold_counts.get(admin_name,0)+1
    trade_id +=1

# === DONE DEAL ===
@bot.message_handler(commands=["done"])
def done_deal(msg):
    global trade_id
    reset_daily_stats()

    if not is_admin(msg.from_user.id):
        bot.reply_to(msg, "⛔ Sirf Admin Deal Complete kar sakta hai.")
        return

    parts = msg.text.split(" ")
    if len(parts) < 4:
        bot.reply_to(msg, "❌ Usage: /done buyer seller amount")
        return

    buyer, seller = parts[1], parts[2]
    amount = float(parts[3])
    admin_name = admins[msg.from_user.id]

    fee = calculate_fee(True, True, amount)
    total = amount + fee

    daily_completed[admin_name] = daily_completed.get(admin_name,0)+amount
    hold_counts[admin_name] = max(hold_counts.get(admin_name,1)-1,0)

    # Update deal history
    for tid, deal in deal_history.items():
        if deal['buyer']==buyer and deal['seller']==seller and deal['status']=='hold':
            deal['status']='completed'
            deal['completed_timestamp']=datetime.now()
            deal['fee']=fee
            deal['total']=total

    text = f"""✅ DEAL COMPLETED
────────────────
👤 Buyer  : {buyer}
👤 Seller : {seller}
💰 Amount : ₹{amount}
💰 Fee    : ₹{fee}
🧤 TOTAL : ₹{total}
🆔 Trade ID : #TID{trade_id}
────────────────
🛡️ Escrowed by @{admin_name}"""

    bot.send_message(msg.chat.id, text)
    bot.send_message(target_channel, text.replace("✅ DEAL COMPLETED", "📜 Deal Completed (Log)"))
    # DM Notification
    send_dm(buyer, text)
    send_dm(seller, text)

# === REFUND DEAL ===
@bot.message_handler(commands=["refund"])
def refund_deal(msg):
    global trade_id
    reset_daily_stats()

    if not is_admin(msg.from_user.id):
        bot.reply_to(msg, "⛔ Sirf Admin Refund kar sakta hai.")
        return

    parts = msg.text.split(" ")
    if len(parts) < 4:
        bot.reply_to(msg, "❌ Usage: /refund buyer seller amount")
        return

    buyer, seller = parts[1], parts[2]
    amount = float(parts[3])
    admin_name = admins[msg.from_user.id]

    fee = calculate_fee(True, True, amount)
    total = amount + fee

    daily_refunded[admin_name] = daily_refunded.get(admin_name,0)+amount

    # Update deal history
    for tid, deal in deal_history.items():
        if deal['buyer']==buyer and deal['seller']==seller and deal['status']=='hold':
            deal['status']='refunded'
            deal['refunded_timestamp']=datetime.now()
            deal['fee']=fee
            deal['total']=total

    text = f"""❌ REFUND COMPLETED
────────────────
👤 Buyer  : {buyer}
👤 Seller : {seller}
💰 Refund : ₹{amount}
💰 Fee    : ₹{fee}
🧤 TOTAL : ₹{total}
🆔 Trade ID : #TID{trade_id}
────────────────
🛡️ Escrowed by @{admin_name}"""

    bot.send_message(msg.chat.id, text)
    bot.send_message(target_channel, text.replace("❌ REFUND COMPLETED", "📜 Refund Log"))
    # DM Notification
    send_dm(buyer, text)
    send_dm(seller, text)

# === RUN BOT ===
bot.infinity_polling()
