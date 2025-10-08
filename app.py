from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
import re
import time

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
    video_id_match = re.search(r'(?:v=|/)([0-9A-Za-z_-]{11})', youtube_url)
    if not video_id_match:
        return jsonify({"error": "Invalid YouTube URL"}), 400
    
    video_id = video_id_match.group(1)
    print(f"[DEBUG] Extracted video ID: {video_id}")

    # ניסיון מספר פעמים עם המתנה בין ניסיונות
    max_retries = 3
    retry_delay = 2  # שניות
    
    for attempt in range(max_retries):
        try:
            print(f"[DEBUG] Attempt {attempt + 1}/{max_retries}")
            
            # נסיון לקבל transcript בשפה כלשהי
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            
            return jsonify({
                "video_id": video_id,
                "status": "success",
                "message": "Subtitles found",
                "transcript_preview": transcript[:3] if len(transcript) > 0 else []
            })

        except TranscriptsDisabled:
            return jsonify({"error": "Transcripts are disabled for this video"}), 404
        
        except NoTranscriptFound:
            return jsonify({"error": "No transcripts found for this video"}), 404
        
        except Exception as e:
            error_message = str(e)
            print(f"[ERROR] Attempt {attempt + 1} failed: {error_message}")
            
            # אם זה שגיאת 429 וזה לא הניסיון האחרון, נחכה וננסה שוב
            if "429" in error_message and attempt < max_retries - 1:
                print(f"[DEBUG] Waiting {retry_delay} seconds before retry...")
                time.sleep(retry_delay)
                retry_delay *= 2  # הכפלת זמן ההמתנה
                continue
            
            # אם הגענו לכאן, זה הניסיון האחרון או שגיאה שונה
            return jsonify({
                "error": error_message,
                "suggestion": "YouTube may be rate limiting requests. Try again in a few minutes."
            }), 500


@app.route('/get-transcript', methods=['POST'])
def get_transcript():
    """קבלת הכתוביות המלאות"""
    data = request.get_json()
    youtube_url = data.get("youtube_url")
    language = data.get("language", "en")

    if not youtube_url:
        return jsonify({"error": "Missing 'youtube_url' in request"}), 400

    video_id_match = re.search(r'(?:v=|/)([0-9A-Za-z_-]{11})', youtube_url)
    if not video_id_match:
        return jsonify({"error": "Invalid YouTube URL"}), 400
    
    video_id = video_id_match.group(1)

    # ניסיון מספר פעמים
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            print(f"[DEBUG] Attempt {attempt + 1}/{max_retries}")
            
            # הורדת הכתוביות בשפה המבוקשת
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[language])
            
            # המרה לטקסט רציף
            full_text = " ".join([entry['text'] for entry in transcript])

            return jsonify({
                "video_id": video_id,
                "language": language,
                "transcript": transcript,
                "full_text": full_text,
                "status": "success"
            })

        except NoTranscriptFound:
            return jsonify({"error": f"No transcript found for language: {language}"}), 404
        
        except Exception as e:
            error_message = str(e)
            print(f"[ERROR] Attempt {attempt + 1} failed: {error_message}")
            
            if "429" in error_message and attempt < max_retries - 1:
                print(f"[DEBUG] Waiting {retry_delay} seconds before retry...")
                time.sleep(retry_delay)
                retry_delay *= 2
                continue
            
            return jsonify({
                "error": error_message,
                "suggestion": "YouTube may be rate limiting requests. Try again in a few minutes."
            }), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
