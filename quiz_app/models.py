from django.contrib.auth.models import User
from django.db import models


class Quiz(models.Model):
    """A quiz generated from a YouTube video."""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='quizzes')
    title = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    video_url = models.URLField()

    class Meta:
        verbose_name = 'Quiz'
        verbose_name_plural = 'Quizzes'
        ordering = ['-created_at']

    def __str__(self):
        """Return the quiz title as its label."""
        return self.title


class Question(models.Model):
    """A single multiple choice question belonging to a quiz."""

    quiz = models.ForeignKey(
        Quiz, on_delete=models.CASCADE, related_name='questions')
    question_title = models.CharField(max_length=200)
    question_options = models.JSONField()
    answer = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        """Return the question text as its label."""
        return self.question_title
