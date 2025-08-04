import random

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Teacher
from .serializers import TeacherSerializer

class TeacherCreateAPIView(APIView):
    def post(self, request):
        lang = request.query_params.get('lang', 'en')
        if lang not in ['en', 'gu']:
            return Response({'error': 'Invalid language'}, status=status.HTTP_400_BAD_REQUEST)

        # username = "Vaishaliben Patel" if lang == 'en' else "વૈશાલી બેન પટેલ"
        # teacher = Teacher.objects.create(
        #     username_en=username if lang == 'en' else '',
        #     username_gu=username if lang == 'gu' else ''
        # )

        # Always save both fields regardless of lang
        # teacher = Teacher.objects.create(
        #     username_en="Vaishaliben Patel",
        #     username_gu="વૈશાલીબેન પટેલ"
        # )

        names_en = ["Vaishaliben Patel", "Parulben Shah", "Manishaben Desai"]
        names_gu = ["વૈશાલીબેન પટેલ", "પારૂલબેન શાહ", "મનીષાબેન દેસાઈ"]

        index = random.randint(0, len(names_en) - 1)

        teacher = Teacher.objects.create(
            username_en=names_en[index],
            username_gu=names_gu[index]
        )

        return Response(TeacherSerializer(teacher).data, status=status.HTTP_201_CREATED)


class TeacherListAPIView(APIView):
    def get(self, request):
        lang = request.query_params.get('lang', 'en')
        if lang not in ['en', 'gu']:
            return Response({'error': 'Invalid language'}, status=status.HTTP_400_BAD_REQUEST)

        teachers = Teacher.objects.all()
        data = []
        for teacher in teachers:
            data.append({
                "id": teacher.id,
                "username": teacher.username_en if lang == 'en' else teacher.username_gu
            })
        return Response(data, status=status.HTTP_200_OK)

class TeacherDetailAPIView(APIView):
    def get(self, request, pk):
        lang = request.query_params.get('lang', 'en')
        if lang not in ['en', 'gu']:
            return Response({'error': 'Invalid language'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            teacher = Teacher.objects.get(pk=pk)
        except Teacher.DoesNotExist:
            return Response({'error': 'Teacher not found'}, status=status.HTTP_404_NOT_FOUND)

        data = {
            "id": teacher.id,
            "username": teacher.username_en if lang == 'en' else teacher.username_gu
        }
        return Response(data, status=status.HTTP_200_OK)

from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

class SurveyAPIView(APIView):
    permission_classes = [AllowAny]  # Optional: allows public access

    def get(self, request, lang=None):
        lang = lang or request.query_params.get('lang', 'en')
        if lang not in ['en', 'gu']:
            return JsonResponse({'error': 'Invalid language'}, status=400)

        # [Rest of the survey dictionary logic as above]

    # def get(self, request):
    #     lang = request.query_params.get('lang', 'en')
    #     if lang not in ['en', 'gu']:
    #         return JsonResponse({'error': 'Invalid language'}, status=400)

        if lang == 'gu':
            survey = {
                "surveyTitle": "ઝડપી ખોરાક સેવા સર્વે",
                "description": "આજની નાસ્તાની સેવાઓ વિશેના કેટલાક ઝડપી પ્રશ્નોના જવાબ આપો.",
                "questions": [
                    {
                        "id": "q1",
                        "text": "શું તમામ વિદ્યાર્થીઓને સમયસર ભોજન આપવામાં આવ્યું?",
                        "options": ["હા, બધાને", "હા, પરંતુ મોડું", "ના", "આંશિક"]
                    },
                    {
                        "id": "q2",
                        "text": "ખોરાકની તાજગી કેવી હતી?",
                        "options": ["ખૂબ તાજું", "તાજું", "ઠીકઠાક", "તાજું નહોતું"]
                    },
                    {
                        "id": "q3",
                        "text": "શું ભોજનની માત્રા તમામ વિદ્યાર્થીઓ માટે પૂરતી હતી?",
                        "options": ["ગણીએ એટલું વધારે", "પુરતું", "ઘટતું", "સૌ માટે પૂરતું નહતું"]
                    },
                    {
                        "id": "q4",
                        "text": "શુ ભોજન વિતરણ દરમ્યાન સ્વચ્છતા જાળવવામાં આવી?",
                        "options": ["ઉત્કૃષ્ટ", "સારી", "સારું છે પણ સુધારો જોઈએ", "ખરાબ"]
                    },
                    {
                        "id": "q5",
                        "text": "આજની નાસ્તાની સેવા તમે કેટલી પ્રમાણમાં રેટ કરો?",
                        "options": ["ઉત્કૃષ્ટ", "સારી", "સરેરાશ", "ખરાબ"]
                    }
                ]
            }
        else:  # English
            survey = {
                "surveyTitle": "Quick Food Service Survey",
                "description": "Please answer these quick questions about today's breakfast service.",
                "questions": [
                    {
                        "id": "q1",
                        "text": "Was the meal served to all students on time?",
                        "options": ["Yes, to all", "Yes, but late", "No", "Partial"]
                    },
                    {
                        "id": "q2",
                        "text": "How was the freshness of the food?",
                        "options": ["Very Fresh", "Fresh", "Okay", "Not Fresh"]
                    },
                    {
                        "id": "q3",
                        "text": "Was the food quantity sufficient for all students?",
                        "options": ["More than enough", "Just enough", "Less than required", "Not sufficient at all"]
                    },
                    {
                        "id": "q4",
                        "text": "Was hygiene maintained during food distribution?",
                        "options": ["Excellent hygiene", "Good hygiene", "Acceptable but needs improvement", "Poor hygiene"]
                    },
                    {
                        "id": "q5",
                        "text": "Overall, how would you rate the breakfast service today?",
                        "options": ["Excellent", "Good", "Average", "Poor"]
                    }
                ]
            }

        return JsonResponse(survey, safe=False)
