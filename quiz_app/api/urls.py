from django.urls import path, include


urlpatterns = [
    path('quizzes/', include('auth_app.api.urls')),
]