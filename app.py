from flask import Flask, request, jsonify
import yt_dlp
import re
import os
import json
import urllib.request
import requests

app = Flask(__name__)

# הורדת קובץ cookies מגיטהאב בפעם הראשונה
def download_cookies_if_needed():
    """מוריד את קובץ ה-cookies אם הוא לא קיים"""
    cookie_path = os.path.join(os.getcwd(), "cookies.txt")
    
    if os.path.exists(cookie_path):
        print(f"✓ cookies.txt already exists at {cookie_path}")
        return
    
    # קריאת משתני סביבה
    GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
    GITHUB_REPO = os.environ.get('GITHUB_REPO')  # פורמט: username/repo
    COOKIES_FILE_PATH = os.environ.get('COOKIES_FILE_PATH', 'cookies.txt')  # נתיב בריפו
    
    if not GITHUB_TOKEN or not GITHUB_REPO:
        print("⚠ GITHUB_TOKEN or GITHUB_REPO not set - skipping cookies download")
        return
    
    # בניית URL להורדה
    url = f'https://raw.githubusercontent.com/{GITHUB_REPO}/main/{COOKIES_FILE_PATH}'
    headers = {'Authorization': f'token {GITHUB_TOKEN}'}
    
    try:
        print(f"⏳ Downloading cookies from GitHub...")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        with open(cookie_path, 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        print(f"✓ cookies.txt downloaded successfully to {cookie_path}")
    except requests.exceptions.RequestException as e:
        print(f"✗ Failed to download cookies: {e}")
        print("⚠ Application will continue without cookies file")

# הורד את הקובץ בהפעלה ראשונה
download_cookies_if_needed()

def extract_video_id(url: str) -> str:
    pattern = r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})"
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    if re.fullmatch(r"[a-zA-Z0-9_-]{11}", url):
        return url
    raise ValueError("Invalid YouTube URL or video ID")

@app.route('/')
def home():
    return jsonify({"message": "YouTube Transcriber API is running"})

@app.route('/transcribe', methods=['POST'])
def transcribe():
    try:
        data = request.json
        youtube_url = data['youtube_url']
        video_id = extract_video_id(youtube_url)
        full_url = f"https://www.youtube.com/watch?v={video_id}"

        cookie_path = os.path.join(os.getcwd(), "cookies.txt")

        ydl_opts = {
            'skip_download': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitlesformat': 'json3',
            'subtitleslangs': ['en', 'he'],
            'quiet': True,
            'no_warnings': True,
        }
        
        # הוסף cookiefile רק אם הקובץ קיים
        if os.path.exists(cookie_path):
            ydl_opts['cookiefile'] = cookie_path

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(full_url, download=False)

            subtitles = info.get('subtitles', {})
            auto_captions = info.get('automatic_captions', {})

            subtitle_data = None
            lang_used = None

            for lang in ['en', 'he']:
                if lang in subtitles:
                    subtitle_data = subtitles[lang]
                    lang_used = lang
                    break

            if not subtitle_data:
                for lang in ['en', 'he']:
                    if lang in auto_captions:
                        subtitle_data = auto_captions[lang]
                        lang_used = lang
                        break

            if not subtitle_data:
                return jsonify({"error": "No subtitles found"}), 404

            json3_url = None
            for fmt in subtitle_data:
                if fmt.get('ext') == 'json3':
                    json3_url = fmt.get('url')
                    break

            if not json3_url:
                return jsonify({"error": "Could not find JSON3 format"}), 404

            with urllib.request.urlopen(json3_url) as response:
                subs_data = json.loads(response.read().decode('utf-8'))

            transcript_text = ""
            if 'events' in subs_data:
                for event in subs_data['events']:
                    if 'segs' in event:
                        for seg in event['segs']:
                            if 'utf8' in seg:
                                transcript_text += seg['utf8']

            return jsonify({
                "video_id": video_id,
                "transcript": transcript_text.strip(),
                "title": info.get('title', ''),
                "language": lang_used
            })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=False)
