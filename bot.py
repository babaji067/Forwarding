import nest_asyncio
import asyncio
import re
import os
import sys
from datetime import datetime, timedelta
from telegram import (
    Update, ChatPermissions, InlineKeyboardButton,
    InlineKeyboardMarkup, InputMediaPhoto
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)
from motor.motor_asyncio import AsyncIOMotorClient

nest_asyncio.apply()

BOT_TOKEN = os.environ.get("BOT_TOKEN", "7728184667:AAGWwerHbDSliBXUxYsnu9w0JKL56gwUdWY")
OWNER_ID = int(os.environ.get("OWNER_ID", "7240937506"))
UPDATE_CHANNEL = os.environ.get("UPDATE_CHANNEL", "-1002178394215")
UPDATE_CHANNEL_LINK = os.environ.get("UPDATE_CHANNEL_LINK", "https://t.me/messo_network")

MONGO_URL = os.environ.get("MONGO_URL", "mongodb+srv://students4396_db_user:f7h8YiRS4E34HeRi@biomutebaba.rbe30h1.mongodb.net/?appName=biomuteBaba")

mongo_client = AsyncIOMotorClient(MONGO_URL)
db = mongo_client["BioMuteBot"]
users_col = db["users"]
groups_col = db["groups"]
warnings_col = db["warnings"]
settings_col = db["settings"]
group_members_col = db["group_members"]

GROUPS_FILE = "groups.txt"
USERS_FILE = "users.txt"

def has_link(text: str) -> bool:
    return bool(re.search(r"(http|www\.|t\.me|instagram\.com|facebook\.com)", text, re.IGNORECASE))

def has_username(text: str) -> bool:
    return bool(re.search(r"@\w+", text)) and not has_link(text)

async def save_user(user_id):
    try:
        await users_col.update_one({"_id": user_id}, {"$set": {"_id": user_id}}, upsert=True)
    except:
        pass

async def approve_user(user_id):
    await users_col.update_one({"_id": user_id}, {"$set": {"_id": user_id, "is_approved": True}}, upsert=True)

async def unapprove_user(user_id):
    await users_col.update_one({"_id": user_id}, {"$set": {"_id": user_id, "is_approved": False}}, upsert=True)

async def is_user_approved(user_id):
    doc = await users_col.find_one({"_id": user_id})
    return doc.get("is_approved", False) if doc else False

async def save_group(group_id):
    try:
        await groups_col.update_one({"_id": group_id}, {"$set": {"_id": group_id}}, upsert=True)
    except:
        pass

async def get_mute_duration():
    doc = await settings_col.find_one({"_id": "mute_duration"})
    return doc["value"] if doc else 2

async def set_mute_duration(hours):
    await settings_col.update_one({"_id": "mute_duration"}, {"$set": {"value": hours}}, upsert=True)

async def get_update_channel():
    doc = await settings_col.find_one({"_id": "update_channel"})
    if doc:
        link = doc.get("link") or f"https://t.me/{str(doc['value']).lstrip('-100')}"
        return doc["value"], link
    return UPDATE_CHANNEL, UPDATE_CHANNEL_LINK

async def set_update_channel(chat_id, invite_link=None):
    data = {"value": str(chat_id)}
    if invite_link:
        data["link"] = invite_link
    await settings_col.update_one({"_id": "update_channel"}, {"$set": data}, upsert=True)

async def get_bio(context, user_id):
    try:
        chat = await context.bot.get_chat(user_id)
        return chat.bio or ""
    except:
        return ""

