import os
import yt_dlp
import whisper

tmp_filename = 'download.%(ext)s'

def download_audio(url):

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": tmp_filename,
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
    model = whisper.load_model("base")
    result = model.transcribe(audio_path)
    return result["text"]



