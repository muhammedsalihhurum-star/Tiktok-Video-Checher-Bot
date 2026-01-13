import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
import datetime
import ffmpeg
import time
import sys
from flask import Flask
from threading import Thread
import os

# SENİN TOKENIN
BOT_TOKEN = '8584063240:AAFlpws7pLka-2dsxxahU7NSDJGJ2cdBGbU'
bot = telebot.TeleBot(BOT_TOKEN)

TIKWM_API_URL = "https://tikwm.com/api/"
CHANNEL_USERNAME = "@kuronai60"  # Zorunlu katılınacak kanal

# --- DİL AYARLARI VE SÖZLÜK ---
user_prefs = {}  

LANGUAGES = {
    "TR": {
        "welcome": "Lütfen bir dil seçin / Please select a language:",
        "lang_set": "✅ Dil Türkçe olarak ayarlandı! TikTok linki gönder.",
        "analyzing": "🚀 **Analiz Başlatılıyor...**",
        "loading_1": "Sunucuya bağlanılıyor...",
        "loading_2": "Kimlik ve Bölge verileri alınıyor...",
        "loading_3": "Teknik analiz yapılıyor...",
        "loading_4": "Dashboard oluşturuldu!",
        "desc_header": "📝 **Video Açıklaması**",
        "no_desc": "Açıklama yok.",
        "id_region_header": "🆔 **Kimlik & Bölge**",
        "region": "Bölge",
        "date": "Tarih",
        "stats_header": "📊 **Etkileşim**",
        "web_ver": "🎬 Kaynak Kalitesi",
        "mobile_ver": "📱 **Mobil Sürüm **",
        "quality": "Kalite",
        "res": "Çözün.",
        "flow": "Akış",
        "file": "Dosya",
        "publisher": "👤 **Yayıncı:**",
        "btn_download": "📥 İndir",
        "btn_music": "🎵 Müzik",
        "btn_profile": "🔗 Profil",
        "err_not_found": "❌ Video bulunamadı.",
        "err_general": "❌ Hata:",
        "sub_warning_text": "⚠️ **Botu kullanmak için kanala katılmalısınız!**\n\nLütfen aşağıdaki butona basarak kanala katılın ve ardından 'Kontrol Et' butonuna basın.",
        "btn_join": "📢 Kanala Katıl",
        "btn_check": "✅ Kontrol Et",
        "not_joined_alert": "❌ Henüz kanala katılmamışsınız!",
        "thanks": "✅ Teşekkürler! Link gönderebilirsiniz.",
        "link_warning": "⚠️ Lütfen geçerli bir TikTok bağlantısı gönderin."  # <-- BU SATIRI EKLE
    },
    "EN": {
        "welcome": "Please select a language:",
        "lang_set": "✅ Language set to English! Send a TikTok link.",
        "analyzing": "🚀 **Starting Analysis...**",
        "loading_1": "Connecting to server...",
        "loading_2": "Fetching ID and Region data...",
        "loading_3": "Performing technical analysis...",
        "loading_4": "Dashboard created!",
        "desc_header": "📝 **Video Description**",
        "no_desc": "No description.",
        "id_region_header": "🆔 **ID & Region**",
        "region": "Region",
        "date": "Date",
        "stats_header": "📊 **Engagement**",
        "web_ver": "🎬 Source Quality",
        "mobile_ver": "📱 **Mobile Version **",
        "quality": "Quality",
        "res": "Res.",
        "flow": "Flow",
        "file": "File",
        "publisher": "👤 **Publisher:**",
        "btn_download": "📥 Download",
        "btn_music": "🎵 Music",
        "btn_profile": "🔗 Profile",
        "err_not_found": "❌ Video not found.",
        "err_general": "❌ Error:",
        "sub_warning_text": "⚠️ **You must join the channel to use the bot!**\n\nPlease join the channel using the button below and then press 'Check'.",
        "btn_join": "📢 Join Channel",
        "btn_check": "✅ Check",
        "not_joined_alert": "❌ You have not joined the channel yet!",
        "thanks": "✅ Thank you! You can send a link.",
        "link_warning": "⚠️ Please send a valid TikTok link."  # <-- BU SATIRI EKLE
    },
    "RU": {
        "welcome": "Пожалуйста, выберите язык:",
        "lang_set": "✅ Язык установлен на Русский! Отправьте ссылку TikTok.",
        "analyzing": "🚀 **Начинается анализ...**",
        "loading_1": "Подключение к серверу...",
        "loading_2": "Получение данных ID и региона...",
        "loading_3": "Технический анализ...",
        "loading_4": "Дашборд создан!",
        "desc_header": "📝 **Описание видео**",
        "no_desc": "Нет описания.",
        "id_region_header": "🆔 **ID и Регион**",
        "region": "Регион",
        "date": "Дата",
        "stats_header": "📊 **Статистика**",
        "web_ver": "🎬 Исходное качество",
        "mobile_ver": "📱 **Мобильная версия **",
        "quality": "Качество",
        "res": "Разреш.",
        "flow": "Поток",
        "file": "Файл",
        "publisher": "👤 **Автор:**",
        "btn_download": "📥 Скачать",
        "btn_music": "🎵 Музыка",
        "btn_profile": "🔗 Профиль",
        "err_not_found": "❌ Видео не найдено.",
        "err_general": "❌ Ошибка:",
        "sub_warning_text": "⚠️ **Вы должны присоединиться к каналу, чтобы использовать бота!**\n\nПожалуйста, присоединяйтесь к каналу, используя кнопку ниже, а затем нажмите «Проверить».",
        "btn_join": "📢 Присоединиться",
        "btn_check": "✅ Проверить",
        "not_joined_alert": "❌ Вы еще не присоединились к каналу!",
        "thanks": "✅ Спасибо! Можете отправить ссылку.",
        "link_warning": "⚠️ Пожалуйста, отправьте действительную ссылку на TikTok."  # <-- BU SATIRI EKLE
    }
}

