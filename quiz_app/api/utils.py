import json
import os

import whisper
import yt_dlp
from django.conf import settings
from google import genai
from google.genai import types
from yt_dlp.utils import YoutubeDLError

from quiz_app.models import Question, Quiz

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
                    "question_options": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
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


class QuizGenerationError(Exception):
    """Raised when a quiz cannot be created from the given URL."""

    pass


def build_ydl_options(outtmpl):
    """Build the yt_dlp options for extracting audio as mp3."""
    return {
        "format": "bestaudio/best",
        "outtmpl": outtmpl,
        "quiet": True,
        "noplaylist": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
        }],
    }


def download_audio(url):
    """Download a video's audio track and return its path and video id."""
    os.makedirs(settings.MEDIA_TEMP_DIR, exist_ok=True)
    outtmpl = str(settings.MEDIA_TEMP_DIR / 'download.%(ext)s')
    ydl_opts = build_ydl_options(outtmpl)
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            audio_path = ydl.prepare_filename(info)
    except YoutubeDLError as exc:
        raise QuizGenerationError(
            "The video could not be downloaded.") from exc
    audio_path = os.path.splitext(audio_path)[0] + '.mp3'
    return audio_path, info["id"]


def transcribe_audio(audio_path):
    """Transcribe an audio file and return the plain text."""
    model = whisper.load_model(settings.WHISPER_MODEL)
    result = model.transcribe(audio_path)
    return result["text"]


def generate_quiz_data(transcript):
    """Ask Gemini to build a quiz from the transcript and return it."""
    response = client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=f"{PROMPT}\n\n{transcript}",
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=QUIZ_SCHEMA,
        ),
    )
    return json.loads(response.text)


def validate_quiz_data(data):
    """Raise if the generated quiz does not match the expected format."""
    for question in data["questions"]:
        if question["answer"] not in question["question_options"]:
            raise QuizGenerationError("The generated quiz is invalid.")


def create_quiz_from_url(url, user):
    """Run the full pipeline and store the resulting quiz."""
    audio_path, video_id = download_audio(url)
    try:
        transcript = transcribe_audio(audio_path)
    finally:
        os.remove(audio_path)
    data = generate_quiz_data(transcript)
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    validate_quiz_data(data)
    return save_quiz(data, video_url, user)


def build_questions(quiz, questions_data):
    """Create unsaved Question objects for the given quiz."""
    return [
        Question(
            quiz=quiz,
            question_title=q["question_title"],
            question_options=q["question_options"],
            answer=q["answer"],
        )
        for q in questions_data
    ]


def save_quiz(data, url, user):
    """Store the generated quiz and its questions."""
    quiz = Quiz.objects.create(
        user=user,
        title=data["title"],
        description=data["description"],
        video_url=url,
    )
    Question.objects.bulk_create(build_questions(quiz, data["questions"]))
    return quiz
