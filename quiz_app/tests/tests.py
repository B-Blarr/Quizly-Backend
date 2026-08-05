from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from quiz_app.api.utils import QuizGenerationError
from quiz_app.models import Quiz, Question
from unittest.mock import patch



User = get_user_model()


class QuizTests(APITestCase):

    def setUp(self):
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
        url = reverse('quiz-list')
        response = self.client.get(url)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_quiz_list_not_authenticated_returns_401(self):
        client = APIClient()
        response = client.get(reverse('quiz-list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_quiz_of_other_user_returns_403(self):
        response = self.client.get(reverse('quiz-detail', args=[self.second_quiz.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_quiz(self):
        response = self.client.delete(reverse('quiz-detail', args=[self.quiz.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Question.objects.count(), 0)

    
    @patch('quiz_app.api.views.create_quiz_from_url')
    def test_create_quiz(self, mock_create):
        mock_create.return_value = self.quiz
        url = 'https://www.youtube.com/watch?v=abc123'
        response = self.client.post(
            reverse('quiz-list'), {'url': url}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        mock_create.assert_called_once_with(url, self.user)

    @patch('quiz_app.api.views.create_quiz_from_url')
    def test_create_quiz_download_fails_returns_400(self, mock_create):
        mock_create.side_effect = QuizGenerationError("The video could not be downloaded.")
        response = self.client.post(
            reverse('quiz-list'),
            {'url': 'https://www.youtube.com/watch?v=abc123'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
