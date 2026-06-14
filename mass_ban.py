import sys
import asyncio
from pyrogram import Client
from pyrogram.errors import FloodWait

BOT_TOKEN = sys.argv[1]
GROUP_ID = int(sys.argv[2])
OWNER_ID = int(sys.argv[3])

API_ID = 6
API_HASH = "eb06d4abfb49dc3eeb1aeb98ae0f581e"

async def main():
    app = Client(
        "ban_scraper",
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=BOT_TOKEN,
        in_memory=True,
        no_updates=True
    )
    
    await app.start()
    
    bot_info = await app.get_me()
    bot_id = bot_info.id
    
    success = 0
    failed = 0
    
    try:
        async for member in app.get_chat_members(GROUP_ID):
            user_id = member.user.id
            if user_id in [OWNER_ID, bot_id]:
                continue
                
            try:
                await app.ban_chat_member(GROUP_ID, user_id)
                success += 1
            except FloodWait as e:
                await asyncio.sleep(e.value)
                try:
                    await app.ban_chat_member(GROUP_ID, user_id)
                    success += 1
                except:
                    failed += 1
            except Exception:
                failed += 1
                
            await asyncio.sleep(0.5)
            
        await app.send_message(OWNER_ID, f"â MTProto Mass-Ban complete for group `{GROUP_ID}`!\nð¨ Banned: {success}\nâ Failed: {failed}")
    except Exception as e:
        await app.send_message(OWNER_ID, f"â Mass-ban scraper failed: {str(e)}")
        
    await app.stop()

if __name__ == "__main__":
    asyncio.run(main())