def get_msg(chat_id, key):
    lang = user_prefs.get(chat_id, "TR")
    return LANGUAGES[lang].get(key, key)

# --- YARDIMCI FONKSİYONLAR ---

def check_subscription(user_id):
    """Kullanıcının kanala üye olup olmadığını kontrol eder."""
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if member.status in ['creator', 'administrator', 'member']:
            return True
        return False
    except:
        return False

def send_subscription_warning(chat_id):
    """SEÇİLEN DİLDE uyarı mesajı gönderir."""
    # Buton metinleri seçilen dile göre gelir
    btn_join_text = get_msg(chat_id, "btn_join")
    btn_check_text = get_msg(chat_id, "btn_check")
    warning_text = get_msg(chat_id, "sub_warning_text")

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(btn_join_text, url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}"))
    markup.add(InlineKeyboardButton(btn_check_text, callback_data="check_sub"))
    
    bot.send_message(chat_id, warning_text, reply_markup=markup, parse_mode='Markdown')

def create_stat_bar(value, max_value=1000000, length=8):
    percent = min(1.0, value / max_value)
    filled = int(length * percent)
    if filled == 0 and value > 0: filled = 1
    return '▓' * filled + '░' * (length - filled)

def simulate_loading(chat_id, message_id):
    steps = [
        ("▰▱▱▱▱▱▱▱▱▱", "loading_1"),
        ("▰▰▰▱▱▱▱▱▱▱", "loading_2"),
        ("▰▰▰▰▰▰▰▰▱▱", "loading_3"),
        ("▰▰▰▰▰▰▰▰▰▰", "loading_4")
    ]
    for bar, key in steps:
        try:
            text = get_msg(chat_id, key)
            bot.edit_message_text(f"⏳ **Sistem İşliyor**\n`{bar}`\n_{text}_", chat_id, message_id, parse_mode='Markdown')
            time.sleep(0.3)
        except: pass

