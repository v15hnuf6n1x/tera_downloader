from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
import logging
import asyncio
from pyrogram.enums import ChatMemberStatus
from dotenv import load_dotenv
from os import environ
import time
from pymongo import MongoClient
from datetime import datetime
from status import format_progress_bar  # Assuming this module exists
from video import download_video, upload_video  # Assuming these functions are correctly implemented

load_dotenv('config.env', override=True)

logging.basicConfig(level=logging.INFO)

api_id = environ.get('TELEGRAM_API', '28192191')
if not api_id:
    logging.error("TELEGRAM_API variable is missing! Exiting now")
    exit(1)

api_hash = environ.get('TELEGRAM_HASH', '663164abd732848a90e76e25cb9cf54a')
if not api_hash:
    logging.error("TELEGRAM_HASH variable is missing! Exiting now")
    exit(1)

bot_token = environ.get('BOT_TOKEN', '7198441390:AAFKm0aYuNbv_kWLesYFmtlLpC-nP5ogrbY')
if not bot_token:
    logging.error("BOT_TOKEN variable is missing! Exiting now")
    exit(1)

dump_id = environ.get('DUMP_CHAT_ID', '-1002149484754')
if not dump_id:
    logging.error("DUMP_CHAT_ID variable is missing! Exiting now")
    exit(1)
else:
    dump_id = int(dump_id)

fsub_id = environ.get('FSUB_ID', '-1002249393777')
if not fsub_id:
    logging.error("FSUB_ID variable is missing! Exiting now")
    exit(1)
else:
    fsub_id = int(fsub_id)

# Set up MongoDB connection
mongo_uri = environ.get('MONGO_URI', 'mongodb+srv://file:link@cluster0.jth5g3y.mongodb.net/?retryWrites=true&w=majority')
mongo_client = MongoClient(mongo_uri)
db = mongo_client['terabot']
user_collection = db['terausers']

app = Client("my_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

@app.on_message(filters.command("start"))
async def start_command(client, message):
    sticker_message = await message.reply_sticker("CAACAgIAAxkBAAEYonplzwrczhVu3I6HqPBzro3L2JU6YAACvAUAAj-VzAoTSKpoG9FPRjQE")
    await asyncio.sleep(2)
    await sticker_message.delete()
    user_mention = message.from_user.mention
    reply_message = f"ᴡᴇʟᴄᴏᴍᴇ, {user_mention}.\n\n🌟 ɪ ᴀᴍ ᴀ ᴛᴇʀᴀʙᴏx ᴅᴏᴡɴʟᴏᴀᴅᴇʀ ʙᴏᴛ. sᴇɴᴅ ᴍᴇ ᴀɴʏ ᴛᴇʀᴀʙᴏx ʟɪɴᴋ ɪ ᴡɪʟʟ ᴅᴏᴡɴʟᴏᴀᴅ ᴡɪᴛʜɪɴ ғᴇᴡ sᴇᴄᴏɴᴅs ᴀɴᴅ sᴇɴᴅ ɪᴛ ᴛᴏ ʏᴏᴜ ✨."
    join_button = InlineKeyboardButton("ᴊᴏɪɴ ", url="https://t.me/teraboxx_downloader")
    developer_button = InlineKeyboardButton("ᴅᴇᴠᴇʟᴏᴘᴇʀ⚡️", url="https://t.me/naresh3221")
    help_button = InlineKeyboardButton("Help", url="https://t.me/teraboxx_downloader")
    reply_markup = InlineKeyboardMarkup([[join_button, developer_button, help_button]])
    await message.reply_text(reply_message, reply_markup=reply_markup)

async def is_user_member(client, user_id):
    user_data = user_collection.find_one({"user_id": user_id})
    if user_data:
        return user_data.get("role", "member")
    
    try:
        member = await client.get_chat_member(fsub_id, user_id)
        if member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            role = "admin"
        elif member.status == ChatMemberStatus.MEMBER:
            role = "member"
        else:
            role = "none"

        user_collection.update_one(
            {"user_id": user_id},
            {"$set": {"role": role, "last_checked": datetime.utcnow()}},
            upsert=True
        )
        logging.info(f"User {user_id} membership status: {member.status}, role: {role}")
        return role
    except Exception as e:
        logging.error(f"Error checking membership status for user {user_id}: {e}")
        return "none"

@app.on_message(filters.text)
async def handle_message(client, message: Message):
    user_id = message.from_user.id
    user_mention = message.from_user.mention
    role = await is_user_member(client, user_id)

    if role == "none":
        join_button = InlineKeyboardButton("ᴊᴏɪɴ ", url="https://t.me/teraboxx_downloader")
        reply_markup = InlineKeyboardMarkup([[join_button]])
        await message.reply_text("ʏᴏᴜ ᴍᴜsᴛ ᴊᴏɪɴ ᴍʏ ᴄʜᴀɴɴᴇʟ ᴛᴏ ᴜsᴇ ᴍᴇ.", reply_markup=reply_markup)
        return

    terabox_link = message.text.strip()
    if "terabox" not in terabox_link:
        await message.reply_text("ᴘʟᴇᴀsᴇ sᴇɴᴅ ᴀ ᴠᴀʟɪᴅ ᴛᴇʀᴀʙᴏx ʟɪɴᴋ.")
        return

    reply_msg = await message.reply_text("sᴇɴᴅɪɴɢ ʏᴏᴜ ᴛʜᴇ ᴍᴇᴅɪᴀ...🤤")

    try:
        file_path, thumbnail_path, video_title = await download_video(terabox_link, reply_msg, user_mention, user_id)
        await upload_video(client, file_path, thumbnail_path, video_title, reply_msg, dump_id, user_mention, user_id, message)
    except Exception as e:
        logging.error(f"Error handling message: {e}")
        await reply_msg.edit_text("ғᴀɪʟᴇᴅ ᴛᴏ ᴘʀᴏᴄᴇss ʏᴏᴜʀ ʀᴇǫᴜᴇsᴛ.\nɪғ ʏᴏᴜʀ ғɪʟᴇ sɪᴢᴇ ɪs ᴍᴏʀᴇ ᴛʜᴀɴ 120ᴍʙ ɪᴛ ᴍɪɢʜᴛ ғᴀɪʟ ᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅ.")

@app.on_message(filters.command("add_admin"))
async def add_admin(client, message):
    if message.from_user.id not in [your_admin_id_here]:  # Replace with your admin ID
        await message.reply_text("You are not authorized to use this command.")
        return

    if not message.reply_to_message:
        await message.reply_text("Please reply to the user message you want to promote to admin.")
        return

    user_id = message.reply_to_message.from_user.id
    user_collection.update_one(
        {"user_id": user_id},
        {"$set": {"role": "admin"}},
        upsert=True
    )
    await message.reply_text(f"User {user_id} has been promoted to admin.")

if __name__ == "__main__":
    app.run()
