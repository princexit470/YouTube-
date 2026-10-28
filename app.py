from flask import Flask, request, jsonify, render_template, send_file
import yt_dlp
import os

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COOKIE_PATH = os.path.join(BASE_DIR, 'cookies.txt')

# POT provider aur format fix ke saath settings
YDL_OPTS = {
    'quiet': True, 
    'no_warnings': True,
    'nocheckcertificate': True,
    'cookiefile': COOKIE_PATH,
    'extractor_args': {
        'youtube': {
            'player_client': ['android', 'ios', 'web'], # TV/mweb hata diya
            'youtubepot-bgutilhttp': {
                'base_url': 'http://127.0.0.1:4416' # POT Provider ka address
            }
        }
    }
}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/get_info', methods=['POST'])
def get_info():
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'Kripya link daalein'}), 400

    try:
        with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
            info = ydl.extract_info(url, download=False)
            return jsonify({
                'title': info.get('title'),
                'thumbnail': info.get('thumbnail'),
                'mp4_url': f"/download?url={url}&type=mp4",
                'mp3_url': f"/download?url={url}&type=mp3"
            })
    except Exception as e:
        print(f"ERROR LOG: {str(e)}") 
        return jsonify({'error': 'Video fetch nahi hui. YouTube block kar raha hai.'}), 400

@app.route('/download')
def download():
    url = request.args.get('url')
    dtype = request.args.get('type')
    
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
        
    dl_opts = YDL_OPTS.copy()
    dl_opts['outtmpl'] = 'downloads/%(title)s.%(ext)s'
    
    if dtype == 'mp3':
        dl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })
    else:
        # Format fix: Ab video aur audio alag mangwayenge aur merge karenge
        dl_opts.update({
            'format': 'bestvideo*+bestaudio/best',
            'merge_output_format': 'mp4'
        })

    try:
        with yt_dlp.YoutubeDL(dl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            if dtype == 'mp3':
                filename = os.path.splitext(filename)[0] + '.mp3'
            else:
                base, ext = os.path.splitext(filename)
                if ext != '.mp4':
                    filename = base + '.mp4'
                
            final_path = os.path.abspath(filename)
            return send_file(final_path, as_attachment=True)
            
    except Exception as e:
        print(f"DOWNLOAD ERROR LOG: {str(e)}")
        return f"Download Error: Format issue ya YouTube block."

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
