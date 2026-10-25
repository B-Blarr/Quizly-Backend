from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from quiz_app.models import Quiz

from .permissions import IsOwner
from .serializers import QuizCreateSerializer, QuizSerializer
from .utils import QuizGenerationError, create_quiz_from_url


class QuizViewSet(viewsets.ModelViewSet):
    """CRUD endpoints for quizzes owned by the requesting user."""

    serializer_class = QuizSerializer
    permission_classes = [IsOwner, IsAuthenticated]
    throttle_scope = 'quiz_create'

    def get_throttles(self):
        """Limit only quiz creation, reading and editing stay unlimited."""
        if self.action == 'create':
            return [ScopedRateThrottle()]
        return super().get_throttles()

    def get_queryset(self):
        """Return own quizzes for the list, all quizzes for detail views."""
        if self.action == 'list':
            return Quiz.objects.filter(user=self.request.user)
        return Quiz.objects.all()

    def create(self, request, *args, **kwargs):
        """Create a quiz from the YouTube URL in the request body."""
        serializer = QuizCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            quiz = create_quiz_from_url(
                serializer.validated_data['url'], request.user)
        except QuizGenerationError as exc:
            return Response(
                {'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            QuizSerializer(quiz).data, status=status.HTTP_201_CREATED)
