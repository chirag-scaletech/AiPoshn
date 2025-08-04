from django.urls import path
from .views import (
    TeacherCreateAPIView,
    TeacherListAPIView,
    TeacherDetailAPIView,
    SurveyAPIView,
    UploadImage,
)

urlpatterns = [
    # Teacher APIs
    path('api/teachers/', TeacherListAPIView.as_view(), name='teacher-list'),
    path('api/teachers/create/', TeacherCreateAPIView.as_view(), name='teacher-create'),
    path('api/teachers/<int:pk>/', TeacherDetailAPIView.as_view(), name='teacher-detail'),

    # Survey API
    path('api/survey/', SurveyAPIView.as_view(), name='get-survey'),
    path('api/survey/<str:lang>/', SurveyAPIView.as_view(), name='get-survey-lang'),

    # Image Menu Verification
    path('api/verify-menu/', UploadImage.as_view(), name='verify-menu'),

]
