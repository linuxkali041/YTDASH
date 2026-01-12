# 📥 YouTube Video Downloader

A powerful, production-ready web application for downloading YouTube videos with **multi-user authentication**, **admin control panel**, and **encrypted credential storage**.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-green.svg)

---

## 🚀 Quick Start (Easiest Way)

### One-Command Installation & Run

**Windows:**
```bash
python install_and_run_windows.py
```

**Linux/macOS:**
```bash
python install_and_run_linux.py
```

That's it! The script will:
- ✅ Create virtual environment
- ✅ Install all dependencies
- ✅ Generate configuration
- ✅ Initialize database
- ✅ Create admin user (save the credentials!)
- ✅ Start the application

**Access your app at:**
- 🏠 Main App: http://localhost:8000
- 🔐 Login: http://localhost:8000/login
- ⚙️ Admin Panel: http://localhost:8000/admin
- 📚 API Docs: http://localhost:8000/docs

---

## ✨ Features

### 🎯 Core Features
- **Download YouTube Videos** - Multiple formats and quality options
- **Audio Extraction** - Download audio-only (MP3)
- **Real-time Progress** - Live download progress tracking
- **Format Selection** - Choose video quality and format
- **Batch Downloads** - Queue multiple downloads

### 👥 Multi-User System
- **User Registration & Login** - Secure JWT authentication
- **Personal Accounts** - Each user has their own space
- **YouTube Credentials** - Add your own YouTube accounts (encrypted)
- **Download History** - Track all your downloads
- **Storage Quotas** - Per-user storage limits
- **Usage Statistics** - Monitor your downloads and storage

### �️ Admin Control Panel
- **User Management** - Create, edit, delete, suspend users
- **Live Dashboard** - System statistics and recent activity
- **Settings Management** - Update any setting via UI (no code changes!)
- **Download Monitoring** - View all downloads across users
- **Audit Logs** - Complete action history with IP tracking
- **Role Management** - Admin/User/Guest roles

### � Security & Privacy
- **Bcrypt Password Hashing** - Industry-standard security
- **JWT Authentication** - Stateless token-based auth
- **Encrypted Credentials** - YouTube cookies encrypted at rest
- **Role-Based Access** - Admin-only endpoints protected
- **Audit Trail** - All actions logged
- **Input Validation** - SQL injection & XSS protection

### 🎨 User Interface
- **Modern Design** - Clean, professional interface
- **Three Themes** - Light, Dark, AMOLED Black
- **Responsive** - Works on desktop, tablet, mobile
- **Real-time Updates** - Live stats and notifications
- **Intuitive Navigation** - Easy to use

---

## 📋 Requirements

- **Python 3.9+** (Required)
- **FFmpeg** (Optional - for merging video/audio streams)
- **Internet Connection** (Required)

---

## � Manual Installation

If you prefer manual setup:

### 1. Clone Repository
```bash
git clone <your-repo-url>
cd Youtube
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# Activate
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Generate Configuration
```bash
python setup.py
```

### 5. Initialize Database
```bash
python init_db.py
```
**⚠️ IMPORTANT:** Save the admin credentials displayed!

### 6. Start Application
```bash
python main.py
```

---

## 🌐 Production Deployment

### Database (Recommended)

Switch from SQLite to PostgreSQL for production:

1. **Install PostgreSQL**

2. **Update `.env`:**
```env
DATABASE_URL=postgresql://user:password@localhost/ytdl
```

3. **Run initialization:**
```bash
python init_db.py
```

### Security

**Generate secure keys:**
```bash
# JWT Secret
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Cookie Encryption Key  
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

**Update `.env`:**
```env
SECRET_KEY=<generated-jwt-secret>
COOKIE_ENCRYPTION_KEY=<generated-encryption-key>
DEBUG=False
```

### Deploy with Gunicorn

```bash
pip install gunicorn

gunicorn main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

### Deploy with Docker (Optional)

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t youtube-downloader .
docker run -p 8000:8000 youtube-downloader
```

---

## 📖 User Guide

### For Regular Users

1. **Register Account**
   - Go to http://localhost:8000/register
   - Create your account
   - Automatic login after registration

2. **Add YouTube Credentials (Optional)**
   - Login to your account
   - Use API to add YouTube cookies
   - Enables downloading age-restricted/private videos

3. **Download Videos**
   - Enter YouTube URL
   - Select format and quality
   - Click download
   - Track progress in real-time

