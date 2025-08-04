import base64
import random
import re
import tempfile
from http import client
from django.utils.regex_helper import normalize
from django.views.decorators.csrf import csrf_exempt
from openai import OpenAI
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Teacher
from .serializers import TeacherSerializer

client = OpenAI(api_key="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")

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


class UploadImage(APIView):

    @csrf_exempt
    def post(self, request):
        if request.method != "POST":
            return JsonResponse({"error": "Only POST method allowed"}, status=405)

        lang = request.POST.get("lang")
        if not lang:
            return JsonResponse({"error": "Missing 'lang' parameter"}, status=400)

        if lang not in ["en", "gu"]:
            return JsonResponse({"error": "Invalid language. Use 'en' or 'gu'"}, status=400)

        menu_items = request.POST.get("menu", "")
        image_file = request.FILES.get("image")

        if not menu_items or not image_file:
            return JsonResponse({"error": "Missing menu or image"}, status=400)

        menu_list = [item.strip().lower() for item in menu_items.split(",") if item.strip()]

        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_img:
            for chunk in image_file.chunks():
                temp_img.write(chunk)
            image_path = temp_img.name

        try:
            with open(image_path, "rb") as img_file:
                image_bytes = img_file.read()
                image_base64 = base64.b64encode(image_bytes).decode("utf-8")

            # Prompts for language
            if lang == "gu":
                prompt_food = "આ છબીમાં તમે કયા ખોરાક વસ્તુઓ જોઈ શકો છો? ફક્ત યાદી આપો."
                prompt_nutrition = "તમે આ છબીમાં કયા ખોરાક જોઈ શકો છો? દરેક વસ્તુ માટે અંદાજિત પોષણ માહિતી (કૅલોરીઝ, પ્રોટીન, ફેટ, કાર્બસ) આપો."
            else:
                prompt_food = "What food items do you see in this image? Just list them."
                prompt_nutrition = "What food items do you see in this image? Also, for each item, provide its approximate nutritional information such as calories, protein, fat, and carbs."

            system_prompt = "You are a food image detection expert. Identify all food items visible in the image."

            # GPT call: Detected food items
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt_food},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}",
                                    "detail": "low"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=150,
                temperature=1
            )

            # GPT call: Nutrition
            responseNutrition = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt_nutrition},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}",
                                    "detail": "low"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=300
            )

            gpt_reply = response.choices[0].message.content.strip().lower()
            gpt_reply_Nutrition = responseNutrition.choices[0].message.content.strip().lower()

            detected_items = [
                item.strip("- ").strip()
                for item in gpt_reply.split("\n")
                if item.strip()
            ]

            found_items = [
                item for item in menu_list
                if any(normalize(item) == normalize(d) for d in detected_items)
            ]

            missing_items = [item for item in menu_list if item not in found_items]

            nutritions = {}
            current_item = None

            for line in gpt_reply_Nutrition.split("\n"):
                line = line.strip()
                if not line:
                    continue

                item_match = re.match(r"^\d+\.\s+\*{0,2}(.+?)\*{0,2}$", line)
                if item_match:
                    current_item = item_match.group(1).strip()
                    nutritions[current_item] = {}
                    continue

                if current_item:
                    nutrition_match = re.match(r"[-*]?\s*\*{0,2}([\w\s]+)\*{0,2}:\s*(.+)", line)
                    if nutrition_match:
                        key = nutrition_match.group(1).strip().lower()
                        value = nutrition_match.group(2).strip()
                        nutritions[current_item][key] = value

            return JsonResponse({
                "items_food": detected_items,
                "input_menu": menu_list,
                "found_items": found_items,
                "missing_items": missing_items,
                "nutritions": nutritions
            })

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
