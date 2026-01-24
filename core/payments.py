# core/payments.py
from datetime import datetime

# pending payments
PENDING_PAYMENTS = {}   # uid -> {plan, days, time}

# owner payment config
PAYMENT_CONFIG = {
    "upi": "NOT SET",
    "binance": "NOT SET",
    "trc20": "NOT SET",
    "bep20": "NOT SET"
}

def set_payment_config(method, value):
    PAYMENT_CONFIG[method] = value

def get_payment_text():
    return (
        "💰 Payment Details\n\n"
        f"🏦 UPI: {PAYMENT_CONFIG['upi']}\n"
        f"🟡 Binance: {PAYMENT_CONFIG['binance']}\n"
        f"🔴 USDT TRC20: {PAYMENT_CONFIG['trc20']}\n"
        f"🟢 USDT BEP20: {PAYMENT_CONFIG['bep20']}\n\n"
        "📸 Payment ke baad screenshot bhejo"
    )

def create_payment(uid, days):
    PENDING_PAYMENTS[uid] = {
        "days": days,
        "time": datetime.now()
    }

def has_pending(uid):
    return uid in PENDING_PAYMENTS

def pop_payment(uid):
    return PENDING_PAYMENTS.pop(uid, None)

def any_pending():
    return next(iter(PENDING_PAYMENTS), None)