def get_video_metadata(video_url):
    if not video_url: return None
    try:
        probe = ffmpeg.probe(video_url)
        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
        if video_stream is None: return None
        avg_frame_rate = video_stream.get('avg_frame_rate', '0/0')
        if '/' in avg_frame_rate:
            num, den = map(int, avg_frame_rate.split('/'))
            fps = float(num) / float(den) if den > 0 else 0
        else:
            fps = float(avg_frame_rate)
        bps = int(video_stream.get('bit_rate', 0) or probe['format'].get('bit_rate', 0))
        bitrate_str = f"{bps / 1_000_000:.1f} Mbps" if bps > 1_000_000 else f"{bps / 1000:.0f} kbps"
        width = video_stream.get('width')
        height = video_stream.get('height')
        short_side = min(width, height)
        if short_side >= 1080: quality = "FHD (1080p)"
        elif short_side >= 720: quality = "HD (720p)"
        else: quality = "SD (480p)"
        return {
            "res": f"{width}x{height}",
            "quality": quality,
            "fps": f"{fps:.0f}", 
            "bitrate": bitrate_str,
            "size_bytes": int(probe['format'].get('size', 0))
        }
    except: return None

def format_number(num):
    if not num: return "0"
    if num > 1000000: return f"{num/1000000:.1f}M"
    if num > 1000: return f"{num/1000:.1f}K"
    return str(num)

def format_size(bytes_size):
    if not bytes_size: return "0 MB"
    return f"{bytes_size / (1024 * 1024):.2f} MB"

def get_date_from_id(video_id):
    try:
        timestamp = int(video_id) >> 32
        return datetime.datetime.fromtimestamp(timestamp).strftime("%d.%m.%Y %H:%M")
    except:
        return "-"

