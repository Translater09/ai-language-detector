import os
import requests
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv

# ------------------------------------------------------------
# .env dosyasını yükle
# ------------------------------------------------------------
load_dotenv()

DETECTLANG_API_KEY = os.getenv("DETECTLANG_API_KEY")

if not DETECTLANG_API_KEY:
    raise RuntimeError("DETECTLANG_API_KEY .env dosyasında bulunamadı!")

app = Flask(__name__)

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
    "zh": "Chinese"
 }

   


# ------------------------------------------------------------
# DİL ALGILAMA - DetectLanguage
# ------------------------------------------------------------
def detect_language(text: str):
    url = "https://ws.detectlanguage.com/0.2/detect"
    headers = {
        "Authorization": f"Bearer {DETECTLANG_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        resp = requests.post(url, headers=headers, json={"q": text}, timeout=10)

        print("▶ DetectLanguage Status:", resp.status_code)
        print("▶ DetectLanguage Response:", resp.text)

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
            "confidence": best.get("confidence", 0.0)
        }

    except Exception as e:
        print("❌ DetectLanguage Error:", repr(e))
        return None


# ------------------------------------------------------------
# ÇEVİRİ - LibreTranslate (Ücretsiz)
# ------------------------------------------------------------
def translate_text(text: str, source_lang: str, target_lang: str):
    try:
        url = "https://api.mymemory.translated.net/get"

        params = {
            "q": text,
            "langpair": f"{source_lang}|{target_lang}"
        }

        resp = requests.get(url, params=params, timeout=15)

        print("▶ MyMemory Status:", resp.status_code)
        print("▶ MyMemory Response:", resp.text)

        if resp.status_code != 200:
            return None

        data = resp.json()
        translated = data.get("responseData", {}).get("translatedText")

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
    # Sadece güvenilir temel diller
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

    raw_confidence = lang_info["confidence"]

    # DetectLanguage puanı (0–30) -> %0–100'e normalize
    normalized_confidence = round(min(100, (raw_confidence / 30) * 100), 2)

    is_reliable = lang_info["is_reliable"]

    # Aynı dile çeviri istemesin diye otomatik değiştir
    if target_lang == source_lang:
        target_lang = "tr" if source_lang != "tr" else "en"

    # 2) ÇEVİRİ
    translated = translate_text(text, source_lang, target_lang)

    return jsonify({
        "original_text": text,

        "source_language_code": source_lang,
        "source_language_name": language_name,

        "confidence_raw": raw_confidence,
        "confidence_percent": normalized_confidence,
        "is_reliable": is_reliable,

        "target_language_code": target_lang,
        "translated_text": translated
    })


# ------------------------------------------------------------
# SERVER START
# ------------------------------------------------------------
if __name__ == "__main__":
    print("🚀 Server başladı: http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
