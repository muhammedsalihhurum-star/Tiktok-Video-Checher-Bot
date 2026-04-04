from flask import Flask, request, jsonify
import requests
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import datetime
import ffmpeg
import time
from threading import Thread
import os

# ---------------- FLASK ----------------
app = Flask('')

# ---------------- RAW FPS FONKSİYONLARI ----------------

def get_raw_video_url(tiktok_url):
    try:
        submit = requests.post(
            "[tikwm.com](https://www.tikwm.com/api/video/task/submit)",
            headers={
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "X-Requested-With": "XMLHttpRequest",
                "Referer": "[tikwm.com](https://www.tikwm.com/originalDownloader.html)",
                "Origin": "[tikwm.com](https://www.tikwm.com)"
            },
            data=f"url={tiktok_url}&web=1"
        ).json()

        if submit.get("code") != 0:
            return None

        task_id = submit["data"]["task_id"]
        time.sleep(2)

        result = requests.get(
            f"[tikwm.com](https://www.tikwm.com/api/video/task/result?task_id={task_id})"
        ).json()

        if result.get("code") != 0:
            return None

        d = result["data"].get("detail", result["data"])
        return (
            d.get("play_url")
            or d.get("download_url")
            or d.get("play")
        )

    except:
        return None


def get_raw_fps(video_url):
    try:
        probe = ffmpeg.probe(video_url)
        video_stream = next(
            (s for s in probe["streams"] if s["codec_type"] == "video"),
            None
        )
        if not video_stream:
            return None, None

        avg = video_stream.get("avg_frame_rate", "0/0")
        num, den = map(int, avg.split("/"))
        reported = num / den if den else 0

        raw = video_stream.get("r_frame_rate", "0/0")
        rnum, rden = map(int, raw.split("/"))
        real = rnum / rden if rden else 0

        return reported, real
    except:
        return None, None


def detect_itsscale(reported, real):
    if not reported or not real:
        return False, reported

    if abs(real - reported * 2) < 1:
        return True, real * 2  # 30 FPS → (120 FPS)
    return False, real

# ---------------- MOBIL API ----------------

@app.route('/api/analyze')
def api_analyze():
    url = request.args.get('url')
    if not url:
        return jsonify({"success": False, "message": "URL yok"})

    try:
        response = requests.post("[tikwm.com](https://tikwm.com/api/)", data={"url": url, "hd": 1},
                                 headers={"User-Agent": "Mozilla/5.0"}).json()

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

            return jsonify({
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
            })
        else:
            return jsonify({"success": False, "message": "TikWM veriyi bulamadı"})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

# ---------------- TELEGRAM BOT ----------------

BOT_TOKEN = "8584063240:AAFNRb73LL-9emyfvVrhkZdjoADOOws0uy4"
bot = telebot.TeleBot(BOT_TOKEN)

TIKWM_API_URL = "[tikwm.com](https://tikwm.com/api/)"
CHANNEL_USERNAME = "@kuronai60"

user_prefs = {}

LANGUAGES = {
    "TR": {
        "welcome": "Lütfen bir dil seçin / Please select a language:",
        "engagement": "Etkileşim Oranı",
        "bot_warning": "🚨 **ŞÜPHELİ ETKİLEŞİM:** Like sayısı izlenmeden fazla! (Olası Bot)",
        "lang_set": "✅ Dil Türkçe olarak ayarlandı! TikTok linki gönder.",
        "analyzing": "🚀 **Analiz Başlatılıyor...**",
        "updating": "🔄 **Veriler Güncelleniyor...**",
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
        "mobile_ver": "📱 **Mobil Sürüm**",
        "quality": "Kalite",
        "res": "Çözün.",
        "file": "Dosya",
        "publisher": "👤 **Yayıncı:**",
        "btn_download": "📥 İndir",
        "btn_refresh": "🔄 Güncelle",
        "btn_profile": "🔗 Profil",
        "Fps": "FPS",
        "err_not_found": "❌ Video bulunamadı.",
        "err_general": "❌ Hata:",
        "thanks": "✅ Teşekkürler! Link gönderebilirsiniz."
    }
}

def get_msg(cid, key):
    lang = user_prefs.get(cid, "TR")
    return LANGUAGES[lang].get(key, key)

