from pyrogram import Client
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import random

# Apne secret config import karo
from config import API_ID, API_HASH, BOT_TOKEN

# Ban list (IDs of users who should never be approved)
ban_list = [11111111, 22222222]

# Store pending verifications
pending_users = {}

# Initialize bot
app = Client("captcha_autoapprove_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


# 🚀 Handle Join Requests
@app.on_chat_join_request()
def handle_join_request(client, join_request):
    user = join_request.from_user
    chat_id = join_request.chat.id

    # ❌ Ban check
    if user.id in ban_list:
        join_request.decline()
        return

    # ❌ Must have username
    if not user.username:
        join_request.decline()
        return

    # ❌ Must have profile photo
    if not user.photo:
        join_request.decline()
        return

    # ✅ Generate Captcha Question
    a, b = random.randint(1, 9), random.randint(1, 9)
    correct_answer = a + b

    options = [correct_answer, correct_answer + 1, correct_answer - 1, correct_answer + 2]
    random.shuffle(options)

    # Save pending verification
    pending_users[user.id] = {"chat_id": chat_id, "correct": correct_answer}

    # Send captcha quiz in DM
    try:
        buttons = InlineKeyboardMarkup(
            [[InlineKeyboardButton(str(opt), callback_data=f"ans_{opt}_{user.id}")] for opt in options]
        )
        app.send_message(
            user.id,
            f"🤖 Verification Required!\n\nSolve this to join group:\n👉 {a} + {b} = ?",
            reply_markup=buttons
        )
    except:
        # If bot not started by user → decline
        join_request.decline()


# 🚀 Handle Captcha Answer
@app.on_callback_query()
def check_answer(client, callback_query):
    data = callback_query.data.split("_")
    if len(data) != 3:
        return

    _, ans, uid = data
    ans = int(ans)
    uid = int(uid)

    # Ensure user is same
    if callback_query.from_user.id != uid:
        callback_query.answer("⚠️ This is not your captcha!", show_alert=True)
        return

    if uid in pending_users:
        chat_id = pending_users[uid]["chat_id"]
        correct = pending_users[uid]["correct"]

        if ans == correct:
            # ✅ Approve
            app.approve_chat_join_request(chat_id, uid)
            callback_query.edit_message_text("✅ Verification successful! You are now approved.")
            app.send_message(chat_id, f"🎉 Welcome {callback_query.from_user.mention}! ✅ Verified.")
        else:
            # ❌ Reject
            app.decline_chat_join_request(chat_id, uid)
            callback_query.edit_message_text("❌ Wrong answer! Join request rejected.")
        
        del pending_users[uid]


print("🚀 Captcha Auto-Approval Bot Started...")
app.run()
