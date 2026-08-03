import os
import yt_dlp
import whisper

from django.conf import settings

tmp_filename = 'download.%(ext)s'

def download_audio(url):
    os.makedirs(settings.MEDIA_TEMP_DIR, exist_ok=True)
    outtmpl = str(settings.MEDIA_TEMP_DIR / 'download.%(ext)s')

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": outtmpl,
        "quiet": True,
        "noplaylist": True,
        "postprocessors": [{
        "key": "FFmpegExtractAudio",
        "preferredcodec": "mp3",
        }],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        audio_path = ydl.prepare_filename(info)    
    audio_path = os.path.splitext(audio_path)[0] + '.mp3'
    return audio_path

def transcribe_audio(audio_path):
    """Transcribe an audio file and return the plain text."""
    model = whisper.load_model("tiny")
    result = model.transcribe(audio_path)
    return result["text"]


