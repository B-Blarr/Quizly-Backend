from django.contrib import admin

from .models import Question, Quiz


class QuestionInline(admin.TabularInline):
    """Allow editing a quiz's questions on the quiz page itself."""

    model = Question
    extra = 0


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    """Admin configuration for quizzes."""

    list_display = ('title', 'user', 'created_at')
    list_filter = ('created_at', 'user')
    search_fields = ('title', 'description')
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """Admin configuration for single questions."""

    list_display = ('question_title', 'quiz', 'answer')
    search_fields = ('question_title',)
