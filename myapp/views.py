import base64
import json
import os
import random
import re
import tempfile
from http import client
from django.utils.regex_helper import normalize
from django.views.decorators.csrf import csrf_exempt
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from openai import OpenAI
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Teacher
from .serializers import TeacherSerializer
from dotenv import load_dotenv
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

load_dotenv()  # Loads from .env
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class TeacherCreateAPIView(APIView):
    # def post(self, request):
    #     lang = request.query_params.get('lang', 'en')
    #     if lang not in ['en', 'gu']:
    #         return Response({'error': 'Invalid language'}, status=status.HTTP_400_BAD_REQUEST)
    #
    #     # username = "Vaishaliben Patel" if lang == 'en' else "વૈશાલી બેન પટેલ"
    #     # teacher = Teacher.objects.create(
    #     #     username_en=username if lang == 'en' else '',
    #     #     username_gu=username if lang == 'gu' else ''
    #     # )
    #
    #     # Always save both fields regardless of lang
    #     # teacher = Teacher.objects.create(
    #     #     username_en="Vaishaliben Patel",
    #     #     username_gu="વૈશાલીબેન પટેલ"
    #     # )
    #
    #     names_en = ["Vaishaliben Patel", "Parulben Shah", "Manishaben Desai"]
    #     names_gu = ["વૈશાલીબેન પટેલ", "પારૂલબેન શાહ", "મનીષાબેન દેસાઈ"]
    #
    #     index = random.randint(0, len(names_en) - 1)
    #
    #     teacher = Teacher.objects.create(
    #         username_en=names_en[index],
    #         username_gu=names_gu[index]
    #     )
    #
    #     return Response(TeacherSerializer(teacher).data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                name="lang",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="Language code: 'en' (English) or 'gu' (Gujarati)",
                required=False,
                default='en'
            )
        ]
    )
    def post(self, request):
        lang = request.query_params.get('lang')
        if not lang:
            return Response({'error': "Missing 'lang' parameter"}, status=status.HTTP_400_BAD_REQUEST)

        if lang not in ['en', 'gu']:
            return Response({'error': "Invalid language. Use 'en' or 'gu'"}, status=status.HTTP_400_BAD_REQUEST)

        names_en = ["Vaishaliben Patel", "Parulben Shah", "Manishaben Desai"]
        names_gu = ["વૈશાલીબેન પટેલ", "પારૂલબેન શાહ", "મનીષાબેન દેસાઈ"]

        schools_en = ["Government Primary School, Sector 15"]
        schools_gu = ["સરકારી પ્રાથમિક શાળા, સેક્ટર ૧૫"]

        locations_en = ["Gandhinagar, Gujarat"]
        locations_gu = ["ગાંધીનગર, ગુજરાત"]

        index = random.randint(0, len(names_en) - 1)

        teacher = Teacher.objects.create(
            username_en=names_en[index],
            username_gu=names_gu[index],
            school_en=schools_en[0],
            school_gu=schools_gu[0],
            location_en=locations_en[0],
            location_gu=locations_gu[0],
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
                "username": teacher.username_en if lang == 'en' else teacher.username_gu,
                "school": teacher.school_en if lang == 'en' else teacher.school_gu,
                "location": teacher.location_en if lang == 'en' else teacher.location_gu
            })
        return Response(data, status=status.HTTP_200_OK)

class TeacherDetailAPIView(APIView):
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                name="lang",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="Language code: 'en' (English) or 'gu' (Gujarati)",
                required=False,
                default='en'
            )
        ]
    )
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
            "username": teacher.username_en if lang == 'en' else teacher.username_gu,
            "school": teacher.school_en if lang == 'en' else teacher.school_gu,
            "location": teacher.location_en if lang == 'en' else teacher.location_gu
        }
        return Response(data, status=status.HTTP_200_OK)

