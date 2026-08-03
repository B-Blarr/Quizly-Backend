from django.shortcuts import render
from rest_framework import viewsets


from quiz_app.models import Quiz, Question
from .serializers import QuestionSerializer, QuizSerializer


class QuizViewSet(viewsets.ModelViewSet):

    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer


    def get_queryset(self):

        return Quiz.objects.filter(user=self.request.user)