from django.urls import path
from .views import TeacherCreateAPIView, TeacherListAPIView, TeacherDetailAPIView, SurveyAPIView

urlpatterns = [
    path('teachers/create/', TeacherCreateAPIView.as_view(), name='teacher-create'),
    path('teachers/', TeacherListAPIView.as_view(), name='teacher-list'),
    path('teachers/<int:pk>/', TeacherDetailAPIView.as_view(), name='teacher-detail'),

    path('getSurvey/', SurveyAPIView.as_view(), name='get-survey'),
    path('getSurvey/<str:lang>/', SurveyAPIView.as_view(), name='get-survey-lang'),



]
