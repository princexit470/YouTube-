from flask import Flask, request, jsonify, render_template, send_file
import yt_dlp
import os
import glob

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/get_info', methods=['POST'])
def get_info():
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'Link daalein'}), 400

    # YOUTUBE BLOCK BYPASS SETTINGS
    ydl_opts = {
        'quiet': True, 
        'no_warnings': True,
        'nocheckcertificate': True,
        'extractor_args': {'youtube': {'player_client': ['android', 'web_safari', 'ios']}}
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return jsonify({
                'title': info.get('title'),
                'thumbnail': info.get('thumbnail'),
                'mp4_url': f"/download?url={url}&type=mp4",
                'mp3_url': f"/download?url={url}&type=mp3"
            })
    except Exception as e:
        # Agar error aaye toh exact error message frontend par bhejein
        print(f"Error: {str(e)}")
        return jsonify({'error': 'Video nahi mila. YouTube block kar raha hai. Kripya koi aur link try karein.'}), 400

@app.route('/download')
def download():
    url = request.args.get('url')
    dtype = request.args.get('type')
    
    # Ensure downloads folder exists
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
        
    ydl_opts = {
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'quiet': True,
        'nocheckcertificate': True,
        'extractor_args': {'youtube': {'player_client': ['android', 'web_safari', 'ios']}}
    }
    
    if dtype == 'mp3':
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })
    else:
        ydl_opts.update({'format': 'best[ext=mp4]/best'})

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # MP3 conversion ke baad file ka naam change ho jata hai
            if dtype == 'mp3':
                filename = os.path.splitext(filename)[0] + '.mp3'
                
            # File ka poora path nikalne ke liye
            final_path = os.path.abspath(filename)
            
            # File ko send karein
            response = send_file(final_path, as_attachment=True)
            
            # File send hone ke baad server se delete karne ka cleanup (optional)
            # @response.call_on_close
            # def cleanup():
            #     os.remove(final_path)
                
            return response
            
    except Exception as e:
        return f"Download Error: {str(e)}"

# Render ke liye port binding (Yeh line hona zaroori hai)
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
