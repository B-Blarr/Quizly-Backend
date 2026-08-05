from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from quiz_app.models import Quiz, Question, User

class QuizTests(APITestCase):

    def setUp(self):
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

    
