from flask import Flask, request, jsonify
import yt_dlp
import os

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"message": "YouTube Transcriber API is running!"})

@app.route('/transcribe', methods=['POST'])
def transcribe():
    data = request.get_json()
    youtube_url = data.get('youtube_url')

    if not youtube_url:
        return jsonify({"error": "Missing 'youtube_url' in request body"}), 400

    # הגדרות yt-dlp כולל cookies.txt מתוך Render
    ydl_opts = {
        "cookies": "/etc/secrets/cookies.txt",  # ← הנתיב שבו Render שומר את הקובץ הסודי
        "quiet": True,
        "skip_download": True,
        "writeinfojson": False,
        "writesubtitles": True,
        "subtitleslangs": ["en"],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            subtitles = info.get("subtitles") or {}
            automatic_captions = info.get("automatic_captions") or {}
            title = info.get("title", "Unknown")

            return jsonify({
                "title": title,
                "subtitles": subtitles,
                "automatic_captions": automatic_captions
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
