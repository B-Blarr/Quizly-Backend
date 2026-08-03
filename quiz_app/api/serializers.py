from rest_framework import serializers
from quiz_app.models import Quiz, Question


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
            model = Question
            fields = ['id', 'question_title', 'question_options', 'answer',
                      'created_at', 'updated_at'    
            ]