### For Administrators

1. **Login**
   - Use credentials from `init_db.py`
   - Redirects to admin panel

2. **Manage Users**
   - Create new users
   - Edit user quotas
   - Suspend/activate accounts
   - Delete users

3. **Configure Settings**
   - Update any setting via UI
   - Changes apply immediately
   - No restart required

4. **Monitor System**
   - View system statistics
   - Check all downloads
   - Review audit logs

---

## ⚙️ Configuration

All settings in `.env` file:

```env
# Application
DEBUG=False
HOST=0.0.0.0
PORT=8000

# Security
SECRET_KEY=<your-secret-key>
COOKIE_ENCRYPTION_KEY=<your-encryption-key>

# Database
DATABASE_URL=sqlite:///./youtube_downloader.db

# Downloads
MAX_CONCURRENT_DOWNLOADS_PER_USER=3
MAX_DOWNLOAD_SIZE_MB=2048
DOWNLOAD_TIMEOUT_SECONDS=3600

# OAuth (Optional)
GOOGLE_CLIENT_ID=<your-client-id>
GOOGLE_CLIENT_SECRET=<your-client-secret>
```

**Or use the Admin Panel to change settings dynamically!**

---

## 🏗️ Architecture

```
├── Backend (FastAPI)
│   ├── Database (SQLAlchemy + SQLite/PostgreSQL)
│   ├── Authentication (JWT + Bcrypt)
│   ├── API Routes (23 endpoints)
│   └── Download Engine (yt-dlp)
│
├── Frontend
│   ├── Vanilla HTML/CSS/JavaScript
│   ├── Three theme modes
│   └── Real-time updates
│
└── Admin Panel
    ├── User Management
    ├── Settings Control
    └── System Monitoring
```

---

## � API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login
- `POST /api/auth/logout` - Logout
- `POST /api/auth/refresh` - Refresh token
- `GET /api/auth/me` - Current user info

### User Management
- `POST /api/user/credentials` - Add YouTube account
- `GET /api/user/credentials` - List credentials
- `DELETE /api/user/credentials/{id}` - Remove credential
- `GET /api/user/downloads` - Download history
- `GET /api/user/stats` - User statistics

### Admin (Admin Only)
- `GET /admin/users` - List all users
- `POST /admin/users` - Create user
- `PUT /admin/users/{id}` - Update user
- `DELETE /admin/users/{id}` - Delete user
- `GET /admin/settings` - Get settings
- `PUT /admin/settings/{key}` - Update setting
- `GET /admin/stats` - System statistics
- `GET /admin/logs` - Audit logs

### Video Downloads
- `POST /api/video/info` - Get video information
- `POST /api/video/download` - Start download
- `GET /api/download/progress/{id}` - Download progress
- `DELETE /api/download/{id}` - Cancel download

**Full API documentation:** http://localhost:8000/docs

---

## 🛠️ Troubleshooting

### Database Issues
```bash
# Reset database
rm youtube_downloader.db
python init_db.py
```

### Port Already in Use
```env
# Change port in .env
PORT=8080
```

### FFmpeg Not Found
**Windows:**
- Download from https://ffmpeg.org/download.html
- Add to PATH

**Linux:**
```bash
sudo apt install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

---

## 📝 Default Admin Credentials

Generated during `init_db.py` - displayed in console.

**If lost:**
```bash
# Reset database
rm youtube_downloader.db
python init_db.py
```

---

## 🔄 Updates

```bash
# Pull latest changes
git pull

# Update dependencies
pip install -r requirements.txt --upgrade

# Restart application
python main.py
```

---

## � License

This project is licensed under the MIT License.

---

## ⚠️ Legal Disclaimer

This tool is for **personal use only**. Downloading videos may violate YouTube's Terms of Service. Users are responsible for complying with applicable laws and regulations. Use at your own risk.

---

## 🙏 Acknowledgments

- **yt-dlp** - Video download engine
- **FastAPI** - Web framework
- **SQLAlchemy** - Database ORM
- **Authlib** - OAuth implementation

---

## 👨‍💻 Developer

**Created by AhMed HaSsan**

Connect with me:
- 💼 Portfolio: Coming soon
- 📧 Email: Coming soon

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

---

## ⭐ Support

If you find this project useful, please give it a star!

---

**Made with ❤️ by AhMed HaSsan**