async def check_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.from_user:
        return

    user = update.message.from_user
    chat = update.effective_chat
    user_id = user.id
    chat_id = chat.id
    msg_text = update.message.text or ""

    if chat.type in ["group", "supergroup"]:
        await save_group(chat_id)
        try:
            await group_members_col.update_one(
                {"group_id": chat_id, "user_id": user_id}, 
                {"$set": {"group_id": chat_id, "user_id": user_id}}, 
                upsert=True
            )
        except:
            pass
    else:
        await save_user(user_id)

    try:
        member = await context.bot.get_chat_member(chat.id, user_id)
        if member.status in ["administrator", "creator"]:
            return
    except:
        return

    if await is_user_approved(user_id):
        return

    # FIRST NAME check â Permanent Mute
    if has_link(user.first_name):
        try:
            await context.bot.restrict_chat_member(
                chat_id=chat_id,
                user_id=user_id,
                permissions=ChatPermissions(can_send_messages=False)
            )
            channel_id, channel_link = await get_update_channel()
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("ð Update Channel", url=channel_link)],
                [InlineKeyboardButton("ð Unmute", url=f"https://t.me/{context.bot.username}")]
            ])
            await context.bot.send_message(
                chat_id=user_id,
                text=f"âï¸ Bio mute âï¸\n\nð¤ {user.first_name} | ð {user.id}\n\nâ Permanently muted due to link in name.",
                reply_markup=keyboard
            )
        except:
            pass
        return

    # NORMAL check â link in bio or message
    if has_link(msg_text) or has_link(await get_bio(context, user_id)):
        if not has_link(user.first_name):  # Already muted above
            try:
                await update.message.delete()
            except:
                pass

            doc = await warnings_col.find_one({"_id": user_id})
            count = (doc["count"] if doc else 0) + 1
            await warnings_col.update_one({"_id": user_id}, {"$set": {"count": count}}, upsert=True)

            if count < 4:
                warn_msg = f"â ï¸ {user.first_name}, links are not allowed in your bio or message ! Warning {count}/3"
                try:
                    await chat.send_message(warn_msg)
                    await context.bot.send_message(user_id, warn_msg)
                except:
                    pass
            else:
                mute_duration = await get_mute_duration()
                until = datetime.utcnow() + timedelta(hours=mute_duration)
                try:
                    await context.bot.restrict_chat_member(
                        chat_id=chat_id,
                        user_id=user_id,
                        permissions=ChatPermissions(can_send_messages=False),
                        until_date=until
                    )
                    channel_id, channel_link = await get_update_channel()
                    keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton("ð Update Channel", url=channel_link)],
                        [InlineKeyboardButton("ð Unmute", url=f"https://t.me/{context.bot.username}")]
                    ])
                    msg = f"âï¸ Bio mute âï¸\n\nð¤ {user.first_name} | ð {user.id}\n\nâ Muted for {mute_duration} hour(s)."
                    await chat.send_message(msg, reply_markup=keyboard)
                    await context.bot.send_message(user_id, msg, reply_markup=keyboard)
                    await warnings_col.update_one({"_id": user_id}, {"$set": {"count": 0}}, upsert=True)
                except:
                    pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat = update.effective_chat

    if chat.type in ["group", "supergroup"]:
        await save_group(chat.id)
    else:
        await save_user(user_id)

    channel_id, channel_link = await get_update_channel()
    try:
        member = await context.bot.get_chat_member(channel_id, user_id)
        if member.status not in ["member", "administrator", "creator"]:
            raise Exception()
    except:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("ð Join Update Channel", url=channel_link)]
        ])
        return await update.message.reply_text(
            "ð Please join the update channel to use the bot.",
            reply_markup=keyboard
        )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("â Add Me To Group", url=f"https://t.me/{context.bot.username}?startgroup=true")],
        [InlineKeyboardButton("ð Update Channel", url=channel_link)],
        [InlineKeyboardButton("â¹ï¸ Help", callback_data="show_help")]
    ])

    try:
        with open("start.jpg", "rb") as img:
            await context.bot.send_photo(chat.id, img, caption="ð Welcome to BioMuteBot! You're now ready to use the bot. Enjoy the features and stay safe! ð", reply_markup=keyboard)
    except:
        await update.message.reply_text("ð Welcome to BioMuteBot! You're now ready to use the bot. Enjoy the features and stay safe! ð", reply_markup=keyboard)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("""
ð¤ BioMuteBot Help

/start â Show welcome menu
/setmute <hours> â Set global mute duration (owner only)
/broadcast â Send message to all groups + users
/status â Show group/user count
/addforce - Set force join channel by replying to a forwarded message (owner only)
/approve <id> - Approve a user to send links (owner only, can also reply)
/unapprove <id> - Revoke link approval (owner only)
/migrate - Migrate old data to MongoDB (owner only)
/banall <groupid> - Ban all tracked members from a group (owner only)
/help â Show this help
""")


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    if query.data == "show_help":
        await query.answer()
        await help_command(query, context)
    elif query.data.startswith("confirm_banall_"):
        if query.from_user.id != OWNER_ID:
            return await query.answer("ð« Owner only.", show_alert=True)
        await query.answer()
        group_id = int(query.data.split("_")[2])
        await query.edit_message_text(f"â³ Starting mass ban for group `{group_id}`... I will message you when it finishes.", parse_mode="Markdown")
        asyncio.create_task(ban_all_task(context, group_id, query.from_user.id))
    elif query.data == "cancel_banall":
        if query.from_user.id != OWNER_ID:
            return await query.answer("ð« Owner only.", show_alert=True)
        await query.answer()
        await query.edit_message_text("â Mass ban cancelled.")


