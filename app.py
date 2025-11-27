from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
import os

app = Flask(__name__)
# Izinkan semua domain mengakses (untuk development). 
# Nanti saat production, ganti '*' dengan domain website Anda.
CORS(app) 

# Konfigurasi folder download sementara
DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

@app.route('/')
def home():
    return "7unisaver Backend is Running!"

# --- ENDPOINT 1: ANALYZE LINK ---
@app.route('/api/analyze', methods=['POST'])
def analyze_video():
    data = request.json
    url = data.get('url')

    if not url:
        return jsonify({'error': 'URL is required'}), 400

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        # Mengambil info tanpa download
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Siapkan data untuk dikirim ke frontend
            return jsonify({
                'title': info.get('title', 'Unknown Title'),
                'thumbnail': info.get('thumbnail'),
                'platform': info.get('extractor_key'),
                'duration': info.get('duration'),
                'formats': [
                    # Sederhanakan format untuk dikirim ke UI
                    {'id': 'best', 'label': 'Best Quality (Auto)'},
                    {'id': 'audio', 'label': 'Audio Only (MP3)'}
                ]
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- ENDPOINT 2: DOWNLOAD VIDEO ---
@app.route('/api/download', methods=['POST'])
def download_video():
    data = request.json
    url = data.get('url')
    fmt = data.get('format', 'best') # 'best' atau 'audio'

    if not url:
        return jsonify({'error': 'URL missing'}), 400

    try:
        # Konfigurasi yt-dlp
        ydl_opts = {
            'outtmpl': f'{DOWNLOAD_FOLDER}/%(id)s.%(ext)s',
            'quiet': True,
        }

        if fmt == 'audio':
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        else:
            ydl_opts['format'] = 'bestvideo+bestaudio/best'

        # Eksekusi Download
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # Jika audio, ekstensi berubah jadi mp3 setelah post-processing
            if fmt == 'audio':
                filename = filename.rsplit('.', 1)[0] + '.mp3'

        # Kirim file ke user
        return send_file(filename, as_attachment=True)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Jalankan di port 5000
    app.run(debug=True, port=5000)