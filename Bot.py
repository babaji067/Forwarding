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
    setup_kb, owner_kb,
    payset_kb, pending_kb
)

from core.payments import (
    set_payment_config, get_payment_text,
    create_payment, has_pending,
    pop_payment, any_pending
)

from core.subscription import (
    activate, is_active, days_left
)

from core.zip_manager import (
    upload_zip, withdraw_zip,
    has_zip, get_zip
)

from core.forward_engine import (
    start_forward, stop_forward, is_running
)

# ================= HELPERS =================
def is_owner(uid):
    return uid == OWNER_ID


# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    reset(uid)
    get_user(uid)

    await update.message.reply_text(
        "🤖 Forwarding Automation Bot (Commit-3)\n\nMenu:",
        reply_markup=main_kb(is_owner(uid))
    )


# ================= ROUTER =================
async def router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.strip()
    user = get_user(uid)
    state = current(uid)

    # ---------- BACK ----------
    if text == "⬅️ Back":
        state = pop(uid)
        await show_state(update, state, uid)
        return

    # ---------- MAIN ----------
    if state == "MAIN":
        if text == "💳 Subscription":
            push(uid, "SUB")
            await update.message.reply_text("Choose plan:", reply_markup=sub_kb())

        elif text == "📊 Status":
            if is_active(uid):
                msg = f"✅ Active\n⏳ {days_left(uid)} days left"
            else:
                msg = "❌ No active subscription"
            await update.message.reply_text(msg, reply_markup=main_kb(is_owner(uid)))

        elif text == "📦 ZIP":
            push(uid, "ZIP")
            await update.message.reply_text("ZIP Menu:", reply_markup=zip_kb())

        elif text == "⚙️ Setup":
            push(uid, "SETUP")
            await update.message.reply_text("Setup Menu:", reply_markup=setup_kb())

        elif text == "🚀 Start":
            if not is_active(uid):
                await update.message.reply_text(
                    "❌ Subscription required",
                    reply_markup=main_kb(is_owner(uid))
                )
                return

            msg = user.get("message")
            interval = user.get("interval")

            if not msg or not interval:
                await update.message.reply_text(
                    "❌ Set message & time first",
                    reply_markup=main_kb(is_owner(uid))
                )
                return

            if start_forward(context.bot, uid, update.effective_chat.id, msg, interval):
                await update.message.reply_text(
                    "▶️ Forward STARTED",
                    reply_markup=main_kb(is_owner(uid))
                )
            else:
                await update.message.reply_text(
                    "⚠️ Already running",
                    reply_markup=main_kb(is_owner(uid))
                )

        elif text == "⛔ Stop":
            if stop_forward(uid):
                await update.message.reply_text(
                    "⛔ Forward STOPPED",
                    reply_markup=main_kb(is_owner(uid))
                )
            else:
                await update.message.reply_text(
                    "⚠️ Not running",
                    reply_markup=main_kb(is_owner(uid))
                )

        elif text == "👑 Owner Panel" and is_owner(uid):
            push(uid, "OWNER")
            await update.message.reply_text(
                "Owner Panel:",
                reply_markup=owner_kb()
            )

        else:
            await update.message.reply_text(
                "Choose from menu",
                reply_markup=main_kb(is_owner(uid))
            )
        return

    # ---------- SUB ----------
    if state == "SUB":
        if text == "🗓 Weekly":
            create_payment(uid, 7)
            await update.message.reply_text(get_payment_text())

        elif text == "📅 Monthly":
            create_payment(uid, 30)
            await update.message.reply_text(get_payment_text())
        return

    # ---------- ZIP ----------
    if state == "ZIP":
        if text == "📤 Upload ZIP":
            user["await_zip"] = True
            await update.message.reply_text("Send ZIP file")

        elif text == "🗑 Withdraw ZIP":
            z = withdraw_zip(uid)
            if z:
                await update.message.reply_text(f"ZIP removed: {z}")
            else:
                await update.message.reply_text("No ZIP found")
        return

    # ---------- SETUP ----------
    if state == "SETUP":
        if text == "✍ Set Message":
            user["await_msg"] = True
            await update.message.reply_text("Send message text")

        elif text == "⏱ Set Time":
            user["await_time"] = True
            await update.message.reply_text("Send interval in minutes")
        return

    # ---------- OWNER ----------
    if state == "OWNER" and is_owner(uid):
        if text == "💰 Payment Settings":
            push(uid, "PAYSET")
            await update.message.reply_text(
                "Select payment method:",
                reply_markup=payset_kb()
            )

        elif text == "💳 Pending Payments":
            push(uid, "PENDING")
            pid = any_pending()
            if pid:
                await update.message.reply_text(
                    f"Pending from user: {pid}",
                    reply_markup=pending_kb()
                )
            else:
                await update.message.reply_text(
                    "No pending",
                    reply_markup=owner_kb()
                )
        return

    # ---------- PAYSET ----------
    if state == "PAYSET" and is_owner(uid):
        user["set_pay"] = text
        await update.message.reply_text("Send value")
        return

    # ---------- PENDING ----------
    if state == "PENDING" and is_owner(uid):
        pid = any_pending()
        if not pid:
            await update.message.reply_text("No pending", reply_markup=owner_kb())
            return

        if text == "✅ Approve":
            info = pop_payment(pid)
            activate(pid, info["days"])
            await update.message.reply_text("Approved", reply_markup=owner_kb())

        elif text == "❌ Reject":
            pop_payment(pid)
            await update.message.reply_text("Rejected", reply_markup=owner_kb())
        return


# ================= FREE INPUT =================
async def free(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user = get_user(uid)

    # ZIP upload
    if user.get("await_zip") and update.message.document:
        upload_zip(uid, update.message.document.file_name)
        user["await_zip"] = False
        await update.message.reply_text("✅ ZIP uploaded")
        return

    # message set
    if user.get("await_msg"):
        user["message"] = update.message.text
        user["await_msg"] = False
        await update.message.reply_text("✅ Message saved")
        return

    # time set
    if user.get("await_time"):
        try:
            user["interval"] = int(update.message.text)
            await update.message.reply_text("✅ Time saved")
        except:
            await update.message.reply_text("Send number only")
        user["await_time"] = False
        return

    # payment proof
    if has_pending(uid):
        await update.message.reply_text("✅ Payment received, waiting approval")
        return

    # owner set payment config
    if is_owner(uid) and user.get("set_pay"):
        if user["set_pay"] == "🏦 Set UPI":
            set_payment_config("upi", update.message.text)
        elif user["set_pay"] == "🟡 Set Binance":
            set_payment_config("binance", update.message.text)
        elif user["set_pay"] == "🔴 Set TRC20":
            set_payment_config("trc20", update.message.text)
        elif user["set_pay"] == "🟢 Set BEP20":
            set_payment_config("bep20", update.message.text)

        user["set_pay"] = None
        await update.message.reply_text("✅ Saved")
        return


# ================= SHOW STATE =================
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
    elif state == "PAYSET":
        await update.message.reply_text("Payment Settings:", reply_markup=payset_kb())
    elif state == "PENDING":
        await update.message.reply_text("Pending:", reply_markup=pending_kb())


# ================= MAIN =================
app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT | filters.Document.ALL, router))
app.add_handler(MessageHandler(filters.ALL, free))

print("🤖 Commit-3 FULL SYSTEM RUNNING")
app.run_polling()
