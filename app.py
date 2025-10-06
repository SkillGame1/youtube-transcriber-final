from flask import Flask, request, jsonify
import yt_dlp
import re
import os
import json
import time
import random
import urllib.request

app = Flask(__name__)

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

        # random user agent
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
            "Mozilla/5.0 (X11; Linux x86_64)",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)"
        ]

        ydl_opts = {
            'skip_download': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitlesformat': 'json3',
            'subtitleslangs': ['en', 'he'],
            'quiet': True,
            'no_warnings': True,
            'http_headers': {'User-Agent': random.choice(user_agents)}
        }

        # delay between requests
        time.sleep(random.uniform(1.5, 3.5))

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
    port = int(os.environ.get('PORT', 5001))
    app.run(host="0.0.0.0", port=port, debug=False)
