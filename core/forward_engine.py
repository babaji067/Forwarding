# core/forward_engine.py
import asyncio

RUNNING = {}   # uid -> task

async def forward_loop(bot, uid, chat_id, message, interval):
    try:
        while True:
            await bot.send_message(chat_id, message)
            await asyncio.sleep(interval * 60)
    except asyncio.CancelledError:
        pass

def start_forward(bot, uid, chat_id, message, interval):
    if uid in RUNNING:
        return False
    task = asyncio.create_task(
        forward_loop(bot, uid, chat_id, message, interval)
    )
    RUNNING[uid] = task
    return True

def stop_forward(uid):
    task = RUNNING.pop(uid, None)
    if task:
        task.cancel()
        return True
    return False

def is_running(uid):
    return uid in RUNNING