async def set_mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return await update.message.reply_text("ð« Only bot owner can set mute duration.")
    if len(context.args) != 1 or not context.args[0].isdigit():
        return await update.message.reply_text("â Usage: /setmute <hours>")
    
    hours = int(context.args[0])
    if hours < 2 or hours > 72:
        return await update.message.reply_text("â ï¸ Mute duration must be between 2â72 hours.")
    
    await set_mute_duration(hours)
    await update.message.reply_text(f"â Global mute duration set to {hours} hour(s).")


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    groups = await groups_col.count_documents({})
    users = await users_col.count_documents({})
    await update.message.reply_text(f"ð Groups: {groups}\nð¤ Users: {users}")


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    success = 0
    failed = 0

    reply_msg = update.message.reply_to_message
    text = " ".join(context.args) if not reply_msg else None

    if not reply_msg and not text:
        return await update.message.reply_text("â Please provide text or reply to a message to broadcast.")

    targets = []
    
    async for group in groups_col.find():
        targets.append((group["_id"], False))
    async for user in users_col.find():
        targets.append((user["_id"], True))

    for target_id, is_user in targets:
        try:
            msg_id = None
            if reply_msg:
                msg = await context.bot.copy_message(
                    chat_id=target_id, 
                    from_chat_id=reply_msg.chat.id, 
                    message_id=reply_msg.message_id,
                    reply_markup=reply_msg.reply_markup
                )
                msg_id = msg.message_id
            elif text:
                msg = await context.bot.send_message(target_id, text)
                msg_id = msg.message_id
            else:
                continue
                
            if not is_user and msg_id:
                try:
                    await context.bot.pin_chat_message(chat_id=target_id, message_id=msg_id)
                except:
                    pass
            success += 1
        except Exception as e:
            print(f"[â] Failed to send to {target_id}: {e}")
            failed += 1

    await update.message.reply_text(f"â Broadcast done.\nSuccess: {success} â\nFailed: {failed} â")


async def migrate_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return await update.message.reply_text("ð« Only bot owner can migrate data.")
    
    msg = await update.message.reply_text("â³ Starting migration from files to MongoDB...")
    
    users_migrated = 0
    groups_migrated = 0
    
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            for line in f:
                uid = line.strip()
                if uid:
                    await save_user(int(uid))
                    users_migrated += 1

    if os.path.exists(GROUPS_FILE):
        with open(GROUPS_FILE, "r") as f:
            for line in f:
                gid = line.strip()
                if gid:
                    await save_group(int(gid))
                    groups_migrated += 1
                    
    await msg.edit_text(f"â Migration Complete!\nð¤ Users migrated: {users_migrated}\nð Groups migrated: {groups_migrated}")


