from flask import Flask, request, jsonify
import requests
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import datetime
import ffmpeg
import time
import sys
from threading import Thread
import os

# --- 1. FLASK UYGULAMASINI EN BAŞTA BAŞLATIYORUZ ---
app = Flask('')

# --- 2. MOBİL UYGULAMA İÇİN API ---
@app.route('/api/analyze')
def api_analyze():
    url = request.args.get('url')
    
    if not url:
        return jsonify({"success": False, "message": "URL yok"})

    try:
        response = requests.post("https://tikwm.com/api/", data={"url": url, "hd": 1}, headers={"User-Agent": "Mozilla/5.0"}).json()
        
        if response.get("code") == 0:
            data = response.get("data", {})
            browser_url = data.get("play")      
            mobile_url = data.get("hdplay")     
            
            browser_meta = get_video_metadata(browser_url)
            
            if mobile_url and mobile_url != browser_url:
                mobile_meta = get_video_metadata(mobile_url)
            else:
                mobile_meta = browser_meta

            def safe_get(meta, key): return meta.get(key, "?") if meta else "?"
            def safe_size(meta): return meta.get("size_bytes", 0) if meta else 0

            api_response = {
                "success": True,
                "data": {
                    "id": data.get("id"),
                    "region": data.get("region", "Global").upper(),
                    "title": data.get("title", ""),
                    "cover": data.get("cover"),
                    "music": data.get("music"),
                    "author": {
                        "nickname": data.get("author", {}).get("nickname"),
                        "unique_id": data.get("author", {}).get("unique_id"),
                        "avatar": data.get("author", {}).get("avatar")
                    },
                    "stats": {
                        "play": data.get("play_count", 0),
                        "digg": data.get("digg_count", 0),
                        "comment": data.get("comment_count", 0),
                        "share": data.get("share_count", 0)
                    },
                    "create_time": data.get("create_time"),
                    "source_data": {
                        "url": browser_url,
                        "quality": safe_get(browser_meta, 'quality'),
                        "resolution": safe_get(browser_meta, 'res'),
                        "fps": safe_get(browser_meta, 'fps'),
                        "size": safe_size(browser_meta),
                        "bitrate": safe_get(browser_meta, 'bitrate')
                    },
                    "mobile_data": {
                        "url": mobile_url,
                        "quality": safe_get(mobile_meta, 'quality'),
                        "resolution": safe_get(mobile_meta, 'res'),
                        "fps": safe_get(mobile_meta, 'fps'),
                        "size": safe_size(mobile_meta),
                        "bitrate": safe_get(mobile_meta, 'bitrate')
                    }
                }
            }
            return jsonify(api_response)
        else:
             return jsonify({"success": False, "message": "TikWM veriyi bulamadı"})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

# --- 3. TELEGRAM BOT AYARLARI ---
BOT_TOKEN = '8584063240:AAFNRb73LL-9emyfvVrhkZdjoADOOws0uy4'
bot = telebot.TeleBot(BOT_TOKEN)

TIKWM_API_URL = "https://tikwm.com/api/"
CHANNEL_USERNAME = "@kuronai60"  

# --- DİL AYARLARI VE SÖZLÜK ---
user_prefs = {}  