# --- BOT HANDLER ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    # BURADA ABONELİK KONTROLÜ YAPMIYORUZ. ÖNCE DİL SEÇSİN.
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🇹🇷 Türkçe", callback_data="lang_TR"))
    markup.add(InlineKeyboardButton("🇬🇧 English", callback_data="lang_EN"))
    markup.add(InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_RU"))
    
    # 3 dilde "Lütfen dil seçin" yazısı (Tek bir mesajda)
    welcome_text = (
        "🇹🇷 Lütfen bir dil seçin:\n"
        "🇬🇧 Please select a language:\n"
        "🇷🇺 Пожалуйста, выберите язык:"
    )
    bot.reply_to(message, welcome_text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("lang_"))
def callback_language(call):
    # 1. Dili kaydet
    lang_code = call.data.split("_")[1]
    user_prefs[call.message.chat.id] = lang_code
    
    # 2. ŞİMDİ Abonelik kontrolü yap
    if check_subscription(call.from_user.id):
        # Üye ise: Başarı mesajı (Seçilen dilde)
        bot.answer_callback_query(call.id, "✅")
        bot.edit_message_text(LANGUAGES[lang_code]["lang_set"], call.message.chat.id, call.message.message_id)
    else:
        # Üye değilse: Uyarı mesajı (Sadece seçilen dilde!)
        bot.answer_callback_query(call.id, "⚠️")
        bot.delete_message(call.message.chat.id, call.message.message_id) # Önceki dil menüsünü sil
        send_subscription_warning(call.message.chat.id) # Yeni temiz uyarıyı at

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def callback_check_sub(call):
    chat_id = call.message.chat.id
    # Kontrol Et butonuna bastığında:
    if check_subscription(call.from_user.id):
        # Artık üye olmuş
        bot.delete_message(chat_id, call.message.message_id)
        bot.answer_callback_query(call.id, "✅", show_alert=False)
        bot.send_message(chat_id, get_msg(chat_id, "thanks"))
    else:
        # Hala üye değil (Seçilen dilde hata ver)
        alert_text = get_msg(chat_id, "not_joined_alert")
        bot.answer_callback_query(call.id, alert_text, show_alert=True)

@bot.message_handler(func=lambda message: True)
def analyze_video(message):
    cid = message.chat.id
    
    # Varsayılan dil TR (eğer seçmediyse)
    if cid not in user_prefs:
        user_prefs[cid] = "EN"

    # Link attığında da KONTROL ŞART
    if not check_subscription(message.from_user.id):
        send_subscription_warning(cid)
        return

    url = message.text.strip()
    
    # --- DÜZELTİLMİŞ KISIM BAŞLANGIÇ ---
    # Bu satırlar da üsttekilerle aynı hizada (içeride) olmalı
    if "tiktok.com" not in url:
        return 
    # --- DÜZELTİLMİŞ KISIM BİTİŞ ---

    # (Buradan sonra kodun devamı geliyorsa o da aynı hizada olmalı)

    msg = bot.reply_to(message, get_msg(cid, "analyzing"), parse_mode='Markdown')

    try:
        simulate_loading(cid, msg.message_id)
        response = requests.post(TIKWM_API_URL, data={"url": url, "hd": 1}, headers={"User-Agent": "Mozilla/5.0"}).json()
        
        if response.get("code") == 0:
            data = response.get("data", {})
            browser_url = data.get("play")  
            mobile_url = data.get("hdplay")
            
            browser_meta = get_video_metadata(browser_url)
            mobile_meta = get_video_metadata(mobile_url) if (mobile_url and mobile_url != browser_url) else browser_meta

            views = data.get("play_count", 0)
            likes = data.get("digg_count", 0)
            view_bar = create_stat_bar(views, 100000)
            like_bar = create_stat_bar(likes, 50000)

            def safe(meta, key): return meta.get(key, "?") if meta else "?"
            def size(meta): return format_size(meta.get("size_bytes", 0)) if meta else "?"

            video_id = data.get("id")
            creation_date = get_date_from_id(video_id)
            region = data.get("region", "Global").upper()
            title = data.get("title", "")
            if not title: title = get_msg(cid, "no_desc")

            caption = (
                f"{get_msg(cid, 'desc_header')}\n_“{title}”_\n\n"
                f"{get_msg(cid, 'id_region_header')}\n├ 🔢 ID: `{video_id}`\n├ 🌍 {get_msg(cid, 'region')}: `{region}`\n└ 📅 {get_msg(cid, 'date')}: `{creation_date}`\n\n"
                f"{get_msg(cid, 'stats_header')}\n`👁 {format_number(views):<6}` {view_bar}\n`♥ {format_number(likes):<6}` {like_bar}\n\n"
                f"{get_msg(cid, 'web_ver')}\n┌ 💎 {get_msg(cid, 'quality')} : `{safe(browser_meta, 'quality')}`\n├ 📐 {get_msg(cid, 'res')} : `{safe(browser_meta, 'res')}`\n├ 🚀 {get_msg(cid, 'Fps')}   : `{safe(browser_meta, 'fps')} FPS`\n└ 💾 {get_msg(cid, 'file')}  : `{size(browser_meta)}`\n\n"
                f"{get_msg(cid, 'mobile_ver')}\n┌ 💎 {get_msg(cid, 'quality')} : `{safe(mobile_meta, 'quality')}`\n├ 📐 {get_msg(cid, 'res')} : `{safe(mobile_meta, 'res')}`\n├ 🚀 {get_msg(cid, 'Fps')}   : `{safe(mobile_meta, 'fps')} FPS`\n└ 💾 {get_msg(cid, 'file')}  : `{size(mobile_meta)}`\n\n"
                f"{get_msg(cid, 'publisher')} `@{data.get('author', {}).get('unique_id')}`"
            )
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton(f"{get_msg(cid, 'btn_download')} (HD - {size(mobile_meta)})", url=mobile_url))
            markup.row(InlineKeyboardButton(get_msg(cid, 'btn_music'), url=data.get("music")), InlineKeyboardButton(get_msg(cid, 'btn_profile'), url=f"https://www.tiktok.com/@{data.get('author', {}).get('unique_id')}"))

            if data.get("cover"):
                bot.delete_message(message.chat.id, msg.message_id)
                bot.send_photo(message.chat.id, data.get("cover"), caption=caption, parse_mode='Markdown', reply_markup=markup)
            else:
                bot.edit_message_text(caption, message.chat.id, msg.message_id, parse_mode='Markdown', reply_markup=markup)
        else:
            bot.edit_message_text(get_msg(cid, "err_not_found"), message.chat.id, msg.message_id)
    except Exception as e:
        bot.edit_message_text(f"{get_msg(cid, 'err_general')} {str(e)[:50]}", message.chat.id, msg.message_id)
# --- FLASK KEEP_ALIVE ---
app = Flask('')

@app.route('/')
def home():
    return "Bot Calisiyor! / Bot is Running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- ÇALIŞTIRMA ---
print("Bot aktif...")
keep_alive()  # Flask sunucusunu başlat

bot.infinity_polling() # Botu başlat




