import os
import requests
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from dotenv import load_dotenv
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash


load_dotenv()

DETECTLANG_API_KEY = os.getenv("DETECTLANG_API_KEY")

if not DETECTLANG_API_KEY:
    print("UYARI: DETECTLANG_API_KEY bulunamadı! Çeviri özellikleri çalışmayabilir.")

app = Flask(__name__)

# ------------------------------------------------------------
# Ayarlar (Config)
# ------------------------------------------------------------
app.config['SECRET_KEY'] = 'cok-gizli-anahtar-123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
@login_manager.unauthorized_handler
def unauthorized():
    
    if request.path == '/':
        return redirect(url_for('login'))
    
    
    flash("Bu sayfaya erişmek için lütfen giriş yapın.", "error")
    return redirect(url_for('login'))
# ------------------------------------------------------------
# DATABASE MODELİ (User Tablosu)
# ------------------------------------------------------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), default='user')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ------------------------------------------------------------
# DİL LİSTESİ VE FONKSİYONLAR
# ------------------------------------------------------------
LANG_NAME_MAP = {
    "af": "Afrikaans", "ar": "Arabic", "az": "Azerbaijani", "bg": "Bulgarian", "bn": "Bengali",
    "ca": "Catalan", "cs": "Czech", "cy": "Welsh", "da": "Danish", "de": "German", "el": "Greek",
    "en": "English", "es": "Spanish", "et": "Estonian", "fa": "Persian", "fi": "Finnish",
    "fr": "French", "ga": "Irish", "gl": "Galician", "gu": "Gujarati", "he": "Hebrew", "hi": "Hindi",
    "hr": "Croatian", "hu": "Hungarian", "id": "Indonesian", "is": "Icelandic", "it": "Italian",
    "ja": "Japanese", "ka": "Georgian", "kk": "Kazakh", "km": "Khmer", "kn": "Kannada", "ko": "Korean",
    "lo": "Lao", "lt": "Lithuanian", "lv": "Latvian", "mk": "Macedonian", "ml": "Malayalam",
    "mn": "Mongolian", "mr": "Marathi", "ms": "Malay", "my": "Myanmar (Burmese)", "ne": "Nepali",
    "nl": "Dutch", "no": "Norwegian", "pa": "Punjabi", "pl": "Polish", "pt": "Portuguese",
    "ro": "Romanian", "ru": "Russian", "si": "Sinhala", "sk": "Slovak", "sl": "Slovenian",
    "sq": "Albanian", "sr": "Serbian", "sv": "Swedish", "sw": "Swahili", "ta": "Tamil",
    "te": "Telugu", "th": "Thai", "tl": "Tagalog", "tr": "Turkish", "uk": "Ukrainian",
    "ur": "Urdu", "uz": "Uzbek", "vi": "Vietnamese", "zh": "Chinese",
}

def detect_language(text: str):
    url = "https://ws.detectlanguage.com/0.2/detect"
    headers = {"Authorization": f"Bearer {DETECTLANG_API_KEY}", "Content-Type": "application/json"}
    try:
        resp = requests.post(url, headers=headers, json={"q": text}, timeout=10)
        if resp.status_code != 200: return None
        data = resp.json()
        detections = data.get("data", {}).get("detections")
        if not detections: return None
        first = detections[0]
        best = first[0] if isinstance(first, list) else first
        return {"code": best["language"], "is_reliable": best.get("isReliable", True), "confidence": best.get("confidence", 0.0)}
    except Exception as e:
        print("❌ DetectLanguage Error:", repr(e))
        return None

def translate_text(text: str, source_lang: str, target_lang: str):
    try:
        url = "https://api.mymemory.translated.net/get"
        params = {"q": text, "langpair": f"{source_lang}|{target_lang}"}
        resp = requests.get(url, params=params, timeout=15)
        if resp.status_code != 200: return None
        data = resp.json()
        translated = data.get("responseData", {}).get("translatedText")
        return translated
    except Exception as e:
        print("❌ MyMemory Error:", repr(e))
        return None

