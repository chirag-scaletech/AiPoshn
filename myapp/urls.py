from django.urls import path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

from .views import (
    TeacherCreateAPIView,
    TeacherListAPIView,
    TeacherDetailAPIView,
    SurveyAPIView,
    UploadImage, FoodImageAPIView,
)

schema_view = get_schema_view(
    openapi.Info(
        title="AiPoshn API",
        default_version='v1',
        description="API for Mid-Day Meal",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Teacher APIs
    path('teachers/create/', TeacherCreateAPIView.as_view(), name='teacher-create'),
    path('teachers/<int:pk>/', TeacherDetailAPIView.as_view(), name='teacher-detail'),

    # Survey API
    path('survey/', SurveyAPIView.as_view(), name='get-survey'),
    path('survey/<str:lang>/', SurveyAPIView.as_view(), name='get-survey-lang'),

    # Image Menu Verification
    path('verify-menu/', UploadImage.as_view(), name='verify-menu'),

    path('verify-menus/', FoodImageAPIView.as_view(), name='verify-menu'),

    # Swagger/OpenAPI UI
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),


]
