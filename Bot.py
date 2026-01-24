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
    set_payment_config,
    get_payment_text,
    create_payment,
    has_pending,
    pop_payment,
    any_pending
)

from core.subscription import (
    activate,
    is_active,
    days_left
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
        "🤖 Forwarding Automation Bot\n\nMenu:",
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
            await update.message.reply_text(
                "Choose plan:",
                reply_markup=sub_kb()
            )

        elif text == "📊 Status":
            if is_active(uid):
                left = days_left(uid)
                msg = f"✅ Subscription Active\n⏳ {left} days left"
            else:
                msg = "❌ No active subscription"

            await update.message.reply_text(
                msg,
                reply_markup=main_kb(is_owner(uid))
            )

        elif text == "📦 ZIP":
            push(uid, "ZIP")
            await update.message.reply_text(
                "ZIP Menu:",
                reply_markup=zip_kb()
            )

        elif text == "⚙️ Setup":
            push(uid, "SETUP")
            await update.message.reply_text(
                "Setup Menu:",
                reply_markup=setup_kb()
            )

        elif text == "🚀 Start":
            user["running"] = True
            await update.message.reply_text(
                "▶️ Forward STARTED",
                reply_markup=main_kb(is_owner(uid))
            )

        elif text == "⛔ Stop":
            user["running"] = False
            await update.message.reply_text(
                "⛔ Forward STOPPED",
                reply_markup=main_kb(is_owner(uid))
            )

        elif text == "❓ Help":
            await update.message.reply_text(
                "Use buttons below.\nBack works step-by-step.",
                reply_markup=main_kb(is_owner(uid))
            )

        elif text == "👑 Owner Panel" and is_owner(uid):
            push(uid, "OWNER")
            await update.message.reply_text(
                "👑 Owner Panel:",
                reply_markup=owner_kb()
            )

        else:
            await update.message.reply_text(
                "Choose option from menu.",
                reply_markup=main_kb(is_owner(uid))
            )
        return

    # ---------- SUB (A, B, C) ----------
    if state == "SUB":
        if text == "🗓 Weekly":
            create_payment(uid, 7)
            await update.message.reply_text(
                get_payment_text(),
                reply_markup=[["⬅️ Back"]]
            )

        elif text == "📅 Monthly":
            create_payment(uid, 30)
            await update.message.reply_text(
                get_payment_text(),
                reply_markup=[["⬅️ Back"]]
            )

        else:
            await update.message.reply_text(
                "Choose plan:",
                reply_markup=sub_kb()
            )
        return

    # ---------- ZIP ----------
    if state == "ZIP":
        await update.message.reply_text(
            "ZIP system will be added in Commit-3",
            reply_markup=zip_kb()
        )
        return

    # ---------- SETUP ----------
    if state == "SETUP":
        await update.message.reply_text(
            "Setup features in Commit-3",
            reply_markup=setup_kb()
        )
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
            if not pid:
                await update.message.reply_text(
                    "No pending payments.",
                    reply_markup=owner_kb()
                )
            else:
                await update.message.reply_text(
                    f"Pending payment from user: {pid}",
                    reply_markup=pending_kb()
                )

        elif text == "⚙️ System Control":
            await update.message.reply_text(
                "System OK",
                reply_markup=owner_kb()
            )

        elif text == "📊 Reports":
            await update.message.reply_text(
                "Reports available later",
                reply_markup=owner_kb()
            )
        return

    # ---------- PAYSET (D, E) ----------
    if state == "PAYSET" and is_owner(uid):
        user["set_pay"] = text
        await update.message.reply_text(
            "Send value:",
            reply_markup=[["⬅️ Back"]]
        )
        return

    # ---------- PENDING STATE (F, G) ----------
    if state == "PENDING" and is_owner(uid):
        pid = any_pending()
        if not pid:
            await update.message.reply_text(
                "No pending payments.",
                reply_markup=owner_kb()
            )
            return

        if text == "✅ Approve":
            info = pop_payment(pid)
            activate(pid, info["days"])
            await update.message.reply_text(
                "✅ Subscription Approved",
                reply_markup=owner_kb()
            )

        elif text == "❌ Reject":
            pop_payment(pid)
            await update.message.reply_text(
                "❌ Payment Rejected",
                reply_markup=owner_kb()
            )
        return


# ================= FREE INPUT =================
async def free(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user = get_user(uid)
    text = update.message.text

    # USER sends payment proof
    if has_pending(uid):
        await update.message.reply_text(
            "✅ Payment received.\nWaiting for owner approval.",
            reply_markup=main_kb(is_owner(uid))
        )
        return

    # OWNER saves payment config
    if is_owner(uid) and user.get("set_pay"):
        key = user["set_pay"]

        if key == "🏦 Set UPI":
            set_payment_config("upi", text)
        elif key == "🟡 Set Binance":
            set_payment_config("binance", text)
        elif key == "🔴 Set TRC20":
            set_payment_config("trc20", text)
        elif key == "🟢 Set BEP20":
            set_payment_config("bep20", text)

        user["set_pay"] = None
        await update.message.reply_text(
            "✅ Payment method saved",
            reply_markup=owner_kb()
        )
        return


# ================= SHOW STATE =================
async def show_state(update: Update, state: str, uid: int):
    if state == "MAIN":
        await update.message.reply_text(
            "Main Menu:",
            reply_markup=main_kb(is_owner(uid))
        )
    elif state == "SUB":
        await update.message.reply_text(
            "Choose plan:",
            reply_markup=sub_kb()
        )
    elif state == "ZIP":
        await update.message.reply_text(
            "ZIP Menu:",
            reply_markup=zip_kb()
        )
    elif state == "SETUP":
        await update.message.reply_text(
            "Setup Menu:",
            reply_markup=setup_kb()
        )
    elif state == "OWNER":
        await update.message.reply_text(
            "Owner Panel:",
            reply_markup=owner_kb()
        )
    elif state == "PAYSET":
        await update.message.reply_text(
            "Payment Settings:",
            reply_markup=payset_kb()
        )
    elif state == "PENDING":
        await update.message.reply_text(
            "Pending Payments:",
            reply_markup=pending_kb()
        )


# ================= MAIN =================
app = Application.builder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT, router))
app.add_handler(MessageHandler(filters.ALL, free))

print("🤖 Commit-2 FULL bot.py running (A–G + PENDING)")
app.run_polling()
