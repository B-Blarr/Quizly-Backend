from django.shortcuts import render
from rest_framework import viewsets


from quiz_app.models import Quiz, Question
from .serializers import QuestionSerializer, QuizSerializer


class QuizViewSet(viewsets.ModelViewSet):

    serializer_class = QuizSerializer

    def get_queryset(self):
        return Quiz.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)