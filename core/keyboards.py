from telegram import ReplyKeyboardMarkup

def kb(rows):
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)

def main_kb(is_owner=False):
    rows = [
        ["💳 Subscription", "📊 Status"],
        ["📦 ZIP", "⚙️ Setup"],
        ["🚀 Start", "⛔ Stop"],
        ["❓ Help", "⬅️ Back"]
    ]
    if is_owner:
        rows.insert(0, ["👑 Owner Panel"])
    return kb(rows)

def sub_kb():
    return kb([["🗓 Weekly", "📅 Monthly"], ["⬅️ Back"]])

def zip_kb():
    return kb([["📤 Upload ZIP", "🗑 Withdraw ZIP"], ["⬅️ Back"]])

def setup_kb():
    return kb([["✍ Set Message", "⏱ Set Time"], ["⬅️ Back"]])

def owner_kb():
    return kb([
        ["💰 Payment Settings", "💳 Pending Payments"],
        ["⚙️ System Control", "📊 Reports"],
        ["⬅️ Back"]
    ])