# ------------------------------------------------------------
# ROTALAR: GİRİŞ / ÇIKIŞ / KAYIT
# ------------------------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Kullanıcı adı veya şifre hatalı!', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if User.query.filter_by(username=username).first():
            flash('Bu kullanıcı adı zaten alınmış.', 'error')
            return redirect(url_for('register'))
        
        hashed_pw = generate_password_hash(password, method='scrypt')
        new_user = User(username=username, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        flash('Kayıt başarılı! Giriş yapabilirsiniz.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# ------------------------------------------------------------
# ⚙️ ADMIN PANELİ İŞLEMLERİ (CRUD)
# ------------------------------------------------------------

# 1. LİSTELEME (READ)
@app.route('/admin_users')
@login_required 
def admin_users():
    
    if current_user.role != "admin":
        flash("⛔ Bu sayfayı görüntüleme yetkiniz yok!", "error")
        return redirect(url_for('index')) 

    all_users = User.query.all()
    return render_template('users.html', users=all_users)

# 2. EKLEME (CREATE)
@app.route('/admin/add', methods=['GET', 'POST'])
@login_required
def admin_add_user():
    
    if current_user.role != "admin":
        flash("⛔ Bu sayfayı görüntüleme yetkiniz yok!", "error")
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')

        if User.query.filter_by(username=username).first():
            flash('Bu kullanıcı adı zaten kullanılıyor.', 'error')
        else:
            hashed_pw = generate_password_hash(password, method='scrypt')
            new_user = User(username=username, password=hashed_pw, role=role) 
            db.session.add(new_user)
            db.session.commit()
            flash('Kullanıcı başarıyla oluşturuldu! ✅', 'success')
            return redirect(url_for('admin_users'))
            
    return render_template('user_form.html', title="Yeni Kullanıcı Ekle", user=None)

# 3. GÜNCELLEME (UPDATE)
@app.route('/admin/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_edit_user(id):
    
    if current_user.role != "admin":
        flash("⛔ Bu sayfayı görüntüleme yetkiniz yok!", "error")
        return redirect(url_for('index'))
        
    user_to_edit = User.query.get_or_404(id)

    if request.method == 'POST':
        user_to_edit.username = request.form.get('username')
        new_password = request.form.get('password')
        user_to_edit.role = request.form.get('role') 

        if new_password:
            user_to_edit.password = generate_password_hash(new_password, method='scrypt')
            
        try:
            db.session.commit()
            flash('Kullanıcı güncellendi! 🔄', 'success')
            return redirect(url_for('admin_users'))
        except:
            flash('Hata oluştu.', 'error')

    return render_template('user_form.html', title="Kullanıcıyı Düzenle", user=user_to_edit)

# 4. SİLME (DELETE)
@app.route('/admin/delete/<int:id>')
@login_required
def admin_delete_user(id):
    
    if current_user.role != "admin":
        flash("⛔ Bu sayfayı görüntüleme yetkiniz yok!", "error")
        return redirect(url_for('index'))
    
    user_to_delete = User.query.get_or_404(id)
    
    if user_to_delete.username == 'admin':
        flash('Admin hesabını silemezsin! 🛡️', 'error')
    else:
        db.session.delete(user_to_delete)
        db.session.commit()
        flash('Kullanıcı silindi. 🗑️', 'success')
        
    return redirect(url_for('admin_users'))

# ------------------------------------------------------------
# ANA SAYFA VE API
# ------------------------------------------------------------
@app.route('/')
@login_required
def index():
    return render_template('index.html', name=current_user.username)

@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route("/api/analyze", methods=["POST"])
@login_required
def analyze():
    body = request.get_json()
    if not body or "text" not in body: return jsonify({"error": "Text field is required"}), 400
    text = body["text"].strip()
    target_lang = body.get("target", "en").lower()
    if target_lang not in ["tr", "en", "es", "fr", "de", "it"]: target_lang = "en"
    if not text: return jsonify({"error": "Text is empty"}), 400

    lang_info = detect_language(text)
    if not lang_info: return jsonify({"error": "Language detection failed"}), 500

    source_lang = lang_info["code"]
    language_name = LANG_NAME_MAP.get(source_lang, source_lang.upper())

    translated = translate_text(text, source_lang, target_lang)
    if translated is None: return jsonify({"error": "Translation failed"}), 500

    return jsonify({
        "original_text": text,
        "source_language_code": source_lang,
        "source_language_name": language_name,
        "target_language_code": target_lang,
        "translated_text": translated,
    })

# ------------------------------------------------------------
# SERVER BAŞLATMA
# ------------------------------------------------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    print("🚀 Server başladı: http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)