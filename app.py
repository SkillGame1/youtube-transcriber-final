from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
import re

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

    # חילוץ video ID מה-URL
    video_id_match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', youtube_url)
    if not video_id_match:
        return jsonify({"error": "Invalid YouTube URL"}), 400
    
    video_id = video_id_match.group(1)

    try:
        # קבלת הכתוביות
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        available_languages = []
        for transcript in transcript_list:
            available_languages.append({
                "language": transcript.language,
                "language_code": transcript.language_code,
                "is_generated": transcript.is_generated
            })

        return jsonify({
            "video_id": video_id,
            "available_languages": available_languages,
            "status": "success"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
