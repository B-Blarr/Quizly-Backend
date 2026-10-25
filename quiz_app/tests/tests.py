from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from yt_dlp.utils import YoutubeDLError

from quiz_app.api.utils import (
    QuizGenerationError,
    create_quiz_from_url,
    download_audio,
    save_quiz,
    transcribe_audio,
)
from quiz_app.models import Question, Quiz

User = get_user_model()


class ThrottleResetTestCase(APITestCase):
    """Start every test with empty throttle counters.

    Login, registration and quiz creation are throttled and the counters
    live in the cache, so one test's requests would count against the next.
    """

    def setUp(self):
        """Reset the throttle counters."""
        super().setUp()
        cache.clear()


class QuizTests(ThrottleResetTestCase):
    """Tests for the quiz endpoints and the generation helpers."""

    def setUp(self):
        """Log in one user and create a quiz for them and for another user."""
        super().setUp()
        self.user = User.objects.create_user(
            username='quizuser', password='SuperSecret123!',
            email='test@test.de',
        )
        self.client.post(
            reverse('login'),
            {'username': 'quizuser', 'password': 'SuperSecret123!'},
            format='json',
        )
        self.quiz = Quiz.objects.create(
            user=self.user, title="Test Quiz", description="A Test Quiz",
            video_url="https://www.youtube.com/watch?v=test",
        )
        Question.objects.create(
            quiz=self.quiz,
            question_title="Wie heißt die Hauptstadt von Frankreich?",
            question_options=["Berlin", "Paris", "Rom", "Madrid"],
            answer="Paris",
        )
        self.second_user = User.objects.create_user(
            username='secondquizuser', password='SuperSecret123!',
            email='test@secondtest.de',
        )
        self.second_quiz = Quiz.objects.create(
            user=self.second_user, title="New Test Quiz",
            description="A new Test Quiz",
            video_url="https://www.youtube.com/watch?v=secondtest",
        )

    def test_get_quiz_list(self):
        """The list only contains the quizzes of the logged in user."""
        url = reverse('quiz-list')
        response = self.client.get(url)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_quiz_list_not_authenticated_returns_401(self):
        """A client without cookies cannot read the quiz list."""
        client = APIClient()
        response = client.get(reverse('quiz-list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_quiz_of_other_user_returns_403(self):
        """Reading a foreign quiz is forbidden, not just not found."""
        response = self.client.get(
            reverse('quiz-detail', args=[self.second_quiz.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_quiz(self):
        """Deleting a quiz also removes its questions."""
        response = self.client.delete(
            reverse('quiz-detail', args=[self.quiz.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Question.objects.count(), 0)

    @patch('quiz_app.api.views.create_quiz_from_url')
    def test_eleventh_quiz_in_an_hour_is_rejected(self, mock_create):
        """Ten quizzes go through, the eleventh answers 429."""
        mock_create.return_value = self.quiz
        payload = {'url': 'https://www.youtube.com/watch?v=abc123'}
        for _ in range(10):
            response = self.client.post(
                reverse('quiz-list'), payload, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.post(
            reverse('quiz-list'), payload, format='json')
        self.assertEqual(
            response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_reading_quizzes_is_not_throttled(self):
        """Listing stays possible far beyond the creation limit."""
        for _ in range(15):
            response = self.client.get(reverse('quiz-list'))
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('quiz_app.api.views.create_quiz_from_url')
    def test_create_quiz(self, mock_create):
        """The view passes the validated URL and the user to the pipeline."""
        mock_create.return_value = self.quiz
        url = 'https://www.youtube.com/watch?v=abc123'
        response = self.client.post(
            reverse('quiz-list'), {'url': url}, format='json')
        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED, response.data)
        mock_create.assert_called_once_with(url, self.user)

    @patch('quiz_app.api.views.create_quiz_from_url')
    def test_create_quiz_download_fails_returns_400(self, mock_create):
        """A failing download is reported as 400, not as a server error."""
        mock_create.side_effect = QuizGenerationError(
            "The video could not be downloaded.")
        response = self.client.post(
            reverse('quiz-list'),
            {'url': 'https://www.youtube.com/watch?v=abc123'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_quiz_with_non_youtube_url_returns_400(self):
        """URLs from other platforms are rejected by the serializer."""
        response = self.client.post(
            reverse('quiz-list'),
            {'url': 'https://video.com/123456'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_save_quiz_creates_quiz_with_questions(self):
        """Generated data is stored as a quiz with all its questions."""
        data = {
            "title": "Generated Quiz",
            "description": "Eine Beschreibung",
            "questions": [
                {"question_title": "Frage 1",
                 "question_options": ["A", "B", "C", "D"], "answer": "A"},
                {"question_title": "Frage 2",
                 "question_options": ["A", "B", "C", "D"], "answer": "B"},
            ],
        }
        quiz = save_quiz(
            data, "https://www.youtube.com/watch?v=abc", self.user)
        self.assertEqual(quiz.title, "Generated Quiz")
        self.assertEqual(quiz.user, self.user)
        self.assertEqual(quiz.questions.count(), 2)
        self.assertEqual(
            quiz.questions.first().question_options, ["A", "B", "C", "D"])

    @patch('quiz_app.api.utils.os.remove')
    @patch('quiz_app.api.utils.generate_quiz_data')
    @patch('quiz_app.api.utils.transcribe_audio')
    @patch('quiz_app.api.utils.download_audio')
    def test_create_quiz_from_url_normalizes_video_url(
            self, mock_download, mock_transcribe, mock_generate, mock_remove):
        """A shorts URL is stored in the watch?v= format and cleaned up."""
        mock_download.return_value = ('tmp/download.mp3', 'FMrQYWGbm7M')
        mock_transcribe.return_value = 'Ein Transkript'
        mock_generate.return_value = {
            "title": "T", "description": "D",
            "questions": [{"question_title": "F",
                           "question_options": ["A", "B", "C", "D"],
                           "answer": "A"}],
        }
        quiz = create_quiz_from_url(
            'https://www.youtube.com/shorts/FMrQYWGbm7M', self.user)
        self.assertEqual(
            quiz.video_url, 'https://www.youtube.com/watch?v=FMrQYWGbm7M')
        mock_remove.assert_called_once_with('tmp/download.mp3')

    @patch('quiz_app.api.utils.yt_dlp.YoutubeDL')
    def test_download_audio_raises_quiz_generation_error(self, mock_ydl):
        """yt_dlp errors are translated into a QuizGenerationError."""
        mock_ydl.side_effect = YoutubeDLError('error')
        with self.assertRaises(QuizGenerationError):
            download_audio('https://www.youtube.com/watch?v=abc')

    @patch('quiz_app.api.utils.whisper.load_model')
    def test_transcribe_audio_returns_text(self, mock_load):
        """The transcription returns the plain text of the result."""
        mock_load.return_value.transcribe.return_value = {
            "text": "Ein Transkript"}
        result = transcribe_audio('tmp/download.mp3')
        self.assertEqual(result, "Ein Transkript")
