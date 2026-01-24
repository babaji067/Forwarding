# core/zip_manager.py

ZIP_STORE = {}   # uid -> file_name

def upload_zip(uid, file_name):
    ZIP_STORE[uid] = file_name

def withdraw_zip(uid):
    return ZIP_STORE.pop(uid, None)

def has_zip(uid):
    return uid in ZIP_STORE

def get_zip(uid):
    return ZIP_STORE.get(uid)