class SurveyAPIView(APIView):
    permission_classes = [AllowAny]  # Optional: allows public access

    # def get(self, request, lang=None):
    #     lang = lang or request.query_params.get('lang', 'en')
    #     if lang not in ['en', 'gu']:
    #         return JsonResponse({'error': 'Invalid language'}, status=400)
    #
    #     # [Rest of the survey dictionary logic as above]
    #
    # # def get(self, request):
    # #     lang = request.query_params.get('lang', 'en')
    # #     if lang not in ['en', 'gu']:
    # #         return JsonResponse({'error': 'Invalid language'}, status=400)
    #
    #     if lang == 'gu':
    #         survey = {
    #             "surveyTitle": "ઝડપી ખોરાક સેવા સર્વે",
    #             "description": "આજની નાસ્તાની સેવાઓ વિશેના કેટલાક ઝડપી પ્રશ્નોના જવાબ આપો.",
    #             "questions": [
    #                 {
    #                     "id": "q1",
    #                     "text": "શું તમામ વિદ્યાર્થીઓને સમયસર ભોજન આપવામાં આવ્યું?",
    #                     "options": ["હા, બધાને", "હા, પરંતુ મોડું", "ના", "આંશિક"]
    #                 },
    #                 {
    #                     "id": "q2",
    #                     "text": "ખોરાકની તાજગી કેવી હતી?",
    #                     "options": ["ખૂબ તાજું", "તાજું", "ઠીકઠાક", "તાજું નહોતું"]
    #                 },
    #                 {
    #                     "id": "q3",
    #                     "text": "શું ભોજનની માત્રા તમામ વિદ્યાર્થીઓ માટે પૂરતી હતી?",
    #                     "options": ["ગણીએ એટલું વધારે", "પુરતું", "ઘટતું", "સૌ માટે પૂરતું નહતું"]
    #                 },
    #                 {
    #                     "id": "q4",
    #                     "text": "શુ ભોજન વિતરણ દરમ્યાન સ્વચ્છતા જાળવવામાં આવી?",
    #                     "options": ["ઉત્કૃષ્ટ", "સારી", "સારું છે પણ સુધારો જોઈએ", "ખરાબ"]
    #                 },
    #                 {
    #                     "id": "q5",
    #                     "text": "આજની નાસ્તાની સેવા તમે કેટલી પ્રમાણમાં રેટ કરો?",
    #                     "options": ["ઉત્કૃષ્ટ", "સારી", "સરેરાશ", "ખરાબ"]
    #                 }
    #             ]
    #         }
    #     else:  # English
    #         survey = {
    #             "surveyTitle": "Quick Food Service Survey",
    #             "description": "Please answer these quick questions about today's breakfast service.",
    #             "questions": [
    #                 {
    #                     "id": "q1",
    #                     "text": "Was the meal served to all students on time?",
    #                     "options": ["Yes, to all", "Yes, but late", "No", "Partial"]
    #                 },
    #                 {
    #                     "id": "q2",
    #                     "text": "How was the freshness of the food?",
    #                     "options": ["Very Fresh", "Fresh", "Okay", "Not Fresh"]
    #                 },
    #                 {
    #                     "id": "q3",
    #                     "text": "Was the food quantity sufficient for all students?",
    #                     "options": ["More than enough", "Just enough", "Less than required", "Not sufficient at all"]
    #                 },
    #                 {
    #                     "id": "q4",
    #                     "text": "Was hygiene maintained during food distribution?",
    #                     "options": ["Excellent hygiene", "Good hygiene", "Acceptable but needs improvement", "Poor hygiene"]
    #                 },
    #                 {
    #                     "id": "q5",
    #                     "text": "Overall, how would you rate the breakfast service today?",
    #                     "options": ["Excellent", "Good", "Average", "Poor"]
    #                 }
    #             ]
    #         }
    #
    #     return JsonResponse(survey, safe=False)

    def get(self, request, lang=None):
        lang = lang or request.query_params.get('lang', 'en')
        if lang not in ['en', 'gu']:
            return JsonResponse({'error': 'Invalid language'}, status=400)

        if lang == 'gu':
            survey = {
                "surveyTitle": "મધ્યાન ભોજન નનરીક્ષણ માટે પ્રશ્નાવલી",
                "description": "ભોજન સેવા પર નિરીક્ષણ માટે નીચે આપેલા પ્રશ્નોના જવાબ આપો.",
                "questions": [
                    {
                        "id": "q1",
                        "text": "🍽️ ભોજન અગાઉ નક્કી કરેલ મેન્યુ મુજબ આપવામાં આવ્યું હતું કે નહીં?",
                        "options": ["✅ હા, મેન્યુ મુજબ સંપૂર્ણ", "♻️ થોડી ફેરફાર સાથે", "⚠️ મોટા ફેરફાર સાથે",
                                    "❌ મેન્યુ મુજબ નહોતું"]
                    },
                    {
                        "id": "q2",
                        "text": "👨‍🍳 આપેલા ભોજનની ગુણવત્તા સંતોષકારક હતી કે નહીં?",
                        "options": ["🌟 ખૂબ સારી", "👍 સારી", "😐 સરેરાશ", "👎 નબળી"]
                    },
                    {
                        "id": "q3",
                        "text": "🍛 વિદ્યાર્થીઓ માટે ભોજનનું પ્રમાણ પૂરતું હતું કે નહીં?",
                        "options": ["✅ હા, બધાના માટે પૂરતું હતું", "⚠️ અંશતઃ પૂરતું હતું", "❗ થોડાક માટે ઓછું પડ્યું",
                                    "❌ બિલકુલ પૂરતું ન હતું"]
                    },
                    {
                        "id": "q4",
                        "text": "📊 કેટલાં ટકા વિદ્યાર્થીઓએ મોટાભાગનું ભોજન લીધું હતું?",
                        "options": ["💯 100%", "📉 75–80%", "📉 50–60%", "📉 20–30%"]
                    },
                    {
                        "id": "q5",
                        "text": "🙅‍♂️ આજે આપેલું ભોજન કોઈ વિદ્યાર્થીએ ખાવાનું નકાર્યું હતું?",
                        "options": ["😊 કોઈએ ન નકારી", "😐 ૧–૨ વિદ્યાર્થીઓ", "☹️ ૩–૫ વિદ્યાર્થીઓ",
                                    "😠 ૫ કરતાં વધુ વિદ્યાર્થીઓ"]
                    },
                    {
                        "id": "q6",
                        "text": "🧼 ભોજન વહેંચણી દરમિયાન કોઈ સફાઈ અથવા સ્વચ્છતાની સમસ્યા જોવા મળી હતી?",
                        "options": ["✅ ના", "⚠️ હળવી સમસ્યા", "🚫 ગંભીર સમસ્યા", "🙈 ધ્યાનમાં નથી"]
                    },
                    {
                        "id": "q7",
                        "text": "😊 ભોજન પછી વિદ્યાર્થીઓ સંતોષ અને આનંદિત લાગ્યા?",
                        "options": ["😄 બધા વિદ્યાર્થીઓ", "🙂 મોટા ભાગના વિદ્યાર્થીઓ", "😐 થોડાક વિદ્યાર્થીઓ", "😞 કોઈ નહિ"]
                    }
                ]

            }
        else:
            survey = {
                "surveyTitle": "Questionnaire for Mid-Day Meal Observation",
                "description": "Please answer the following questions for meal service monitoring.",
                "questions": [
                    {
                        "id": "q1",
                        "text": "🍽️ Was the meal served as per the pre-decided menu?",
                        "options": ["✅ Yes, exactly as per menu", "♻️ Minor changes", "⚠️ Major changes",
                                    "❌ Not at all as per menu"]
                    },
                    {
                        "id": "q2",
                        "text": "👨‍🍳 Was the quality of food served satisfactory?",
                        "options": ["🌟 Very good", "👍 Good", "😐 Average", "👎 Poor"]
                    },
                    {
                        "id": "q3",
                        "text": "🍛 Was the quantity of food sufficient for all students?",
                        "options": ["✅ Yes, sufficient for all", "⚠️ Partially sufficient", "❗ Insufficient for some",
                                    "❌ Not sufficient at all"]
                    },
                    {
                        "id": "q4",
                        "text": "📊 What percentage of students consumed the major portion of their meal?",
                        "options": ["💯 100%", "📉 75–80%", "📉 50–60%", "📉 20–30%"]
                    },
                    {
                        "id": "q5",
                        "text": "🙅‍♂️ Did any student refuse to eat the food served today?",
                        "options": ["😊 No student refused", "😐 1–2 students", "☹️ 3–5 students",
                                    "😠 More than 5 students"]
                    },
                    {
                        "id": "q6",
                        "text": "🧼 Were there any visible hygiene or cleanliness issues during food distribution?",
                        "options": ["✅ No issues", "⚠️ Minor concern", "🚫 Major concern", "🙈 Not Observed"]
                    },
                    {
                        "id": "q7",
                        "text": "😊 Did students appear happy and satisfied after the meal?",
                        "options": ["😄 All students", "🙂 Most students", "😐 Few students", "😞 None"]
                    }
                ]

            }

        return JsonResponse(survey, safe=False)


