from collections import defaultdict

USERS = defaultdict(dict)

def get_user(uid):
    return USERS[uid]
