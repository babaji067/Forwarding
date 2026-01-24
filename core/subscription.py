# core/subscription.py
from datetime import datetime, timedelta

# active subscriptions
SUBSCRIPTIONS = {}   # uid -> expire_datetime

def activate(uid, days):
    expire = datetime.now() + timedelta(days=days)
    SUBSCRIPTIONS[uid] = expire
    return expire

def is_active(uid):
    exp = SUBSCRIPTIONS.get(uid)
    if not exp:
        return False
    if exp < datetime.now():
        SUBSCRIPTIONS.pop(uid, None)
        return False
    return True

def days_left(uid):
    exp = SUBSCRIPTIONS.get(uid)
    if not exp:
        return 0
    delta = exp - datetime.now()
    return max(delta.days, 0)

def deactivate(uid):
    SUBSCRIPTIONS.pop(uid, None)
