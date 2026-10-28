from flask import Flask, request, jsonify, render_template, send_file
import yt_dlp
import os

app = Flask(__name__)

# Yahan humne cookies.txt ka rasta de diya hai
YDL_OPTS = {
    'quiet': True, 
    'no_warnings': True,
    'nocheckcertificate': True,
    'cookiefile': 'cookies.txt',  # <--- YEH SABSE ZAROORI LINE HAI
    'extractor_args': {
        'youtube': {
            'player_client': ['android', 'web_safari', 'ios', 'web'],
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
        print(f"Error: {str(e)}") # Yeh error Render ke logs mein dikhega
        return jsonify({'error': 'YouTube ne block kar diya hai. Kripya cookies update karein ya thodi der baad try karein.'}), 400

@app.route('/download')
def download():
    url = request.args.get('url')
    dtype = request.args.get('type')
    
    # Downloads folder check karein
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
        dl_opts.update({'format': 'best[ext=mp4]/best'})

    try:
        with yt_dlp.YoutubeDL(dl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            if dtype == 'mp3':
                filename = os.path.splitext(filename)[0] + '.mp3'
                
            final_path = os.path.abspath(filename)
            return send_file(final_path, as_attachment=True)
            
    except Exception as e:
        print(f"Download Error: {str(e)}")
        return f"Download Error: YouTube ne download block kar diya hai. (Check Render logs for details)"

# Render par deploy karne ke liye port binding
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
