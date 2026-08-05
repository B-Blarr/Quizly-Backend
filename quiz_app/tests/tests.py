from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from quiz_app.models import Quiz, Question


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
    