LANGUAGES = {
    "TR": {
        "welcome": "Lütfen bir dil seçin / Please select a language:",
        "engagement": "Etkileşim Oranı",
        "bot_warning": "🚨 **ŞÜPHELİ ETKİLEŞİM:** Like sayısı izlenmeden fazla! (Olası Bot)",
        "lang_set": "✅ Dil Türkçe olarak ayarlandı! TikTok linki gönder.",
        "analyzing": "🚀 **Analiz Başlatılıyor...**",
        "updating": "🔄 **Veriler Güncelleniyor...**", # Yeni
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
        "btn_refresh": "🔄 Güncelle", # Yeni
        "btn_profile": "🔗 Profil",
        "err_not_found": "❌ Video bulunamadı.",
        "err_general": "❌ Hata:",
        "sub_warning_text": "⚠️ **Botu kullanmak için kanala katılmalısınız!**\n\nLütfen aşağıdaki butona basarak kanala katılın ve ardından 'Kontrol Et' butonuna basın.",
        "btn_join": "📢 Kanala Katıl",
        "btn_check": "✅ Kontrol Et",
        "not_joined_alert": "❌ Henüz kanala katılmamışsınız!",
        "thanks": "✅ Teşekkürler! Link gönderebilirsiniz.",
        "link_warning": "⚠️ Lütfen geçerli bir TikTok bağlantısı gönderin."
    },
    "EN": {
        "welcome": "Please select a language:",
        "lang_set": "✅ Language set to English! Send a TikTok link.",
        "analyzing": "🚀 **Starting Analysis...**",
        "updating": "🔄 **Updating Data...**", # New
        "bot_warning": "🚨 **SUSPICIOUS:** Likes > Views! (Possible Bot)",
        "loading_1": "Connecting to server...",
        "engagement": "Engagement Rate",
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
        "btn_refresh": "🔄 Refresh", # New
        "btn_profile": "🔗 Profile",
        "err_not_found": "❌ Video not found.",
        "err_general": "❌ Error:",
        "sub_warning_text": "⚠️ **You must join the channel to use the bot!**\n\nPlease join the channel using the button below and then press 'Check'.",
        "btn_join": "📢 Join Channel",
        "btn_check": "✅ Check",
        "not_joined_alert": "❌ You have not joined the channel yet!",
        "thanks": "✅ Thank you! You can send a link.",
        "link_warning": "⚠️ Please send a valid TikTok link."
    },
    "RU": {
        "welcome": "Пожалуйста, выберите язык:",
        "engagement": "Уровень вовлеченности",
        "lang_set": "✅ Язык установлен на Русский! Отправьте ссылку TikTok.",
        "analyzing": "🚀 **Начинается анализ...**",
        "updating": "🔄 **Обновление данных...**", # New
        "loading_1": "Подключение к серверу...",
        "loading_2": "Получение данных ID и региона...",
        "loading_3": "Технический анализ...",
        "loading_4": "Дашборд создан!",
        "bot_warning": "🚨 **ПОДОЗРИТЕЛЬНО:** Лайков > Просмотров! (Возможно бот)",
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
        "btn_refresh": "🔄 Обновить", # New
        "btn_profile": "🔗 Профиль",
        "err_not_found": "❌ Видео не найдено.",
        "err_general": "❌ Ошибка:",
        "sub_warning_text": "⚠️ **Вы должны присоединиться к каналу, чтобы использовать бота!**\n\nПожалуйста, присоединяйтесь к каналу, используя кнопку ниже, а затем нажмите «Проверить».",
        "btn_join": "📢 Присоединиться",
        "btn_check": "✅ Проверить",
        "not_joined_alert": "❌ Вы еще не присоединились к каналу!",
        "thanks": "✅ Спасибо! Можете отправить ссылку.",
        "link_warning": "⚠️ Пожалуйста, отправьте действительную ссылку на TikTok."
    }
}

def get_msg(chat_id, key):
    lang = user_prefs.get(chat_id, "TR")
    return LANGUAGES[lang].get(key, key)

# --- YARDIMCI FONKSİYONLAR ---

