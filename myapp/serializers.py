from rest_framework import serializers
from .models import Teacher

class TeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Teacher
        fields = ['id', 'username_en', 'username_gu', 'school_en', 'school_gu', 'location_en', 'location_gu']
