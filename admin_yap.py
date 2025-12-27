from app import app, db, User

with app.app_context():
   
    kullanici = User.query.filter_by(username='admin').first()
    
    if kullanici:
        
        kullanici.role = 'admin'
        db.session.commit()
        print("\n✅ BAŞARILI: 'admin' kullanıcısının yetkisi verildi!")
        print("Şimdi siteye gidip panele girmeyi deneyebilirsin.")
    else:
        print("\n❌ HATA: 'admin' adında bir kullanıcı bulunamadı.")
        print("Lütfen önce siteden 'admin' adıyla kayıt ol.")