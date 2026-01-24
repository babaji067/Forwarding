from collections import defaultdict

NAV = defaultdict(list)

def reset(uid):
    NAV[uid].clear()
    NAV[uid].append("MAIN")

def push(uid, state):
    NAV[uid].append(state)

def pop(uid):
    if NAV[uid]:
        NAV[uid].pop()
    return NAV[uid][-1] if NAV[uid] else "MAIN"

def current(uid):
    return NAV[uid][-1] if NAV[uid] else "MAIN"
