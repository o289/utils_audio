import os
import uuid
import subprocess
from yt_dlp import YoutubeDL

TMP_DIR = "./tmp"
os.makedirs(TMP_DIR, exist_ok=True)

COOKIE_FILE = "cookies/www.youtube.com_cookies.txt"

def get_video_info(url):
    ydl_opts = {
        'quiet': True,
        'cookiefile': COOKIE_FILE,
        'ignoreerrors': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info

def download_audio(url):
    filename_prefix = f"tmp_{uuid.uuid4().hex}"
    output_template = os.path.join(TMP_DIR, filename_prefix)

    print(f"🎵 ダウンロード開始: {url}")
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_template,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'noplaylist': True,
        'quiet': False,
        'cookiefile': COOKIE_FILE,
        'ignoreerrors': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }

    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    downloaded_path = output_template + ".mp3"
    return downloaded_path

def cut_audio(input_path, output_path, start, end):
    print("✂️ ffmpegで音声を切り出し中...")

    command = [
        "./bin/ffmpeg",
        "-y",
        "-ss", start,
        "-to", end,
        "-i", input_path,
        "-c", "copy",
        output_path
    ]

    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg での切り出しに失敗:\n{result.stderr}")
    else:
        print("✅ 切り出し完了！")

