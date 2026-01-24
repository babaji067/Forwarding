from telegram import Update
from telegram.ext import (
    Application, CommandHandler,
    MessageHandler, ContextTypes, filters
)

from config import BOT_TOKEN, OWNER_ID
from core.users import get_user
from core.navigation import reset, push, pop, current
from core.keyboards import (
    main_kb, sub_kb, zip_kb,
    setup_kb, owner_kb
)

def is_owner(uid):
    return uid == OWNER_ID

# ---------- START ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    reset(uid)
    get_user(uid)
    await update.message.reply_text(
        "🤖 Forwarding System (Core Ready)\n\nMenu:",
        reply_markup=main_kb(is_owner(uid))
    )

# ---------- ROUTER ----------
async def router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.strip()
    state = current(uid)

    # BACK (step-by-step)
    if text == "⬅️ Back":
        state = pop(uid)
        await show_state(update, state, uid)
        return

    # MAIN
    if state == "MAIN":
        if text == "💳 Subscription":
            push(uid, "SUB")
            await update.message.reply_text("Choose plan:", reply_markup=sub_kb())

        elif text == "📊 Status":
            await update.message.reply_text("Status: No subscription yet", reply_markup=main_kb(is_owner(uid)))

        elif text == "📦 ZIP":
            push(uid, "ZIP")
            await update.message.reply_text("ZIP Menu:", reply_markup=zip_kb())

        elif text == "⚙️ Setup":
            push(uid, "SETUP")
            await update.message.reply_text("Setup Menu:", reply_markup=setup_kb())

        elif text == "🚀 Start":
            await update.message.reply_text("▶️ Forward START (logic next commit)", reply_markup=main_kb(is_owner(uid)))

        elif text == "⛔ Stop":
            await update.message.reply_text("⛔ Forward STOP", reply_markup=main_kb(is_owner(uid)))

        elif text == "❓ Help":
            await update.message.reply_text("Use buttons. Back is step-by-step.", reply_markup=main_kb(is_owner(uid)))

        elif text == "👑 Owner Panel" and is_owner(uid):
            push(uid, "OWNER")
            await update.message.reply_text("Owner Panel:", reply_markup=owner_kb())

        else:
            await update.message.reply_text("Select from menu.", reply_markup=main_kb(is_owner(uid)))
        return

    # SUB
    if state == "SUB":
        await update.message.reply_text("Subscription flow in next commit.", reply_markup=sub_kb())
        return

    # ZIP
    if state == "ZIP":
        await update.message.reply_text("ZIP logic in next commit.", reply_markup=zip_kb())
        return

    # SETUP
    if state == "SETUP":
        await update.message.reply_text("Setup logic in next commit.", reply_markup=setup_kb())
        return

    # OWNER
    if state == "OWNER":
        await update.message.reply_text("Owner features next commit.", reply_markup=owner_kb())
        return

async def show_state(update, state, uid):
    if state == "MAIN":
        await update.message.reply_text("Main Menu:", reply_markup=main_kb(is_owner(uid)))
    elif state == "SUB":
        await update.message.reply_text("Choose plan:", reply_markup=sub_kb())
    elif state == "ZIP":
        await update.message.reply_text("ZIP Menu:", reply_markup=zip_kb())
    elif state == "SETUP":
        await update.message.reply_text("Setup Menu:", reply_markup=setup_kb())
    elif state == "OWNER":
        await update.message.reply_text("Owner Panel:", reply_markup=owner_kb())

# ---------- MAIN ----------
app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT, router))

print("🤖 Commit-1 Core System Running")
app.run_polling()
