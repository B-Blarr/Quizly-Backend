import os
import json
import yt_dlp
import whisper

from google import genai
from google.genai import types
from django.conf import settings


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
    model=whisper.load_model(settings.WHISPER_MODEL)
    result = model.transcribe(audio_path)
    return result["text"]


client = genai.Client(api_key=settings.GEMINI_API_KEY)

QUIZ_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "description": {"type": "string"},
        "questions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "question_title": {"type": "string"},
                    "question_options": {"type": "array", "items": {"type": "string"}},
                    "answer": {"type": "string"},
                },
                "required": ["question_title", "question_options", "answer"],
            },
        },
    },
    "required": ["title", "description", "questions"],
}

PROMPT = """Based on the following transcript, generate a quiz in valid JSON format.

The quiz must follow this exact structure:

{

  "title": "Create a concise quiz title based on the topic of the transcript.",

  "description": "Summarize the transcript in no more than 150 characters. Do not include any quiz questions or answers.",

  "questions": [

    {

      "question_title": "The question goes here.",

      "question_options": ["Option A", "Option B", "Option C", "Option D"],

      "answer": "The correct answer from the above options"

    },

    ...

    (exactly 10 questions)

  ]

}

Requirements:

- Every question and answer has to be in German.

- Each question must have exactly 4 distinct answer options.

- Only one correct answer is allowed per question, and it must be present in 'question_options'.

- The output must be valid JSON and parsable as-is (e.g., using Python's json.loads).

- Do not include explanations, comments, or any text outside the JSON.
"""

def generate_quiz_data(transcript):

    response = client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=f"{PROMPT}\n\n{transcript}",
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=QUIZ_SCHEMA,
        ),
    )
    return json.loads(response.text)
