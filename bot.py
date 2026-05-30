import asyncio
from telethon import TelegramClient
import random
from aiohttp import web
import os

api_id = 37085876
api_hash = 'e394b3c45e0ce293c2686d798b136976'
bot_token = '8945670254:AAGTxoEoT6pQ-5dhDjIYPpAE3f0vwCpiX0w'

client = TelegramClient('paraxtr_bot_session', api_id, api_hash)
hedef_grup = '@testparaxtr' # Buraya asıl reklam atacağın hedefi veya kendi test grubunu yaz

reklam_metinleri = [
    "🚀 İnternetten ek gelir mi arıyorsun? ParaXTR ile ankete katıl, oyun oyna, reklam izle ve anında kazanmaya başla! Hemen incele: https://ParaXTR.com",
    "💸 Boş vakitlerini nakde çevir! ParaXTR sisteminde anket doldurarak, mobil oyun oynayarak veya sadece reklam izleyerek kazanç sağlayabilirsin. Detaylar burada: https://ParaXTR.com",
    "🔥 Sadece basit görevler yaparak para kazanmak mümkün! ParaXTR'ye katıl; görevleri tamamla, oyun oyna, reklam izle ve kendi işinin patronu ol: https://ParaXTR.com"
]

# Bulut sistemini kandıracak sahte web sayfamız
async def sahte_site(request):
    return web.Response(text="ParaXTR Botu Sapasağlam Çalışıyor!")

async def web_sunucusu_baslat():
    app = web.Application()
    app.router.add_get('/', sahte_site)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"🌐 Sahte web sunucusu {port} portunda uyandırma için hazırlandı.")

# Asıl bot döngümüz
async def bot_dongusu():
    await client.start(bot_token=bot_token)
    print("🤖 ParaXTR Resmi Botu Aktif! Hedefe sızıldı, operasyon başlıyor...")
    
    while True:
        try:
            secilen_metin = random.choice(reklam_metinleri)
            await client.send_message(hedef_grup, secilen_metin)
            print(f"✅ Reklam başarıyla fırlatıldı: {hedef_grup}")
            
            bekleme = random.randint(600, 900)
            print(f"⏳ {bekleme} saniye beklemedeyiz...\n")
            await asyncio.sleep(bekleme)
            
        except Exception as e:
            print(f"❌ Mesaj atılamadı: {e}")
            await asyncio.sleep(60)

async def ana_sistem():
    # Hem sahte siteyi hem botu aynı anda çalıştırıyoruz
    await asyncio.gather(web_sunucusu_baslat(), bot_dongusu())

if __name__ == '__main__':
    asyncio.run(ana_sistem())