def check_subscription(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if member.status in ['creator', 'administrator', 'member']:
            return True
        return False
    except:
        return False

def send_subscription_warning(chat_id):
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
        import ffmpeg # ffmpeg'in import edildiğinden emin olmak için
        probe = ffmpeg.probe(video_url)
        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
        if video_stream is None: return None
        
        # --- NORMAL FPS'İ AL (Değer ne geliyorsa o) ---
        avg_frame_rate = video_stream.get('avg_frame_rate', '0/0')
        if '/' in avg_frame_rate:
            num, den = map(int, avg_frame_rate.split('/'))
            fps = float(num) / float(den) if den > 0 else 0
        else:
            fps = float(avg_frame_rate)
            
        fps_sonuc = f"{fps:.0f}" 
        
        # --- ITSCALE DEDEKTİFİ KONTROLÜ ---
        try:
            import subprocess
            cmd = [
                'ffprobe', '-v', 'error', '-select_streams', 'v:0', 
                '-show_packets', '-show_entries', 'packet=pts_time', 
                '-of', 'default=noprint_wrappers=1:nokey=1', 
                '-read_intervals', '%+#20', video_url
            ]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, text=True, timeout=5)
            pts_list = [float(x) for x in res.stdout.strip().split('\n') if x.strip()]
            
            if len(pts_list) >= 5:
                pts_list.sort() 
                deltas = [pts_list[i] - pts_list[i-1] for i in range(1, len(pts_list)) if (pts_list[i] - pts_list[i-1]) > 0.001]
                
                if deltas:
                    avg_delta = sum(deltas) / len(deltas)
                    real_fps = round(1.0 / avg_delta)
                    reported_fps = round(fps)
                    
                    # Eğer hile varsa (gerçek FPS, metadatadan %10 farklıysa)
                    if abs(real_fps - reported_fps) > (reported_fps * 0.1):
                        # Orijinal sayının yanına parantez içinde gerçek FPS'i ekle
                        fps_sonuc = f"{fps:.0f} ({real_fps}fps)"
        except Exception:
            pass # Eğer hata verirse botu çökertme, orijinal FPS ile devam et
            
        # --- DİĞER VERİLER ---
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
            "fps": fps_sonuc, 
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

# --- ORTAK MESAJ OLUŞTURUCU (Hem ilk analiz hem de yenileme için) ---
def prepare_message_content(data, browser_meta, mobile_meta, cid):
    views = data.get("play_count", 0)
    likes = data.get("digg_count", 0)
    comments = data.get("comment_count", 0) 
    shares = data.get("share_count", 0)
    
    if views > 0:
        eng_rate = ((likes + comments + shares) / views) * 100
    else:
        eng_rate = 0
        
    view_bar = create_stat_bar(views, 100000)
    like_bar = create_stat_bar(likes, 50000)
    
    bot_alert = ""
    if likes > views:
        bot_alert = f"\n\n{get_msg(cid, 'bot_warning')}"
        
    def safe(meta, key): return meta.get(key, "?") if meta else "?"
    def size(meta): return format_size(meta.get("size_bytes", 0)) if meta else "?"

    video_id = data.get("id")
    creation_date = get_date_from_id(video_id)
    region = data.get("region", "Global").upper()
    title = data.get("title", "")
    if not title: title = get_msg(cid, "no_desc")
    
    mobile_url = data.get("hdplay")

    caption = (
        f"{get_msg(cid, 'desc_header')}\n_“{title}”_\n\n"
        f"{get_msg(cid, 'id_region_header')}\n├ 🔢 ID: `{video_id}`\n├ 🌍 {get_msg(cid, 'region')}: `{region}`\n└ 📅 {get_msg(cid, 'date')}: `{creation_date}`\n\n"
        f"{get_msg(cid, 'stats_header')}\n`👁 {format_number(views):<6}` {view_bar}\n`♥ {format_number(likes):<6}` {like_bar}\n\n"
        f"📈 {get_msg(cid, 'engagement')}: `%{eng_rate:.2f}`"
        f"{bot_alert}\n\n"
        f"{get_msg(cid, 'web_ver')}\n┌ 💎 {get_msg(cid, 'quality')} : `{safe(browser_meta, 'quality')}`\n├ 📐 {get_msg(cid, 'res')} : `{safe(browser_meta, 'res')}`\n├ 🚀 {get_msg(cid, 'Fps')}     : `{safe(browser_meta, 'fps')} FPS`\n└ 💾 {get_msg(cid, 'file')}   : `{size(browser_meta)}`\n\n"
        f"{get_msg(cid, 'mobile_ver')}\n┌ 💎 {get_msg(cid, 'quality')} : `{safe(mobile_meta, 'quality')}`\n├ 📐 {get_msg(cid, 'res')} : `{safe(mobile_meta, 'res')}`\n├ 🚀 {get_msg(cid, 'Fps')}     : `{safe(mobile_meta, 'fps')} FPS`\n└ 💾 {get_msg(cid, 'file')}   : `{size(mobile_meta)}`\n\n"
        f"{get_msg(cid, 'publisher')} `@{data.get('author', {}).get('unique_id')}`"
    )
    
    markup = InlineKeyboardMarkup()
    # İndirme Butonu
    markup.add(InlineKeyboardButton(f"{get_msg(cid, 'btn_download')} (HD - {size(mobile_meta)})", url=mobile_url))
    
    # Müzik Butonu Kaldırıldı -> Yerine Yenileme Butonu Eklendi
    refresh_callback = f"refresh_{video_id}"
    profile_url = f"https://www.tiktok.com/@{data.get('author', {}).get('unique_id')}"
    
    markup.row(
        InlineKeyboardButton(get_msg(cid, 'btn_refresh'), callback_data=refresh_callback), 
        InlineKeyboardButton(get_msg(cid, 'btn_profile'), url=profile_url)
    )
    
    return caption, markup

