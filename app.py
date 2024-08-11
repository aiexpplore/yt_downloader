from flask import Flask, render_template, request, send_file, jsonify
import yt_dlp
from io import BytesIO
import os
import threading

app = Flask(__name__)

# Global variable to store download progress
download_progress = {'status': 'idle', 'percent': '0%', 'downloaded': '0', 'total': 'Unknown'}

def progress_hook(d):
    if d['status'] == 'downloading':
        download_progress['status'] = 'downloading'
        download_progress['percent'] = d.get('_percent_str', '0%')
        downloaded = d.get('downloaded_bytes', 0)
        total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)

        download_progress['downloaded'] = f'{downloaded / (1024 * 1024):.2f}'
        download_progress['total'] = f'{total / (1024 * 1024):.2f}' if total else 'Unknown'

def download_video(url, download_type):
    ydl_opts = {
        'format': 'bestaudio/best' if download_type == 'audio' else 'best[height<=480]',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'progress_hooks': [progress_hook],
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '128',
        }] if download_type == 'audio' else []
    }

    with app.app_context():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if download_type == 'audio':
                filename = os.path.splitext(filename)[0] + '.mp3'
    
    download_progress['status'] = 'completed'
    return filename

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    url = request.form['url']
    download_type = request.form['type']
    download_progress['status'] = 'starting'
    threading.Thread(target=download_video, args=(url, download_type)).start()
    return jsonify({'status': 'started'})

@app.route('/progress')
def progress():
    return jsonify(download_progress)

@app.route('/get_file')
def get_file():
    if download_progress['status'] == 'completed':
        filename = os.path.join('downloads', os.listdir('downloads')[-1])
        return send_file(filename, as_attachment=True)
    else:
        return jsonify({'status': 'not ready'})

if __name__ == '__main__':
    print("Server is starting...")
    
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
        
    app.run(debug=True)