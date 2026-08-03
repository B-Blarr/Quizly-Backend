from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated


from quiz_app.models import Quiz, Question
from .serializers import QuestionSerializer, QuizSerializer
from .permissions import IsOwner


class QuizViewSet(viewsets.ModelViewSet):

    serializer_class = QuizSerializer
    permission_classes = [IsOwner, IsAuthenticated]

    def get_queryset(self):
        return Quiz.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)