async def add_force(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return await update.message.reply_text("ð« Only bot owner can set the force join channel.")
        
    if not update.message.reply_to_message:
        return await update.message.reply_text("â ï¸ Please reply to a forwarded message from the channel.")
        
    replied = update.message.reply_to_message
    
    chat_id = None
    if getattr(replied, 'forward_origin', None) and hasattr(replied.forward_origin, 'chat'):
        chat_id = replied.forward_origin.chat.id
    elif replied.forward_from_chat:
        chat_id = replied.forward_from_chat.id
        
    if not chat_id:
        return await update.message.reply_text("â Could not detect channel from the forwarded message.")
        
    invite_link = None
    if context.args:
        invite_link = context.args[0]
    else:
        try:
            invite_link = await context.bot.export_chat_invite_link(chat_id)
        except Exception as e:
            invite_link = f"https://t.me/{str(chat_id).lstrip('-100')}"
            await update.message.reply_text(f"â ï¸ Could not generate invite link automatically (Make sure Bot is admin in the channel). Please provide the link manually:\n`/addforce <invite_link>`", parse_mode="Markdown")

    await set_update_channel(chat_id, invite_link)
    await update.message.reply_text(f"â Force-join channel updated!\nID: `{chat_id}`\nLink: {invite_link}", parse_mode="Markdown")

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return await update.message.reply_text("ð« Only bot owner can approve users.")
    
    target_id = None
    if update.message.reply_to_message:
        target_id = update.message.reply_to_message.from_user.id
    elif context.args and context.args[0].lstrip('-').isdigit():
        target_id = int(context.args[0])
        
    if not target_id:
        return await update.message.reply_text("â Please provide a user ID or reply to their message.\nUsage: `/approve <id>`", parse_mode="Markdown")
        
    await approve_user(target_id)
    await update.message.reply_text(f"â User `{target_id}` has been approved to send links!", parse_mode="Markdown")

async def unapprove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return await update.message.reply_text("ð« Only bot owner can unapprove users.")
    
    target_id = None
    if update.message.reply_to_message:
        target_id = update.message.reply_to_message.from_user.id
    elif context.args and context.args[0].lstrip('-').isdigit():
        target_id = int(context.args[0])
        
    if not target_id:
        return await update.message.reply_text("â Please provide a user ID or reply to their message.\nUsage: `/unapprove <id>`", parse_mode="Markdown")
        
    await unapprove_user(target_id)
    await update.message.reply_text(f"â User `{target_id}` has been unapproved. They can no longer send links.", parse_mode="Markdown")

async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return await update.message.reply_text("ð« Only bot owner can restart the bot.")
    
    await update.message.reply_text("ð Restarting bot... Please wait.")
    await asyncio.sleep(1) # Give it time to send the message
    
    try:
        os.execv(sys.executable, [sys.executable] + sys.argv)
    except Exception:
        import subprocess
        subprocess.Popen([sys.executable] + sys.argv)
        os._exit(0)

async def ban_all_task(context: ContextTypes.DEFAULT_TYPE, group_id: int, owner_id: int):
    import subprocess
    subprocess.Popen([sys.executable, "mass_ban.py", BOT_TOKEN, str(group_id), str(owner_id)])

async def banall_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return await update.message.reply_text("ð« Only bot owner can use this.")
        
    if len(context.args) != 1 or not context.args[0].lstrip('-').isdigit():
        return await update.message.reply_text("â Usage: `/banall <group_id>`", parse_mode="Markdown")
        
    group_id = int(context.args[0])
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("ð¥ NUKE (Ban All)", callback_data=f"confirm_banall_{group_id}"),
            InlineKeyboardButton("â Cancel", callback_data="cancel_banall")
        ]
    ])
    
    await update.message.reply_text(
        f"â ï¸ **WARNING: MTPROTO SCRAPER** â ï¸\n\nAre you absolutely sure you want to scrape and permanently ban **EVERY SINGLE EXISTING MEMBER** from group `{group_id}`?\nThis action cannot be undone.",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

async def main():
    print("ð¤ Bot starting...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("setmute", set_mute))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("migrate", migrate_data))
    app.add_handler(CommandHandler("addforce", add_force))
    app.add_handler(CommandHandler("approve", approve))
    app.add_handler(CommandHandler("unapprove", unapprove))
    # app.add_handler(CommandHandler("restart", restart))  # Disabled for now
    app.add_handler(CommandHandler("banall", banall_command))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.ALL, check_user))

    await app.initialize()
    await app.start()
    print("â Bot running...")
    await app.updater.start_polling()
    await asyncio.Event().wait()


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
