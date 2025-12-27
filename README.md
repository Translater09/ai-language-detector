Berkay Çevirici 220204054 
Melih Polat 220204043 
Arhan Ataş-230205018

# AI Language Detector & Translator

This project is a web application that detects the language of a given text and translates it into a selected target language. Additionally, it now includes a comprehensive **Management Panel** equipped with user authentication and role-based security.

## 🚀 Features

### 🔹 Core Features
- **Automatic Language Detection:** Uses an AI-supported API to detect the source language.
- **Multi-Language Translation:** Translates text into selected languages (EN, TR, ES, FR, DE, IT).
- **Character Counter:** Dynamically tracks text input length.

### 🔐 User & Management System
- **User Authentication:** Secure Register and Login system.
- **Role-Based Access Control (RBAC):** Distinction between Standard Users and Administrators.
- **Admin Dashboard:**
  - List all registered users.
  - Add new users manually.
  - Edit user details and roles (Admin/User).
  - Delete users.
- **Security:**
  - Password hashing using **Scrypt/SHA** (Werkzeug Security).
  - Route protection via `@login_required`.
  - Smart redirection (Unauthorized access redirects to login or home page).
- **User Experience:**
  - Flash message notifications for errors and success events.
  - Exclusive badges and controls for Admin users.

## 🛠️ Technologies

- **Backend:** Python (Flask)
- **Database:** SQLite (Flask-SQLAlchemy ORM)
- **Authentication:** Flask-Login
- **Frontend:** HTML5, CSS3, Vanilla JavaScript
- **API Integrations:**
  - Language Detection API
  - Translation API
- **Security:** Werkzeug Security (Password Hashing)