# --- BOT HANDLER ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🇹🇷 Türkçe", callback_data="lang_TR"))
    markup.add(InlineKeyboardButton("🇬🇧 English", callback_data="lang_EN"))
    markup.add(InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_RU"))
    
    welcome_text = (
        "🇹🇷 Lütfen bir dil seçin:\n"
        "🇬🇧 Please select a language:\n"
        "🇷🇺 Пожалуйста, выберите язык:"
    )
    bot.reply_to(message, welcome_text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("lang_"))
def callback_language(call):
    lang_code = call.data.split("_")[1]
    user_prefs[call.message.chat.id] = lang_code
    
    if check_subscription(call.from_user.id):
        bot.answer_callback_query(call.id, "✅")
        bot.edit_message_text(LANGUAGES[lang_code]["lang_set"], call.message.chat.id, call.message.message_id)
    else:
        bot.answer_callback_query(call.id, "⚠️")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        send_subscription_warning(call.message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def callback_check_sub(call):
    chat_id = call.message.chat.id
    if check_subscription(call.from_user.id):
        bot.delete_message(chat_id, call.message.message_id)
        bot.answer_callback_query(call.id, "✅", show_alert=False)
        bot.send_message(chat_id, get_msg(chat_id, "thanks"))
    else:
        alert_text = get_msg(chat_id, "not_joined_alert")
        bot.answer_callback_query(call.id, alert_text, show_alert=True)

# --- YENİ EKLENEN: REFRESH HANDLER ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("refresh_"))
def callback_refresh_video(call):
    cid = call.message.chat.id
    video_id = call.data.split("_")[1]
    
    # Kullanıcıya işlem yapıldığını göster
    try:
        bot.answer_callback_query(call.id, get_msg(cid, "updating"))
    except: pass
    
    # ID üzerinden link oluştur (TikTok standart formatı)
    url = f"https://m.tiktok.com/v/{video_id}"
    
    try:
        # Aynı analiz işlemini tekrar yap
        response = requests.post(TIKWM_API_URL, data={"url": url, "hd": 1}, headers={"User-Agent": "Mozilla/5.0"}).json()
        
        if response.get("code") == 0:
            data = response.get("data", {})
            browser_url = data.get("play")  
            mobile_url = data.get("hdplay")
            
            browser_meta = get_video_metadata(browser_url)
            mobile_meta = get_video_metadata(mobile_url) if (mobile_url and mobile_url != browser_url) else browser_meta
            
            # Yeni içerik oluştur
            caption, markup = prepare_message_content(data, browser_meta, mobile_meta, cid)
            
            # Mesajı güncelle
            bot.edit_message_caption(chat_id=cid, message_id=call.message.message_id, caption=caption, reply_markup=markup, parse_mode='Markdown')
        else:
            bot.answer_callback_query(call.id, get_msg(cid, "err_not_found"), show_alert=True)
            
    except Exception as e:
        bot.answer_callback_query(call.id, f"{get_msg(cid, 'err_general')} {str(e)[:20]}", show_alert=True)


@bot.message_handler(func=lambda message: True)
def analyze_video(message):
    cid = message.chat.id
    
    if cid not in user_prefs:
        user_prefs[cid] = "TR"

    url = message.text.strip()
    
    if "tiktok.com" not in url:
        return 

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

            # Ortak fonksiyonu kullanıyoruz
            caption, markup = prepare_message_content(data, browser_meta, mobile_meta, cid)

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

