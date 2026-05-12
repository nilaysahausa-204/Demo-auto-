# ==========================================
# NILAY BOT MEGA SINGLE FILE VERSION
# ==========================================

import os
import time
import asyncio
import random
import string
import logging
import platform

from flask import Flask
from dotenv import load_dotenv
from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ChatPermissions
)
from motor.motor_asyncio import AsyncIOMotorClient

# ==========================================
# LOAD ENV
# ==========================================

load_dotenv()

API_ID = int(os.environ.get("API_ID", ""))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
BOT_USERNAME = os.environ.get("BOT_USERNAME", "NilayBot")
ADMIN = int(os.environ.get("ADMIN", "0"))
MONGO_DB_URI = os.environ.get("MONGO_DB_URI", "")
LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", "0"))
DB_CHANNEL = int(os.environ.get("DB_CHANNEL", "0"))
UPDATE_CHANNEL = os.environ.get("UPDATE_CHANNEL", "")

# ==========================================
# FLASK WEB SERVER
# ==========================================

web = Flask(__name__)

@web.route('/')
def home():
    return "Nilay Bot Running Successfully"

# ==========================================
# DATABASE
# ==========================================

mongo_client = AsyncIOMotorClient(MONGO_DB_URI)
db = mongo_client["NilayBot"]
users_col = db["users"]
files_col = db["files"]

# ==========================================
# BOT CLIENT
# ==========================================

app = Client(
    "NilayBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ==========================================
# HELPER FUNCTIONS
# ==========================================

async def add_user(user_id):
    user = await users_col.find_one({"user_id": user_id})

    if not user:
        await users_col.insert_one({"user_id": user_id})


async def total_users():
    return await users_col.count_documents({})


def generate_token(length=8):
    return ''.join(random.choice(string.ascii_letters) for _ in range(length))

# ==========================================
# START COMMAND
# ==========================================

@app.on_message(filters.command("start"))
async def start_command(client, message):

    await add_user(message.from_user.id)

    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "📢 Updates",
                    url=f"https://t.me/{UPDATE_CHANNEL}"
                )
            ],
            [
                InlineKeyboardButton(
                    "ℹ️ Help",
                    callback_data="help"
                )
            ]
        ]
    )

    text = f"""
👋 Hello {message.from_user.mention}

Welcome To Nilay Bot ⚡

📂 Unlimited File Storage
🚀 Fast Sharing
🔒 Secure Telegram Bot
"""

    await message.reply_text(
        text,
        reply_markup=buttons
    )

# ==========================================
# HELP COMMAND
# ==========================================

@app.on_message(filters.command("help"))
async def help_command(client, message):

    text = """
📚 Nilay Bot Help

/start - Start Bot
/help - Help Menu
/about - About Bot
/stats - Statistics
/ping - Check Speed
/id - User ID
/search - Search Files
/broadcast - Broadcast
"""

    await message.reply_text(text)

# ==========================================
# ABOUT
# ==========================================

@app.on_message(filters.command("about"))
async def about_command(client, message):

    await message.reply_text(
        "🤖 Nilay Bot\n⚡ Advanced Telegram File Store Bot"
    )

# ==========================================
# STORE FILES
# ==========================================

@app.on_message(filters.private & (filters.document | filters.video | filters.audio | filters.photo))
async def store_files(client, message):

    copied = await message.copy(DB_CHANNEL)

    file_id = copied.id

    await files_col.insert_one(
        {
            "file_id": file_id,
            "type": str(message.media)
        }
    )

    link = f"https://t.me/{BOT_USERNAME}?start=file_{file_id}"

    await message.reply_text(
        f"✅ File Stored Successfully\n\n🔗 {link}"
    )

# ==========================================
# GET FILE
# ==========================================

@app.on_message(filters.command("start"))
async def get_file(client, message):

    if len(message.command) < 2:
        return

    data = message.command[1]

    if data.startswith("file_"):

        file_id = int(data.split("_")[1])

        await client.copy_message(
            message.chat.id,
            DB_CHANNEL,
            file_id
        )

