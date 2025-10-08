from flask import Flask, request, jsonify
import yt_dlp
import os

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"message": "YouTube Transcriber API is running"})


@app.route('/transcribe', methods=['POST'])
def transcribe():
    data = request.get_json()
    youtube_url = data.get("youtube_url")

    if not youtube_url:
        return jsonify({"error": "Missing 'youtube_url' in request"}), 400

    # נתיב לקובץ העוגיות של Render (אם קיים)
    cookies_path = "/etc/secrets/cookies.txt"
print(f"[DEBUG] Checking if cookies file exists at {cookies_path}: {os.path.exists(cookies_path)}")
    # נוודא שהקובץ קיים לפני שנשתמש בו
    if os.path.exists(cookies_path):
        ydl_opts = {
            "quiet": True,
            "skip_download": True,
            "writesubtitles": True,
            "subtitleslangs": ["en"],
            "writeinfojson": False,
            "cookies": cookies_path
        }
    else:
        ydl_opts = {
            "quiet": True,
            "skip_download": True,
            "writesubtitles": True,
            "subtitleslangs": ["en"],
            "writeinfojson": False
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            subtitles = info.get("subtitles", {})
            automatic_captions = info.get("automatic_captions", {})

            if not subtitles and not automatic_captions:
                return jsonify({"error": "No subtitles found for this video"}), 404

            available = subtitles or automatic_captions
            langs = list(available.keys())
            return jsonify({
                "video_title": info.get("title"),
                "video_id": info.get("id"),
                "available_languages": langs,
                "status": "success"
            })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