def check_subscription(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["creator", "administrator", "member"]
    except:
        return False

def create_stat_bar(value, max_value=1000000, length=8):
    p = min(1.0, value / max_value)
    filled = int(length * p)
    if filled == 0 and value > 0:
        filled = 1
    return "▓" * filled + "░" * (length - filled)

def get_video_metadata(video_url):
    if not video_url:
        return None
    try:
        probe = ffmpeg.probe(video_url)
        fmt = probe.get("format", {})

        vs = next((s for s in probe["streams"] if s["codec_type"] == "video"), None)
        if not vs:
            return None

        avg = vs.get("avg_frame_rate", "0/0")
        num, den = map(int, avg.split("/"))
        fps = num / den if den else 0

        bitrate = int(vs.get('bit_rate', 0) or fmt.get('bit_rate', 0))
        bstr = f"{bitrate/1_000_000:.1f} Mbps" if bitrate >= 1_000_000 else f"{bitrate/1000:.0f} kbps"

        w = vs.get("width")
        h = vs.get("height")

        return {
            "res": f"{w}x{h}",
            "quality": "HD (720p)" if min(w, h) >= 720 else "SD (480p)",
            "fps": f"{fps:.0f}",
            "bitrate": bstr,
            "size_bytes": int(fmt.get("size", 0))
        }

    except:
        return None
def format_number(n):
    if not n:
        return "0"
    if n > 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n > 1000:
        return f"{n/1000:.1f}K"
    return str(n)

def format_size(b):
    if not b:
        return "0 MB"
    return f"{b / (1024*1024):.2f} MB"

def get_date_from_id(vid):
    try:
        ts = int(vid) >> 32
        return datetime.datetime.fromtimestamp(ts).strftime("%d.%m.%Y %H:%M")
    except:
        return "-"

# ---------------- MESAJ OLUŞTURUCU ----------------

def prepare_message_content(data, browser_meta, mobile_meta, cid):

    views = data.get("play_count", 0)
    likes = data.get("digg_count", 0)
    comments = data.get("comment_count", 0)
    shares = data.get("share_count", 0)

    eng_rate = ((likes + comments + shares) / views) * 100 if views else 0

    def safe(m, k): return m.get(k, "?") if m else "?"
    def size(m): return format_size(m.get("size_bytes", 0)) if m else "?"

    vid = data.get("id")
    date = get_date_from_id(vid)
    region = data.get("region", "Global").upper()
    title = data.get("title", "") or get_msg(cid, "no_desc")

    # ---------------- RAW FPS ANALİZİ ----------------

    raw_url = get_raw_video_url(data.get("play"))

    if raw_url:
        reported, real = get_raw_fps(raw_url)
        scaled, final_fps = detect_itsscale(reported, real)
        if scaled:
            fps_text = f"{int(reported)} FPS ({int(final_fps)} FPS)"
        else:
            fps_text = f"{int(reported)} FPS"
    else:
        fps_text = f"{safe(browser_meta, 'fps')} FPS"

    # -------------------------------------------------

    caption = (
        f"{get_msg(cid, 'desc_header')}\n_“{title}”_\n\n"
        f"{get_msg(cid, 'id_region_header')}\n"
        f"├ 🔢 ID: `{vid}`\n"
        f"├ 🌍 {get_msg(cid, 'region')}: `{region}`\n"
        f"└ 📅 {get_msg(cid, 'date')}: `{date}`\n\n"

        f"{get_msg(cid, 'stats_header')}\n"
        f"`👁 {format_number(views):<6}` {create_stat_bar(views)}\n"
        f"`♥ {format_number(likes):<6}` {create_stat_bar(likes,50000)}\n\n"

        f"📈 {get_msg(cid, 'engagement')}: `%{eng_rate:.2f}`\n\n"

        f"{get_msg(cid, 'web_ver')}\n"
        f"┌ 💎 {get_msg(cid, 'quality')}: `{safe(browser_meta, 'quality')}`\n"
        f"├ 📐 {get_msg(cid, 'res')}: `{safe(browser_meta, 'res')}`\n"
        f"├ 🚀 FPS: `{fps_text}`\n"
        f"└ 💾 {get_msg(cid, 'file')}: `{size(browser_meta)}`\n\n"

        f"{get_msg(cid, 'mobile_ver')}\n"
        f"┌ 💎 {get_msg(cid, 'quality')}: `{safe(mobile_meta, 'quality')}`\n"
        f"├ 📐 {get_msg(cid, 'res')}: `{safe(mobile_meta, 'res')}`\n"
        f"├ 🚀 FPS: `{fps_text}`\n"
        f"└ 💾 {get_msg(cid, 'file')}: `{size(mobile_meta)}`\n\n"

        f"{get_msg(cid, 'publisher')} `@{data.get('author',{}).get('unique_id')}`"
    )

    markup = InlineKeyboardMarkup()
    mobile_url = data.get("hdplay")

    markup.add(InlineKeyboardButton(
        f"{get_msg(cid, 'btn_download')} (HD - {size(mobile_meta)})", url=mobile_url))

    refresh_id = f"refresh_{vid}"
    profile_url = f"[tiktok.com](https://www.tiktok.com/@{data.get()'author', {}).get('unique_id')}"


    markup.row(
        InlineKeyboardButton(get_msg(cid, "btn_refresh"), callback_data=refresh_id),
        InlineKeyboardButton(get_msg(cid, "btn_profile"), url=profile_url)
    )

    return caption, markup


# ---------------- TELEGRAM KOMUTLARI ----------------

@bot.message_handler(commands=['start'])
def send_welcome(message):
    m = InlineKeyboardMarkup()
    m.add(InlineKeyboardButton("🇹🇷 Türkçe", callback_data="lang_TR"))
    m.add(InlineKeyboardButton("🇬🇧 English", callback_data="lang_EN"))
    m.add(InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_RU"))

    bot.reply_to(message,
        "🇹🇷 Lütfen bir dil seçin:\n"
        "🇬🇧 Please select a language:\n"
        "🇷🇺 Пожалуйста, выберите язык:",
        reply_markup=m)


@bot.callback_query_handler(func=lambda c: c.data.startswith("lang_"))
def cb_lang(call):
    lang = call.data.split("_")[1]
    user_prefs[call.message.chat.id] = lang
    bot.edit_message_text(LANGUAGES[lang]["lang_set"],
                          call.message.chat.id,
                          call.message.message_id)


@bot.callback_query_handler(func=lambda c: c.data.startswith("refresh_"))
def cb_refresh(call):

    cid = call.message.chat.id
    vid = call.data.split("_")[1]

    url = f"[tiktok.com](https://www.tiktok.com/@dummy/video/{vid})"

    try:
        r = requests.post(TIKWM_API_URL, data={"url": url, "hd": 1},
                          headers={"User-Agent": "Mozilla/5.0"}).json()

        if r.get("code") == 0:
            d = r["data"]
            b = get_video_metadata(d.get("play"))
            m = get_video_metadata(d.get("hdplay")) or b

            caption, markup = prepare_message_content(d, b, m, cid)

            bot.edit_message_caption(
                caption=caption,
                chat_id=cid,
                message_id=call.message.message_id,
                reply_markup=markup,
                parse_mode="Markdown"
            )
    except:
        pass


@bot.message_handler(func=lambda m: True)
def analyze(message):

    cid = message.chat.id
    url = message.text.strip()

    if "tiktok.com" not in url:
        return

    msg = bot.reply_to(message, get_msg(cid, "analyzing"), parse_mode="Markdown")

    try:
        r = requests.post(
            TIKWM_API_URL, data={"url": url, "hd": 1},
            headers={"User-Agent": "Mozilla/5.0"}
        ).json()

        if r.get("code") == 0:
            d = r["data"]
            b = get_video_metadata(d.get("play"))
            m = get_video_metadata(d.get("hdplay")) or b

            caption, markup = prepare_message_content(d, b, m, cid)

            bot.delete_message(cid, msg.message_id)
            bot.send_photo(cid, d.get("cover"), caption=caption,
                           parse_mode="Markdown", reply_markup=markup)

    except Exception as e:
        bot.edit_message_text("Hata: " + str(e), cid, msg.message_id)

# ---------------- FLASK KEEP ALIVE ----------------

@app.route("/")
def home():
    return "Bot çalışıyor!"

def run():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

print("Bot aktif...")
keep_alive()
bot.infinity_polling()