# ==========================================
# SEARCH
# ==========================================

@app.on_message(filters.command("search"))
async def search_command(client, message):

    if len(message.command) < 2:
        return await message.reply_text(
            "Usage : /search movie"
        )

    query = message.text.split(None, 1)[1]

    text = f"🔍 Searching : {query}"

    await message.reply_text(text)

# ==========================================
# BROADCAST
# ==========================================

@app.on_message(filters.command("broadcast") & filters.user(ADMIN))
async def broadcast_command(client, message):

    if not message.reply_to_message:
        return

    users = users_col.find({})

    total = 0

    async for user in users:

        try:

            await message.reply_to_message.copy(user["user_id"])
            total += 1

        except:
            pass

    await message.reply_text(
        f"✅ Broadcast Done\n\n👥 Sent : {total}"
    )

# ==========================================
# STATS
# ==========================================

@app.on_message(filters.command("stats"))
async def stats_command(client, message):

    users = await total_users()

    await message.reply_text(
        f"📊 Total Users : {users}"
    )

# ==========================================
# PING
# ==========================================

@app.on_message(filters.command("ping"))
async def ping_command(client, message):

    start = time.time()

    msg = await message.reply_text("🏓 Pinging...")

    end = time.time()

    speed = round((end - start) * 1000)

    await msg.edit_text(
        f"🏓 Pong : {speed} ms"
    )

# ==========================================
# USER ID
# ==========================================

@app.on_message(filters.command("id"))
async def id_command(client, message):

    await message.reply_text(
        f"🆔 Your ID : {message.from_user.id}"
    )

# ==========================================
# BAN WORD FILTER
# ==========================================

BAD_WORDS = ["spam", "hack", "virus"]

@app.on_message(filters.group & filters.text)
async def badword_filter(client, message):

    text = message.text.lower()

    for word in BAD_WORDS:

        if word in text:

            try:
                await message.delete()
            except:
                pass

# ==========================================
# AUTO REPLY
# ==========================================

@app.on_message(filters.private & filters.text)
async def auto_reply(client, message):

    text = message.text.lower()

    if "hello" in text:
        await message.reply_text("👋 Hello")

# ==========================================
# FORCE SUB
# ==========================================

@app.on_message(filters.private)
async def force_subscribe(client, message):

    try:

        await client.get_chat_member(
            UPDATE_CHANNEL,
            message.from_user.id
        )

    except:

        button = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "📢 Join Channel",
                        url=f"https://t.me/{UPDATE_CHANNEL}"
                    )
                ]
            ]
        )

        await message.reply_text(
            "⚠️ Join Updates Channel First",
            reply_markup=button
        )

# ==========================================
# GROUP LOCK
# ==========================================

@app.on_message(filters.command("lock") & filters.user(ADMIN))
async def lock_group(client, message):

    await client.set_chat_permissions(
        message.chat.id,
        ChatPermissions()
    )

    await message.reply_text("🔒 Group Locked")

# ==========================================
# GROUP UNLOCK
# ==========================================

@app.on_message(filters.command("unlock") & filters.user(ADMIN))
async def unlock_group(client, message):

    permissions = ChatPermissions(
        can_send_messages=True
    )

    await client.set_chat_permissions(
        message.chat.id,
        permissions
    )

    await message.reply_text("🔓 Group Unlocked")

# ==========================================
# PREMIUM SYSTEM
# ==========================================

premium_users = []

@app.on_message(filters.command("premium"))
async def premium_check(client, message):

    if message.from_user.id in premium_users:

        await message.reply_text("💎 Premium User")

    else:

        await message.reply_text("❌ Not Premium")

# ==========================================
# SERVER INFO
# ==========================================

@app.on_message(filters.command("server"))
async def server_info(client, message):

    text = f"""
🖥 Server Information

💻 System : {platform.system()}
⚡ Release : {platform.release()}
"""

    await message.reply_text(text)

# ==========================================
# MAIN
# ==========================================

print("✅ Nilay Bot Started Successfully")

app.run()
