# How to Add YouTube Cookies

## Why Do I Need This?

YouTube sometimes requires authentication to download videos. Adding your YouTube cookies allows the app to download videos as if you were logged in, avoiding bot detection.

## Quick Steps

### 1. Install Cookie Exporter Extension

**Chrome/Edge:**
- Go to: https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc
- Click "Add to Chrome/Edge"

**Firefox:**
- Go to: https://addons.mozilla.org/firefox/addon/cookies-txt/
- Click "Add to Firefox"

### 2. Export YouTube Cookies

1. Go to **youtube.com**
2. Make sure you're **logged in**
3. Click the **cookie extension icon** in your browser toolbar
4. Click **"Export"** or **"Get cookies.txt"**
5. Save the file as `youtube_cookies.txt`

### 3. Add Cookies to App

**Option A: Using the Helper Script (Easiest)**

```powershell
# Run the helper script
venv\Scripts\python.exe add_cookies.py

# When prompted:
# - Enter your username (admin)
# - Enter path to youtube_cookies.txt
```

**Option B: Using the Web Interface (Coming Soon)**

The admin panel will have a cookies upload feature.

### 4. Test It!

Go back to the main site and try downloading a video. It should work now!

## Troubleshooting

**"File not found" error:**
- Make sure you provide the full path to the cookies file
- Example: `C:\Users\YourName\Downloads\youtube_cookies.txt`

**"No encryption key" warning:**
- The script will generate one for you
- Copy the `COOKIE_ENCRYPTION_KEY=...` line
- Add it to your `.env` file

**Downloads still failing:**
- Make sure your YouTube cookies are fresh (export them again)
- Make sure you're logged into YouTube when exporting
- Try a different video

## Security Notes

⚠️ **Important:**
- Cookies are encrypted before storage
- Never share your cookies file with anyone
- Cookies expire after some time (re-export if needed)
- The app stores them securely in the database

## Alternative: Use yt-dlp Directly

If you prefer not to add cookies, you can still use the app for video info and formats, but downloads might fail for some videos due to YouTube's bot protection.
