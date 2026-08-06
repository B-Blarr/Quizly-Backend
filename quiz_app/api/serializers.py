from urllib.parse import urlparse

from rest_framework import serializers

from quiz_app.models import Question, Quiz

YOUTUBE_HOSTS = ('youtube.com', 'www.youtube.com', 'm.youtube.com', 'youtu.be')


class QuestionSerializer(serializers.ModelSerializer):
    """Serialize a single question of a quiz."""

    class Meta:
        model = Question
        fields = ['id', 'question_title', 'question_options', 'answer',
                  'created_at', 'updated_at']


class QuizSerializer(serializers.ModelSerializer):
    """Serialize a quiz including its nested questions."""

    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = ['id', 'title', 'description', 'created_at', 'updated_at',
                  'video_url', 'questions']
        read_only_fields = ['video_url']


class QuizCreateSerializer(serializers.Serializer):
    """Validate the YouTube URL sent when creating a new quiz."""

    url = serializers.URLField()

    def validate_url(self, value):
        """Ensure the given URL points to YouTube."""
        if urlparse(value).hostname not in YOUTUBE_HOSTS:
            raise serializers.ValidationError('Only YouTube URLs are allowed.')
        return value
