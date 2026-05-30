import os
import sys
import asyncio
import random
from telethon import TelegramClient
from telethon.sessions import StringSession
from aiohttp import web

# Log sistemini zorla aktifleştir
print("Bot baslatiliyor...")
sys.stdout.flush()

api_id = 37085876
api_hash = 'e394b3c45e0ce293c2686d798b136976'
bot_token = '8945670254:AAGTxoEoT6pQ-5dhDjIYPpAE3f0vwCpiX0w'

client = TelegramClient(StringSession(), api_id, api_hash)
hedef_grup = '@testparaxtr'

reklam_metinleri = [
    "🚀 İnternetten ek gelir mi arıyorsun? ParaXTR ile ankete katıl, oyun oyna, reklam izle ve anında kazanmaya başla! Hemen incele: https://ParaXTR.com",
    "💸 Boş vakitlerini nakde çevir! ParaXTR sisteminde anket doldurarak, mobil oyun oynayarak veya sadece reklam izleyerek kazanç sağlayabilirsin. Detaylar burada: https://ParaXTR.com",
    "🔥 Sadece basit görevler yaparak para kazanmak mümkün! ParaXTR'ye katıl; görevleri tamamla, oyun oyna, reklam izle ve kendi işinin patronu ol: https://ParaXTR.com"
]

async def sahte_site(request):
    return web.Response(text="ParaXTR Botu aktif ve calisiyor.")

async def web_sunucusu_baslat():
    app = web.Application()
    app.router.add_get('/', sahte_site)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"🌐 Web sunucusu {port} portunda hazir.")
    sys.stdout.flush()

async def bot_dongusu():
    while True: # Hata alsa bile döngü asla ölmesin
        try:
            if not client.is_connected():
                await client.start(bot_token=bot_token)
            
            print("🤖 Bot aktif ve reklam firlatmaya hazir!")
            sys.stdout.flush()
            
            while True:
                metin = random.choice(reklam_metinleri)
                await client.send_message(hedef_grup, metin)
                print(f"✅ Mesaj gonderildi: {hedef_grup}")
                sys.stdout.flush()
                await asyncio.sleep(random.randint(600, 900))
        except Exception as e:
            print(f"❌ Hata yakalandi, 30sn sonra yeniden deneniyor: {e}")
            sys.stdout.flush()
            await asyncio.sleep(30)

async def ana_sistem():
    await asyncio.gather(web_sunucusu_baslat(), bot_dongusu())

if __name__ == '__main__':
    asyncio.run(ana_sistem())
