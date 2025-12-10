import os
import requests
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv

# ------------------------------------------------------------
# .env yükle
# ------------------------------------------------------------
load_dotenv()

DETECTLANG_API_KEY = os.getenv("DETECTLANG_API_KEY")

if not DETECTLANG_API_KEY:
    raise RuntimeError("DETECTLANG_API_KEY .env dosyasında bulunamadı!")

app = Flask(__name__)

# ------------------------------------------------------------
# Dil kodu -> isim map
# ------------------------------------------------------------
LANG_NAME_MAP = {
    "af": "Afrikaans",
    "ar": "Arabic",
    "az": "Azerbaijani",
    "bg": "Bulgarian",
    "bn": "Bengali",
    "ca": "Catalan",
    "cs": "Czech",
    "cy": "Welsh",
    "da": "Danish",
    "de": "German",
    "el": "Greek",
    "en": "English",
    "es": "Spanish",
    "et": "Estonian",
    "fa": "Persian",
    "fi": "Finnish",
    "fr": "French",
    "ga": "Irish",
    "gl": "Galician",
    "gu": "Gujarati",
    "he": "Hebrew",
    "hi": "Hindi",
    "hr": "Croatian",
    "hu": "Hungarian",
    "id": "Indonesian",
    "is": "Icelandic",
    "it": "Italian",
    "ja": "Japanese",
    "ka": "Georgian",
    "kk": "Kazakh",
    "km": "Khmer",
    "kn": "Kannada",
    "ko": "Korean",
    "lo": "Lao",
    "lt": "Lithuanian",
    "lv": "Latvian",
    "mk": "Macedonian",
    "ml": "Malayalam",
    "mn": "Mongolian",
    "mr": "Marathi",
    "ms": "Malay",
    "my": "Myanmar (Burmese)",
    "ne": "Nepali",
    "nl": "Dutch",
    "no": "Norwegian",
    "pa": "Punjabi",
    "pl": "Polish",
    "pt": "Portuguese",
    "ro": "Romanian",
    "ru": "Russian",
    "si": "Sinhala",
    "sk": "Slovak",
    "sl": "Slovenian",
    "sq": "Albanian",
    "sr": "Serbian",
    "sv": "Swedish",
    "sw": "Swahili",
    "ta": "Tamil",
    "te": "Telugu",
    "th": "Thai",
    "tl": "Tagalog",
    "tr": "Turkish",
    "uk": "Ukrainian",
    "ur": "Urdu",
    "uz": "Uzbek",
    "vi": "Vietnamese",
    "zh": "Chinese",
}

# ------------------------------------------------------------
# DİL ALGILAMA - DetectLanguage
# ------------------------------------------------------------
def detect_language(text: str):
    url = "https://ws.detectlanguage.com/0.2/detect"
    headers = {
        "Authorization": f"Bearer {DETECTLANG_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(url, headers=headers, json={"q": text}, timeout=10)

        print("▶ DetectLanguage:", resp.status_code, resp.text)

        if resp.status_code != 200:
            return None

        data = resp.json()
        detections = data.get("data", {}).get("detections")

        if not detections:
            return None

        first = detections[0]
        if isinstance(first, list):
            best = first[0]
        else:
            best = first

        return {
            "code": best["language"],
            "is_reliable": best.get("isReliable", True),
            "confidence": best.get("confidence", 0.0),  # sadece iç kullanım, response'a koymuyoruz
        }

    except Exception as e:
        print("❌ DetectLanguage Error:", repr(e))
        return None


# ------------------------------------------------------------
# ÇEVİRİ - MyMemory (Ücretsiz)
# ------------------------------------------------------------
def translate_text(text: str, source_lang: str, target_lang: str):
    """
    MyMemory: https://mymemory.translated.net/doc/spec.php
    API key'siz basic kullanım (rate limitli ama ücretsiz)
    """
    try:
        url = "https://api.mymemory.translated.net/get"
        params = {
            "q": text,
            "langpair": f"{source_lang}|{target_lang}",
        }

        resp = requests.get(url, params=params, timeout=15)

        print("▶ MyMemory:", resp.status_code, resp.text[:200])

        if resp.status_code != 200:
            return None

        data = resp.json()
        translated = data.get("responseData", {}).get("translatedText")
        if not translated:
            return None

        return translated

    except Exception as e:
        print("❌ MyMemory Error:", repr(e))
        return None


# ------------------------------------------------------------
# ROUTES
# ------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/analyze", methods=["POST"])
def analyze():
    body = request.get_json()

    if not body or "text" not in body:
        return jsonify({"error": "Text field is required"}), 400

    text = body["text"].strip()
    target_lang = body.get("target", "en").lower()

    # Sadece güvenilir temel diller (isteğe göre genişletebilirsin)
    ALLOWED_TARGETS = ["tr", "en", "es", "fr", "de", "it"]
    if target_lang not in ALLOWED_TARGETS:
        target_lang = "en"

    if not text:
        return jsonify({"error": "Text is empty"}), 400

    # 1) Dil algılama
    lang_info = detect_language(text)
    if not lang_info:
        return jsonify({"error": "Language detection failed"}), 500

    source_lang = lang_info["code"]
    language_name = LANG_NAME_MAP.get(source_lang, source_lang.upper())

    # DİKKAT:
    # Daha önce burada:
    # if target_lang == source_lang:
    #     target_lang = "tr" if source_lang != "tr" else "en"
    # vardı.
    # BUNU KALDIRDIK → artık kullanıcı aynı dili isterse,
    # source == target kalacak ve MyMemory o dilde çeviri/parafraz
    # yapmaya çalışacak (veya neredeyse aynı metni dönecek).

    # 2) ÇEVİRİ
    translated = translate_text(text, source_lang, target_lang)
    if translated is None:
        return jsonify({"error": "Translation failed"}), 500

    return jsonify(
        {
            "original_text": text,
            "source_language_code": source_lang,
            "source_language_name": language_name,
            "target_language_code": target_lang,
            "translated_text": translated,
        }
    )


# ------------------------------------------------------------
# SERVER START
# ------------------------------------------------------------
if __name__ == "__main__":
    print("🚀 Server başladı: http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
