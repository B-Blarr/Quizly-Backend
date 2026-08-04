from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated

from quiz_app.models import Quiz
from .serializers import QuizSerializer
from .permissions import IsOwner


class QuizViewSet(viewsets.ModelViewSet):

    serializer_class = QuizSerializer
    permission_classes = [IsOwner, IsAuthenticated]

    def get_queryset(self):
        if self.action == 'list':
            return Quiz.objects.filter(user=self.request.user)
        return Quiz.objects.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class QuizCreateView(CreateAPIView):
    pass
