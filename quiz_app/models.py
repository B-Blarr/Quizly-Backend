from django.db import models

from django.contrib.auth.models import User


class Quiz(models.Model):
    user = models.ForeignKey(User, related_name='quizzes', on_delete=models.CASCADE)
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
        return self.title