class UploadImage(APIView):
    permission_classes = [AllowAny]  # Optional: allows public

    parser_classes = (MultiPartParser, FormParser)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                name="lang",
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                description="Language code ('en' or 'gu')",
                required=True,
            ),
            openapi.Parameter(
                name="menu",
                in_=openapi.IN_FORM,
                type=openapi.TYPE_STRING,
                description="JSON list of menu items as string, e.g., [\"poha\", \"sev\"]",
                required=True,
            ),
            openapi.Parameter(
                name="image",
                in_=openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                description="Image file of the food plate",
                required=True,
            ),
        ]
    )

    @csrf_exempt
    def post(self, request):
        # if request.method != "POST":
        #     return JsonResponse({"error": "Only POST method allowed"}, status=405)
        #
        # lang = request.POST.get("lang")
        # if not lang:
        #     return JsonResponse({"error": "Missing 'lang' parameter"}, status=400)
        #
        # if lang not in ["en", "gu"]:
        #     return JsonResponse({"error": "Invalid language. Use 'en' or 'gu'"}, status=400)
        #
        # menu_items = request.POST.get("menu", "")
        # image_file = request.FILES.get("image")
        #
        # if not menu_items or not image_file:
        #     return JsonResponse({"error": "Missing menu or image"}, status=400)
        #
        # menu_list = [item.strip().lower() for item in menu_items.split(",") if item.strip()]

        if request.method != "POST":
            return JsonResponse({"error": "Only POST method allowed"}, status=405)

            # Get and validate language
        lang = request.POST.get("lang")
        if not lang:
            return JsonResponse({"error": "Missing 'lang' parameter"}, status=400)
        if lang not in ["en", "gu"]:
            return JsonResponse({"error": "Invalid language. Use 'en' or 'gu'"}, status=400)

        # Get image
        image_file = request.FILES.get("image")
        if not image_file:
            return JsonResponse({"error": "Missing 'image' parameter"}, status=400)

        # Parse menu (expecting a JSON string list in FormData)
        raw_menu = request.POST.get("menu", "[]")
        print("raw_menu", raw_menu)
        try:
            menu_items = json.loads(raw_menu)
            if not isinstance(menu_items, list) or not all(isinstance(item, str) for item in menu_items):
                raise ValueError
        except Exception:
            return JsonResponse({"error": "Invalid 'menu' format. Must be a JSON list of strings."}, status=400)

        # Normalize menu list
        menu_list = [item.strip().lower() for item in menu_items if item.strip()]

        if not menu_list:
            return JsonResponse({"error": "Menu list is empty or invalid"}, status=400)

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
                prompt_food = "આ છબીમાં તમે કયા ખોરાક વસ્તુઓ જોઈ શકો છો? ફક્ત યાદી આપો. તમામ માહિતી કૃપા કરીને ફક્ત ગુજરાતી ભાષામાં આપો."

                # prompt_food = "આ છબીમાં દૃશ્યમાન ખોરાક વસ્તુઓની સરળ, વિશિષ્ટ યાદી આપો. દરેક વસ્તુ અલગ પંક્તિમાં લખો. સમાન વસ્તુઓને એકસાથે જૂથ ન કરો. ફક્ત ખોરાકનાં નામ લખો — વિશેષણો કે વર્ણનો નહીં. તમામ માહિતી કૃપા કરીને ફક્ત ગુજરાતી ભાષામાં આપો."

                # prompt_nutrition = "આ છબીમાં તમને કયા ખાદ્ય પદાર્થો દેખાય છે? ઉપરાંત, દરેક વસ્તુ માટે, કેલરી, પ્રોટીન, ચરબી અને કાર્બોહાઇડ્રેટ્સ જેવી અંદાજિત પોષક માહિતી આપો. "
                prompt_nutrition = (
                    "આ છબીમાં તમને કયા ખાદ્ય પદાર્થો દેખાય છે? "
                    "દરેક ખોરાક વસ્તુ માટે પહેલે તેનું નામ લખો અને પછી તેની અંદાજિત પોષક માહિતી આપો — "
                    "જેમ કે કેલરી, પ્રોટીન, ચરબી અને કાર્બોહાઇડ્રેટ્સ. "
                    "દરેક ખોરાક વસ્તુને અલગ રીતે જણાવો. તમામ માહિતી કૃપા કરીને ફક્ત ગુજરાતી ભાષામાં આપો."
                )


            else:
                prompt_food = "What food items do you see in this image? Just list them. Please provide all information in the English language only."
                prompt_nutrition = "What food items do you see in this image? Also, for each item, provide its approximate nutritional information such as calories, protein, fat, and carbs. Please provide all information in the English language only."

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
            print("gpt_reply",gpt_reply)

            # def is_valid_line(line):
            #     line = line.strip()
            #     return line and not line.startswith("```") and not line.endswith("```")

            detected_items = [
                item.strip("- ").strip()
                for item in gpt_reply.split("\n")
                if item.strip()
            ]

            # def normalize(text):
            #     return re.sub(r"\s+", "", text.lower())

            # found_items = []
            # for item in menu_list:
            #     norm_item = normalize(item)
            #     matched = any(norm_item in normalize(detected) for detected in detected_items)
            #     if matched:
            #         found_items.append(item)

            def normalize(text):
                return re.sub(r"\s+", "", text.lower())

            found_items = []
            for item in menu_list:
                norm_item = normalize(item)
                for detected in detected_items:
                    norm_detected = normalize(detected)
                    if norm_item in norm_detected or norm_detected in norm_item:
                        found_items.append(item)
                        break

            missing_items = [item for item in menu_list if item not in found_items]

            # found_items = [
            #     item for item in menu_list
            #     if any(normalize(item) == normalize(d) for d in detected_items)
            # ]
            # missing_items = [item for item in menu_list if item not in found_items]

            gpt_reply_Nutrition = responseNutrition.choices[0].message.content.strip().lower()
            print(gpt_reply_Nutrition)

            nutritions = self.parse_nutrition_info(gpt_reply_Nutrition)
            # Retry if result is empty
            if not nutritions:
                nutritions = self.parse_nutrition_info(gpt_reply_Nutrition)


            # # Here Want to check for Nutrition if { }
            # # Case 1: Entire dict is empty
            # if not nutritions:
            #     print("Nutrition data is completely empty")
            #
            # # Case 2: All items have empty dictionaries
            # elif all(not value for value in nutritions.values()):
            #     print("All nutrition entries are empty")
            #     if current_item:
            #         nutrition_match = re.match(
            #             r"[-*]?\s*\*{0,2}([\w\u0A80-\u0AFF\s():]+)\*{0,2}\s*[:：]\s*(.+)", line)
            #         if nutrition_match:
            #             key = nutrition_match.group(1).strip().lower()
            #             value = nutrition_match.group(2).strip()
            #             nutritions[current_item][key] = value

            # nutritions = {}
            # current_item = None
            #
            # for line in gpt_reply_Nutrition.split("\n"):
            #     line = line.strip()
            #     if not line:
            #         continue
            #
            #     # Start of new item (e.g., "1. **potatoes**" or "**potatoes**")
            #     item_match = re.match(r"^(?:\d+\.\s*)?\*{2}(.+?)\*{2}$", line)
            #     if item_match:
            #         current_item = item_match.group(1).strip()
            #         nutritions[current_item] = {}
            #         continue
            #
            #     # Nutrition line for current item
            #     if current_item:
            #         nutrition_match = re.match(r"[-*]?\s*([a-zA-Z\u0A80-\u0AFF\s]+):\s*(.+)", line)
            #         if nutrition_match:
            #             key = nutrition_match.group(1).strip().lower()
            #             value = nutrition_match.group(2).strip()
            #             nutritions[current_item][key] = value

            # nutritions = {}
            # current_item = None
            #
            # for line in gpt_reply_Nutrition.split("\n"):
            #     line = line.strip()
            #     if not line:
            #         continue
            #
            #     item_match = re.match(r"^\d+\.\s+\*{0,2}(.+?)\*{0,2}$", line)
            #     if item_match:
            #         current_item = item_match.group(1).strip()
            #         nutritions[current_item] = {}
            #         continue
            #
            #     if current_item:
            #         nutrition_match = re.match(r"[-*]?\s*\*{0,2}([\w\s]+)\*{0,2}:\s*(.+)", line)
            #         if nutrition_match:
            #             key = nutrition_match.group(1).strip().lower()
            #             value = nutrition_match.group(2).strip()
            #             nutritions[current_item][key] = value

            return JsonResponse({
                "items_food": detected_items,
                "input_menu": menu_list,
                "found_items": found_items,
                "missing_items": missing_items,
                "nutritions": nutritions
            })

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    def parse_nutrition_info(self, gpt_reply_Nutrition: str) -> dict:
        nutritions = {}
        current_item = None

        for line in gpt_reply_Nutrition.split("\n"):
            line = line.strip()
            if not line:
                continue

            # Match item title: e.g., "1. **poha (flattened rice)**" or "**poha**"
            item_match = re.match(r"^(?:\d+\.\s*)?\*{2}(.+?)\*{2}", line)
            if item_match:
                current_item = item_match.group(1).strip()
                nutritions[current_item] = {}
                continue

            # Match nutrition info lines under the item
            if current_item:
                nutrition_match = re.match(
                    r"[-*]?\s*\*{0,2}([\w\u0A80-\u0AFF\s():]+)\*{0,2}\s*[:：]\s*(.+)", line)
                if nutrition_match:
                    key = nutrition_match.group(1).strip().lower()
                    value = nutrition_match.group(2).strip()
                    nutritions[current_item][key] = value

        return nutritions
