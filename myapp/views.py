import asyncio
import base64
import json
import os
import random
import re
import tempfile
from http import client

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from dotenv import load_dotenv
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from openai import OpenAI
from rapidfuzz import fuzz
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Teacher
from .serializers import TeacherSerializer

load_dotenv()  # Loads from .env
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class TeacherCreateAPIView(APIView):
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
                # prompt_food = "આ છબીમાં તમે કયા ખોરાક વસ્તુઓ જોઈ શકો છો? ફક્ત યાદી આપો. તમામ માહિતી કૃપા કરીને ફક્ત ગુજરાતી ભાષામાં આપો."
                prompt_food = "આ ચિત્રમાં દર્શાવાયેલ ખોરાકની ઓળખ કરો. દરેક ખોરાકનો સ્પષ્ટ ઉલ્લેખ કરો. ફક્ત યાદી આપો. તમામ માહિતી કૃપા કરીને ફક્ત ગુજરાતી ભાષામાં આપો."

                # prompt_food = "આ ચિત્રમાં દર્શાવાયેલ ખોરાકની ઓળખ કરો. દરેક ખોરાકનો સ્પષ્ટ ઉલ્લેખ કરો, જો શક્ય હોય તો આ વાનગીઓનું સામાન્ય વર્ગીકરણ પણ કરો (જેમ કે મુખ્ય ખોરાક, મીઠાઈ, સાઈડ ડિશ વગેરે). માત્ર ખોરાકના નામો અને વર્ણન આપો – વ્યક્તિ, પ્લેટ અથવા પૃષ્ઠભૂમિ વિશે કંઈ પણ ન લખો. તમામ માહિતી કૃપા કરીને ફક્ત ગુજરાતી ભાષામાં આપો. "

                # prompt_food = "આ છબીમાં દૃશ્યમાન ખોરાક વસ્તુઓની સરળ, વિશિષ્ટ યાદી આપો. દરેક વસ્તુ અલગ પંક્તિમાં લખો. સમાન વસ્તુઓને એકસાથે જૂથ ન કરો. ફક્ત ખોરાકનાં નામ લખો — વિશેષણો કે વર્ણનો નહીં. તમામ માહિતી કૃપા કરીને ફક્ત ગુજરાતી ભાષામાં આપો."

                # prompt_nutrition = "આ છબીમાં તમને કયા ખાદ્ય પદાર્થો દેખાય છે? ઉપરાંત, દરેક વસ્તુ માટે, કેલરી, પ્રોટીન, ચરબી અને કાર્બોહાઇડ્રેટ્સ જેવી અંદાજિત પોષક માહિતી આપો. "
                prompt_nutrition = (
                    "તમામ માહિતી કૃપા કરીને ફક્ત ગુજરાતી ભાષામાં આપો"
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

            detected_items = [
                item.strip("- ").strip()
                for item in gpt_reply.split("\n")
                if item.strip()
            ]

            def normalize(text):
                return re.sub(r"\s+", "", text.lower())

            found_items = []
            for item in menu_list:
                for detected in detected_items:
                    score = fuzz.partial_ratio(item, detected)
                    if score >= 85:
                        found_items.append(item)
                        break

            missing_items = [item for item in menu_list if item not in found_items]

            gpt_reply_Nutrition = responseNutrition.choices[0].message.content.strip().lower()
            print(gpt_reply_Nutrition)

            max_retries = 3
            nutritions = {}
            for attempt in range(max_retries):
                nutritions = self.parse_nutrition_info(gpt_reply_Nutrition)
                if nutritions:
                    break  # ✅ Success
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


@method_decorator(csrf_exempt, name="dispatch")
class FoodImageAPIView(View):
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

    async def post(self, request):
        # Validate method
        if request.method != "POST":
            return JsonResponse({"error": "Only POST method allowed"}, status=405)

        # Validate parameters
        lang = request.POST.get("lang")
        if lang not in ("en", "gu"):
            return JsonResponse({"error": "Invalid or missing 'lang' parameter"}, status=400)

        image_file = request.FILES.get("image")
        if not image_file:
            return JsonResponse({"error": "Missing 'image' parameter"}, status=400)

        raw_menu = request.POST.get("menu", "[]")
        try:
            menu_items = json.loads(raw_menu)
            if not isinstance(menu_items, list) or not all(isinstance(i, str) for i in menu_items):
                raise ValueError
        except Exception:
            return JsonResponse(
                {"error": "Invalid 'menu'. Must be JSON list of strings."},
                status=400
            )

        menu_list = [item.strip().lower() for item in menu_items if item.strip()]
        if not menu_list:
            return JsonResponse({"error": "Parsed menu list is empty"}, status=400)

        # Save uploaded image to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            for chunk in image_file.chunks():
                tmp.write(chunk)
            image_path = tmp.name

        try:
            with open(image_path, "rb") as f:
                # image_base64 = base64.b64encode(f.read()).decode()
                # Convert image to base64 (you can keep this sync)
                image_base64 = self._convert_image_to_base64(image_file)

            # Select prompts
            prompts = self._get_language_prompts(lang)
            system_prompt = "You are a food image detection expert. Identify all food items visible in the image."

            # system_prompt_gujarati = "You are a food image detection expert. Identify all food items visible in the image. Provide information only in Gujarati language."
            # system_prompt_english = "You are a food image detection expert. Identify all food items visible in the image. Provide information only in English language."

            # 🧠 Run GPT calls in parallel
            # if lang == "gu":
            #     system_prompt = system_prompt_gujarati
            # else:
            #     system_prompt = system_prompt_english

            food_task = asyncio.create_task(
                self._call_gpt_image(system_prompt, prompts["food"], image_base64, as_lines=True)
            )
            nutrition_task = asyncio.create_task(
                self._call_gpt_image(system_prompt, prompts["nutrition"], image_base64, max_tokens=300, as_lines=False)
            )

            def _looks_like_no_food_reply(items):
                if not items:
                    return True

                joined = " ".join(items).lower()
                joined = re.sub(r"[\"',.?!।]", "", joined)

                # Match by keywords or indicative phrases
                keyword_fragments = [
                    # Gujarati fragments
                    "માફ", "જાણ્યું નથી", "ઓળખી શકાતું નથી", "ખાદ્ય", "ખોરાક નથી", "ખાદ્ય પદાર્થ", "નથી ઓળખી", "દેખાતા નથી", "નથી પડતો", "સ્પષ્ટ નથી","કોઈ ખોરાક દેખાતો નથી"
                    # English fragments
                    "Sorry", "Not known", "Unrecognizable", "Food", "No food", "Food item", "Not recognized", "Not visible", "Not falling", "Not clear", "No food visible"
                ]

                return any(kw in joined for kw in keyword_fragments)

            detected_items, gpt_reply_nutrition = await asyncio.gather(food_task, nutrition_task)

            # 🧼 Clean detected items list
            clean_items = [
                item.strip("- ").strip()
                for item in detected_items
                if item.strip() and not item.strip().startswith("```")
            ]

            print("clean_items", clean_items)

            # ❌ Reject if no real food detected
            if _looks_like_no_food_reply(clean_items):
                if lang == "gu":
                    error_msg = "છબીમાં કોઈ ખોરાક વસ્તુ ઓળખી શકાયી નથી. કૃપા કરીને ખોરાક સમાવિષ્ટ નવી છબી અપલોડ કરો."
                else:
                    error_msg = "No food items detected in the image. Please upload a new image that clearly includes food items."

                return JsonResponse({"error": error_msg}, status=400)

            print("detected_items", detected_items)
            print("gpt_reply_nutrition", gpt_reply_nutrition)

            found_items, missing_items = self._match_menu(menu_list, detected_items)
            nutritions = self._retry_parse(gpt_reply_nutrition, max_retries=3)

            # ✅ If nutritions is still empty, recall OpenAI and try again
            if not nutritions:
                print("⚠️ Nutrition info was empty. Retrying GPT call...")
                gpt_reply_nutrition = await self._call_gpt_image(
                    system_prompt, prompts["nutrition"], image_base64, max_tokens=300, as_lines=False
                )
                nutritions = self._retry_parse(gpt_reply_nutrition, max_retries=3)

            # ❌ Still failed after retry
            if not nutritions:
                return JsonResponse({"error": "Nutrition info could not be extracted"}, status=422)

            return JsonResponse({
                "items_food": detected_items,
                "input_menu": menu_list,
                # "found_items": found_items,
                "missing_items": missing_items,
                "nutritions": nutritions
            })

        except Exception as err:
            return JsonResponse({"error": str(err)}, status=500)

    def _get_language_prompts(self, lang: str) -> dict:
        if lang == "gu":
            return {
                "food": (
                    "આ ચિત્રમાં દર્શાવાયેલ ખોરાકની ઓળખ કરો. દરેક ખોરાકનો સ્પષ્ટ ઉલ્લેખ કરો. "
                    "જો ચિત્રમાં રાંધેલા ચોખા હોય તો હંમેશા “ભાત” શબ્દ જ લખો — “ચોખા” શબ્દ નો ઉપયોગ ન કરો."
                    "દરેક ખોરાકની સામે પીરસેલી અંદાજિત માત્રા લખો, ગ્રામ અથવા મિલી એકમમાં, અથવા સંખ્યામાં જો તે વસ્તુ ટુકડાઓમાં હોય (જેમ કે “૨ રોટલી”). ફક્ત ચિત્રમાં દેખાતી વસ્તુઓ જ લખો, અંદાજથી નવી વસ્તુ ઉમેરશો નહીં. પરંતુ ક્રમાંક (૧, ૨, ૩...) નો ઉપયોગ ન કરો."
                    "ફક્ત યાદી આપો. માહિતી માત્ર ગુજરાતી ભાષામાં આપો."
                ),

                "nutrition": (
                    "તમામ માહિતી ફક્ત ગુજરાતી ભાષામાં અને સાફ JSON ફોર્મેટમાં આપો. "
                    "દરેક ખોરાક વસ્તુનું નામ (માત્રા સાથે જો દર્શાવેલ હોય) આપો અને પછી બે ફીલ્ડ આપો: "
                    "\"અંદાજિત કેલોરિ\" (જેમ ~230 કિલોકેલરી (1 કપ)) અને \"પ્રોટીન\" (જેમ ~12 ગ્રામ). "
                    "જો માત્રા બતાવેલ હોય (જેમ '2 રોટલી'), તો પોષણ તે સંપૂર્ણ માત્રા માટે આપો. "
                    "છેલ્લે 'કુલ (સર્વ કરેલી માત્રા માટે)' તરીકે કુલ પોષણ આપો. "
                    "આઉટપુટ ચોક્કસ રીતે નીચે મુજબ હોવો જોઈએ:\n"
                    "{\n"
                    "    \"ડાળ (1 કપ)\": {\n"
                    "        \"અંદાજિત કેલોરિ\": \"~230 કિલોકેલરી (1 કપ)\",\n"
                    "        \"પ્રોટીન\": \"~12 ગ્રામ\"\n"
                    "    },\n"
                    "    \"ભાત (1 કપ)\": {\n"
                    "        \"અંદાજિત કેલોરિ\": \"~200 કિલોકેલરી (1 કપ)\",\n"
                    "        \"પ્રોટીન\": \"~4 ગ્રામ\"\n"
                    "    },\n"
                    "    \"કોટ (1 કપ)\": {\n"
                    "        \"અંદાજિત કેલોરિ\": \"~150 કિલોકેલરી (1 કપ)\",\n"
                    "        \"પ્રોટીન\": \"~5 ગ્રામ\"\n"
                    "    },\n"
                    "    \"રોટલી (2)\": {\n"
                    "        \"અંદાજિત કેલોરિ\": \"~240 કિલોકેલરી (2 રોટલી)\",\n"
                    "        \"પ્રોટીન\": \"~6 ગ્રામ\"\n"
                    "    },\n"
                    "    \"કુલ (સર્વ કરેલી માત્રા માટે)\": {\n"
                    "        \"અંદાજિત કેલોરિ\": \"~820 કિલોકેલરી\",\n"
                    "        \"પ્રોટીન\": \"~27 ગ્રામ\"\n"
                    "    }\n"
                    "}"
                )

            }
        else:
            return {
                "food": ("Identify the food shown in this picture. Name each food clearly."
                         "If the picture shows cooked rice, always write the word rice — do not use the word cooked rice."
                         "Write the approximate serving size against each food, in grams or ml, or in numbers if the item is in pieces (such as “2 loaves”). Write only the items shown in the picture, do not add new items by estimation. But do not use ordinal numbers (1, 2, 3...)."
                         "Just give the list. Give the information only in English language."),
                "nutrition": ("Please provide all information in Gujarati language only"
"What food items do you see in this image? "
"For each food item, first write its name and then give its approximate nutritional information — "
                              "Such as calories, protein."
                              "Describe each food item separately. "
                              "Finally, provide a total row for all detected items in the format: "
                              "'Total (for serving size)': {'Estimated calories': '~XXX kilocalories', 'protein': '~YY grams'}."
                              "Please provide all information in English language only."
                              )
            }

    async def _call_gpt_image(self, system_prompt, user_text, img_base64, max_tokens=150, as_lines=True):
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_text},
                            {"type": "image_url", "image_url": {
                                "url": f"data:image/jpeg;base64,{img_base64}", "detail": "low"
                            }},
                        ],
                    },
                ],
                max_tokens=max_tokens,
                # temperature=1
            )
        )

        reply = response.choices[0].message.content.strip()
        print("reply", reply)
        if as_lines:
            return [
                ln.strip("- ").strip()
                for ln in reply.split("\n")
                if ln.strip() and not ln.strip().startswith("```")
            ]
        return reply

    def _match_menu(self, menu_list, detected_items, threshold=50):
        found, missing = [], []
        for item in menu_list:
            for detected in detected_items:
                if fuzz.partial_ratio(item, detected) >= threshold:
                    found.append(item)
                    break
        missing = [i for i in menu_list if i not in found]
        return found, missing

    def _retry_parse(self, nutrition_text, max_retries=3):
        print("Retrying to parse nutrition info...", nutrition_text)
        for attempt in range(max_retries):
            result = self.parse_nutrition_info(nutrition_text)
            if result:
                # total_nutrition = self.calculate_total_nutrition(result)
                # result["total_nutrition"] = total_nutrition
                return result
        return {}

    def parse_nutrition_info(self, text) -> dict:
        if isinstance(text, list):
            text = "\n".join(text)  # Convert list to string

        nutritions, current = {}, None
        for line in text.split("\n"):
            line = line.strip().rstrip(",")  # Remove trailing comma
            if not line:
                continue

            print("line++", line)

            # Match food item name (either JSON-style or bold)
            match_item = re.match(
                r'^(?:"|)?([\u0A80-\u0AFF\w\s()]+)(?:"|)[:：]?\s*\{$|^(?:\d+\.\s*)?\*{2}(.+?)\*{2}',
                line
            )
            if match_item:
                current = match_item.group(1) or match_item.group(2)
                current = current.strip()
                nutritions[current] = {}
                continue

            print("current++", current)
            if current:
                # Match JSON-style "key": "value"
                num = re.match(
                    r'^(?:"|)?([\u0A80-\u0AFF\w\s()]+)(?:"|)\s*[:：]\s*(?:"|)?([^"]+)(?:"|)?$',
                    line
                )
                if num:
                    key = num.group(1).strip()
                    value = num.group(2).strip()
                    # If it's the total row, move it outside
                    if "કુલ" in key:
                        nutritions[key] = value
                    else:
                        nutritions[current][key] = value

        print("nutritions ++++++", nutritions)
        return nutritions

    def _convert_image_to_base64(self, image_file):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_img:
            for chunk in image_file.chunks():
                temp_img.write(chunk)
            path = temp_img.name

        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()

    def calculate_total_nutrition(self, nutritions: dict) -> dict:
        total_calories = 0
        total_protein = 0

        for item, values in nutritions.items():
            kcal_text = values.get("કૅલરી", "")
            protein_text = values.get("પ્રોટીન", "")

            # Extract average calorie from range or single number
            kcal_nums = re.findall(r"(\d+)", kcal_text)
            if kcal_nums:
                kcal_nums = list(map(int, kcal_nums))
                avg_kcal = sum(kcal_nums) / len(kcal_nums)
                total_calories += avg_kcal

            # Extract average protein from range or single number
            protein_nums = re.findall(r"(\d+)", protein_text)
            if protein_nums:
                protein_nums = list(map(int, protein_nums))
                avg_protein = sum(protein_nums) / len(protein_nums)
                total_protein += avg_protein

        return {
            "total_kcal": round(total_calories, 2),
            "total_protein_g": round(total_protein, 2)
        }


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class FoodDetectImageAPIView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            # Get uploaded image
            image_file = request.FILES.get("image")
            menu_items = request.data.get("menu")  # Expecting JSON string list: '["sev", "poha"]'
            lang = request.data.get("lang", "gu")  # default Gujarati

            if not image_file or not menu_items or not lang:
                return Response({"error": "Image, menu_items and lang are required"}, status=status.HTTP_400_BAD_REQUEST)

            import json
            try:
                menu_items = json.loads(menu_items)
            except Exception as e:
                return Response({"error": f"Invalid menu_items format: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

            # Convert image to base64
            image_bytes = image_file.read()
            image_base64 = base64.b64encode(image_bytes).decode("utf-8")

            # # Build prompt for OpenAI
            # prompt = f"""
            # You are a food detection assistant.
            # Given the image of a dish and this menu list: {menu_items},
            # identify which items are present in the dish and which are missing.
            # Respond in strict JSON with keys 'detected' and 'not_detected'.
            # """

            # prompt = f"""
            # You are a food detection assistant.
            #
            # Step 1: Look at the image and identify foods. Match them against this menu list (may contain Gujarati or English): {menu_items}.
            #
            # Step 2: Once matches are found, always output the response in JSON format with two keys: "items_food" and "missing_items".
            #
            # Step 3: IMPORTANT: The final output must be written in {"Gujarati" if lang == "GU" else "English"} only.
            # If a menu item was given in another language, translate it to the target language before returning.
            #
            # Example if lang=GU:
            # {{
            #   "items_food": ["પોહા", "સેવ"],
            #   "missing_items": ["રોટલી"]
            # }}
            #
            # Example if lang=EN:
            # {{
            #   "items_food": ["poha", "sev"],
            #   "missing_items": ["roti"]
            # }}
            #
            # Output strict JSON only, no text or markdown.
            # """

            # prompt = f"""
            # You are a food nutrition assistant.
            #
            # Given an image of a dish and this menu list (Gujarati or English): {menu_items},
            #
            # Tasks:
            # 1. Detect which items from the menu are present in the dish.
            # 2. For each detected item, provide approximate nutrition info: calories (કિલોકેલરી) and protein (ગ્રામ).
            # 3. Calculate a "total nutrition" (sum of calories & protein from detected items).
            # 4. Respond ONLY in JSON with keys:
            #    - "detected": list of detected items
            #    - "not_detected": list of missing items
            #    - "nutritions": dictionary with nutrition info for detected items and a "total nutrition" entry.
            #
            # Important:
            # - The response language must be {"Gujarati" if lang == "GU" else "English"}.
            # - Do not include nutrition info for items that are not detected.
            # - Respond in strict JSON, no markdown or explanations.
            #
            # Example (Gujarati):
            # {{
            #   "detected": ["પોહા", "સેવ"],
            #   "not_detected": ["રોટલી"],
            #   "nutritions": {{
            #       "પોહા": {{
            #           "અંદાજિત કેલરી": "130 કિલોકેલરી (1 કપ)",
            #           "પ્રોટીન": "2.5 ગ્રામ"
            #       }},
            #       "સેવ": {{
            #           "અંદાજિત કેલરી": "200 કિલોકેલરી (30 ગ્રામ)",
            #           "પ્રોટીન": "4 ગ્રામ"
            #       }},
            #       "કુલ પોષણ": {{
            #           "અંદાજિત કેલરી": "330 કિલોકેલરી",
            #           "પ્રોટીન": "6.5 ગ્રામ"
            #       }}
            #   }}
            # }}
            #
            # Example (English):
            # {{
            #   "detected": ["poha", "sev"],
            #   "not_detected": ["roti"],
            #   "nutritions": {{
            #       "poha": {{
            #           "Estimated Calories": "130 kcal (1 cup)",
            #           "Protein": "2.5 g"
            #       }},
            #       "sev": {{
            #           "Estimated Calories": "200 kcal (30 g)",
            #           "Protein": "4 g"
            #       }},
            #       "Total Nutrition": {{
            #           "Estimated Calories": "330 kcal",
            #           "Protein": "6.5 g"
            #       }}
            #   }}
            # }}
            # """

            # prompt = f"""
            # You are a food nutrition assistant.
            #
            # Given an image of a dish and this menu list (Gujarati or English): {menu_items},
            #
            # Tasks:
            # 1. Detect which items from the menu are present in the dish.
            # 2. For each detected item:
            #    - If the item is **countable** (like રોટલી, roti, puri, samosa, chapati), count how many pieces are present in the dish.
            #    - Multiply nutrition values by the count.
            #    - For non-countable foods (like rice, dal, sabzi, poha), give nutrition for standard portion only.
            # 3. Provide approximate nutrition info for each detected item: Calories and Protein.
            # 4. Calculate a "Total Nutrition" entry (sum of all calories & protein).
            # 5. Respond ONLY in JSON with:
            #    - "detected": list of detected items (include count in the name, e.g., "રોટલી (2)")
            #    - "not_detected": list of missing items
            #    - "nutritions": dictionary with nutrition info for detected items and a "total nutrition" entry.
            #
            # Response must be in {"Gujarati" if lang == "GU" else "English"} only.
            # Strict JSON, no markdown or extra text.
            #
            # Example Gujarati:
            # {{
            #   "detected": ["રોટલી (2)", "શાક"],
            #   "not_detected": ["દાળ"],
            #   "nutritions": {{
            #     "રોટલી (2)": {{
            #       "અંદાજિત કેલરી": "142 કિલોકેલરી (2 રોટલી)",
            #       "પ્રોટીન": "6 ગ્રામ"
            #     }},
            #     "શાક": {{
            #       "અંદાજિત કેલરી": "120 કિલોકેલરી",
            #       "પ્રોટીન": "2 ગ્રામ"
            #     }},
            #     "કુલ પોષણ": {{
            #       "અંદાજિત કેલરી": "262 કિલોકેલરી",
            #       "પ્રોટીન": "8 ગ્રામ"
            #     }}
            #   }}
            # }}
            #
            # Example English:
            # {{
            #   "detected": ["roti (2)", "sabzi"],
            #   "not_detected": ["dal"],
            #   "nutritions": {{
            #     "roti (2)": {{
            #       "Estimated Calories": "142 kcal (2 roti)",
            #       "Protein": "6 g"
            #     }},
            #     "sabzi": {{
            #       "Estimated Calories": "120 kcal",
            #       "Protein": "2 g"
            #     }},
            #     "Total Nutrition": {{
            #       "Estimated Calories": "262 kcal",
            #       "Protein": "8 g"
            #     }}
            #   }}
            # }}
            # """

            # prompt = f"""
            # You are a food nutrition assistant.
            #
            # Given an image of a dish and this menu list (Gujarati or English): {menu_items},
            #
            # Tasks:
            # 1. Detect which items from the menu are present in the dish.
            # 2. For each detected item:
            #    - If the item is **countable** (like રોટલી, roti, puri, samosa, chapati):
            #        * Count ONLY clearly visible, separate pieces.
            #        * Do NOT assume hidden or stacked pieces unless fully visible.
            #        * Example: if 2 rotis are visible (even if folded), report "રોટલી (2)".
            #    - Multiply nutrition values by the count.
            #    - For non-countable foods (like rice, dal, sabzi, poha), give nutrition for 1 standard portion only.
            # 3. Provide approximate nutrition info for each detected item: Calories and Protein.
            # 4. Calculate a "Total Nutrition" entry (sum of all calories & protein).
            # 5. Respond ONLY in JSON with:
            #    - "detected": list of detected items (include count in the name, e.g., "રોટલી (2)")
            #    - "not_detected": list of missing items
            #    - "nutritions": dictionary with nutrition info for detected items and a "total nutrition" entry.
            #
            # Response must be in {"Gujarati" if lang == "GU" else "English"} only.
            # Strict JSON, no markdown or extra text.
            #
            # Important:
            # - Do not guess hidden pieces.
            # - If unsure between 2 or 3 pieces, always choose the lower visible number.
            # - Folded or half-visible roti = still counts as 1, not 2.
            #
            # Example Gujarati:
            # {{
            #   "detected": ["રોટલી (2)", "શાક"],
            #   "not_detected": ["દાળ"],
            #   "nutritions": {{
            #     "રોટલી (2)": {{
            #       "અંદાજિત કેલરી": "242 કિલોકેલરી (2 રોટલી)",
            #       "પ્રોટીન": "6 ગ્રામ"
            #     }},
            #     "શાક": {{
            #       "અંદાજિત કેલરી": "120 કિલોકેલરી",
            #       "પ્રોટીન": "2 ગ્રામ"
            #     }},
            #     "કુલ પોષણ": {{
            #       "અંદાજિત કેલરી": "362 કિલોકેલરી",
            #       "પ્રોટીન": "8 ગ્રામ"
            #     }}
            #   }}
            # }}
            #
            # Example English:
            # {{
            #   "detected": ["roti (2)", "sabzi"],
            #   "not_detected": ["dal"],
            #   "nutritions": {{
            #     "roti (2)": {{
            #       "Estimated Calories": "242 kcal (2 roti)",
            #       "Protein": "6 g"
            #     }},
            #     "sabzi": {{
            #       "Estimated Calories": "120 kcal",
            #       "Protein": "2 g"
            #     }},
            #     "Total Nutrition": {{
            #       "Estimated Calories": "362 kcal",
            #       "Protein": "8 g"
            #     }}
            #   }}
            # }}
            # """

            # prompt = f"""
            # You are a food nutrition assistant.
            #
            # Given an image of a dish and this menu list (Gujarati or English): {menu_items},
            #
            # Tasks:
            # 1. Detect which items from the menu are present in the dish.
            # 2. For each detected item:
            #    - If the item is **countable** (like રોટલી, roti, puri, samosa, chapati):
            #        * Count ONLY clearly visible, separate pieces.
            #        * Do NOT assume hidden or stacked pieces unless fully visible.
            #        * Example: if 2 rotis are visible (even if folded), report "રોટલી (2)".
            #        * Also estimate grams = count × avg grams per piece (e.g., roti ≈ 40g).
            #    - Multiply nutrition values by the count.
            #    - For non-countable foods (like rice, dal, sabzi, poha):
            #        * Give nutrition for 1 standard portion only.
            #        * Also include estimated grams (e.g., rice ≈ 100g, dal ≈ 120g, sabzi ≈ 120g).
            # 3. Provide approximate nutrition info for each detected item: Calories, Protein, and Grams.
            # 4. Calculate a "Total Nutrition" entry (sum of all calories & protein, and sum of grams).
            # 5. Respond ONLY in JSON with:
            #    - "items_food": list of detected items (include count in the name, e.g., "રોટલી (2)")
            #    - "missing_items": list of missing items
            #    - "nutritions": dictionary with nutrition info for detected items and a "total nutrition" entry.
            #
            # Response must be in {"Gujarati" if lang == "GU" else "English"} only.
            # Strict JSON, no markdown or extra text.
            #
            # Important:
            # - Do not guess hidden pieces.
            # - If unsure between 2 or 3 pieces, always choose the lower visible number.
            # - Folded or half-visible roti = still counts as 1, not 2.
            #
            # Example Gujarati:
            # {{
            #   "items_food": ["રોટલી (2)", "શાક"],
            #   "missing_items": ["દાળ"],
            #   "nutritions": {{
            #     "રોટલી (2)": {{
            #       "અંદાજિત કેલરી": "242 કિલોકેલરી",
            #       "પ્રોટીન": "6 ગ્રામ",
            #       "ગ્રામ": "80 ગ્રામ"
            #     }},
            #     "શાક": {{
            #       "અંદાજિત કેલરી": "120 કિલોકેલરી",
            #       "પ્રોટીન": "2 ગ્રામ",
            #       "ગ્રામ": "120 ગ્રામ"
            #     }},
            #     "કુલ પોષણ": {{
            #       "અંદાજિત કેલરી": "362 કિલોકેલરી",
            #       "પ્રોટીન": "8 ગ્રામ",
            #       "ગ્રામ": "200 ગ્રામ"
            #     }}
            #   }}
            # }}
            #
            # Example English:
            # {{
            #   "items_food": ["roti (2)", "sabzi"],
            #   "missing_items": ["dal"],
            #   "nutritions": {{
            #     "roti (2)": {{
            #       "Estimated Calories": "242 kcal",
            #       "Protein": "6 g",
            #       "Grams": "80 g"
            #     }},
            #     "sabzi": {{
            #       "Estimated Calories": "120 kcal",
            #       "Protein": "2 g",
            #       "Grams": "120 g"
            #     }},
            #     "Total Nutrition": {{
            #       "Estimated Calories": "362 kcal",
            #       "Protein": "8 g",
            #       "Grams": "200 g"
            #     }}
            #   }}
            # }}
            # """

            # prompt = f"""
            #             You are a food nutrition assistant.
            #
            #             Given an image of a dish and this menu list (Gujarati or English): {menu_items},
            #
            #             Tasks:
            #             1. Detect which items from the menu are present in the dish.
            #             2. For each detected item:
            #                - If the item is **countable** (like રોટલી, roti, puri, samosa, chapati):
            #                    * Count ONLY clearly visible, separate pieces.
            #                    * Do NOT assume hidden or stacked pieces unless fully visible.
            #                    * Example: if 2 rotis are visible (even if folded), report "રોટલી (2)".
            #                    * Also estimate grams = count × avg grams per piece (e.g., roti ≈ 40g).
            #                - Multiply nutrition values by the count.
            #                - For non-countable foods (like rice, dal, sabzi, poha):
            #                    * Give nutrition for 1 standard portion only.
            #                    * Also include estimated grams (e.g., rice ≈ 100g, dal ≈ 120g, sabzi ≈ 120g).
            #             3. Provide approximate nutrition info for each detected item: Calories, Protein, and Grams.
            #             4. Calculate a "Total Nutrition" entry (sum of all calories & protein, and sum of grams).
            #             5. Respond ONLY in JSON with:
            #                - "items_food": list of detected items (include count in the name, e.g., "રોટલી (2)")
            #                - "missing_items": list of missing items
            #                - "nutritions": dictionary with nutrition info for detected items and a "total nutrition" entry.
            #
            #             Response must be in {"Gujarati" if lang == "GU" else "English"} only.
            #             Strict JSON, no markdown or extra text.
            #
            #             Important:
            #             - Do not guess hidden pieces.
            #             - If unsure between 2 or 3 pieces, always choose the lower visible number.
            #             - Folded or half-visible roti = still counts as 1, not 2.
            #             🔹 - Only mark a menu item as detected if the visible food matches that exact item or its explicit synonym.
            #             🔹 - Do NOT substitute a different sabzi (e.g., bhindi for "મગ શાક"). If a different sabzi is visible but not in the menu, leave the menu item in "missing_items".
            #             🔹 - If a food is clearly visible but not in the menu, add it under an optional field `"extras_found"` without affecting detection.
            #             🔹 - Always detect food items even if they appear in Gujarati, English, or mixed forms.
            #                  Use this synonym mapping for detection and normalization:
            #                  • ડુંગળી, કાંદો → Onion
            #                  • બટાકા, આલુ → Potato
            #                  • રોટલી, ચપાટી → Roti
            #                  • ભાત, ચોખા → Rice
            #             🔹 - If you find a synonym, normalize it to the menu’s wording (Gujarati if `lang=="GU"`, English if `lang=="EN"`).
            #
            #             Example Gujarati:
            #             {{
            #               "items_food": ["રોટલી (2)", "શાક"],
            #               "missing_items": ["દાળ"],
            #               "nutritions": {{
            #                 "રોટલી (2)": {{
            #                   "અંદાજિત કેલરી": "242 કિલોકેલરી",
            #                   "પ્રોટીન": "6 ગ્રામ",
            #                   "ગ્રામ": "80 ગ્રામ"
            #                 }},
            #                 "શાક": {{
            #                   "અંદાજિત કેલરી": "120 કિલોકેલરી",
            #                   "પ્રોટીન": "2 ગ્રામ",
            #                   "ગ્રામ": "120 ગ્રામ"
            #                 }},
            #                 "કુલ પોષણ": {{
            #                   "અંદાજિત કેલરી": "362 કિલોકેલરી",
            #                   "પ્રોટીન": "8 ગ્રામ",
            #                   "ગ્રામ": "200 ગ્રામ"
            #                 }}
            #               }}
            #             }}
            #
            #             Example English:
            #             {{
            #               "items_food": ["roti (2)", "sabzi"],
            #               "missing_items": ["dal"],
            #               "nutritions": {{
            #                 "roti (2)": {{
            #                   "Estimated Calories": "242 kcal",
            #                   "Protein": "6 g",
            #                   "Grams": "80 g"
            #                 }},
            #                 "sabzi": {{
            #                   "Estimated Calories": "120 kcal",
            #                   "Protein": "2 g",
            #                   "Grams": "120 g"
            #                 }},
            #                 "Total Nutrition": {{
            #                   "Estimated Calories": "362 kcal",
            #                   "Protein": "8 g",
            #                   "Grams": "200 g"
            #                 }}
            #               }}
            #             }}
            #             """

            # prompt = f"""
            #                         You are a food nutrition assistant.
            #
            #                         Given an image of a dish and this menu list (Gujarati or English): {menu_items},
            #
            #                         Tasks:
            #                         1. Detect which items from the menu are present in the dish.
            #                         2. For each detected item:
            #                            - If the item is **countable** (like રોટલી, roti, ભાખરી, puri, samosa, chapati):
            #                                * Count ONLY clearly visible, separate pieces.
            #                                * Do NOT assume hidden or stacked pieces unless fully visible.
            #                                * Example: if 2 rotis or 1 bhakhri are visible, report "રોટલી (2)" or "ભાખરી (1)".
            #                                * Also estimate grams = count × avg grams per piece (e.g., roti ≈ 40g, bhakhri ≈ 50g).
            #                            - Multiply nutrition values by the count.
            #                            - For non-countable foods (like rice, dal, sabzi, poha):
            #                                * Give nutrition for 1 standard portion only.
            #                                * Also include estimated grams (e.g., rice ≈ 100g, dal ≈ 120g, sabzi ≈ 120g).
            #                         3. Provide approximate nutrition info for each detected item: Calories, Protein, and Grams.
            #                         4. Calculate a "Total Nutrition" entry (sum of all calories & protein, and sum of grams).
            #                         5. Respond ONLY in JSON with:
            #                            - "items_food": list of detected items (include count in the name, e.g., "રોટલી (2)")
            #                            - "missing_items": list of missing items
            #                            - "nutritions": dictionary with nutrition info for detected items and a "total nutrition" entry.
            #
            #                         Response must be in {"Gujarati" if lang == "gu" else "English"} only.
            #                         Strict JSON, no markdown or extra text.
            #
            #                         Important:
            #                         - Do not guess hidden pieces.
            #                         - If unsure between 2 or 3 pieces, always choose the lower visible number.
            #                         - Folded or half-visible roti = still counts as 1, not 2.
            #                         🔹 - Only mark a menu item as detected if the visible food matches that exact item or its explicit synonym.
            #                         🔹 - Do NOT substitute a different sabzi (e.g., bhindi for "મગ શાક"). If a different sabzi is visible but not in the menu, leave the menu item in "missing_items".
            #                         🔹 - If a food is clearly visible but not in the menu, add it under an optional field `"extras_found"` without affecting detection.
            #                         🔹 - Always detect food items even if they appear in Gujarati, English, or mixed forms.
            #                              Use this synonym mapping for detection and normalization:
            #                              • ડુંગળી, કાંદો → Onion
            #                              • બટાકા, આલુ → Potato
            #                              • રોટલી, ચપાટી → Roti
            #                              • ભાખરી → Bhakhri
            #                              • ભાત, ચોખા → Rice
            #                              • ભુંગળા, કલરફુલ ભુંગળા → Bhungala
            #                         🔹 - If you find a synonym, normalize it to the menu’s wording (Gujarati if `lang=="gu"`, English if `lang=="en"`).
            #
            #                         Example Gujarati:
            #                         {{
            #                           "items_food": ["રોટલી (2)", "શાક"],
            #                           "missing_items": ["દાળ"],
            #                           "nutritions": {{
            #                             "રોટલી (2)": {{
            #                               "અંદાજિત કેલરી": "242 કિલોકેલરી",
            #                               "પ્રોટીન": "6 ગ્રામ",
            #                               "ગ્રામ": "80 ગ્રામ"
            #                             }},
            #                             "શાક": {{
            #                               "અંદાજિત કેલરી": "120 કિલોકેલરી",
            #                               "પ્રોટીન": "2 ગ્રામ",
            #                               "ગ્રામ": "120 ગ્રામ"
            #                             }},
            #                             "કુલ પોષણ": {{
            #                               "અંદાજિત કેલરી": "362 કિલોકેલરી",
            #                               "પ્રોટીન": "8 ગ્રામ",
            #                               "ગ્રામ": "200 ગ્રામ"
            #                             }}
            #                           }}
            #                         }}
            #
            #                         Example English:
            #                         {{
            #                           "items_food": ["roti (2)", "sabzi"],
            #                           "missing_items": ["dal"],
            #                           "nutritions": {{
            #                             "roti (2)": {{
            #                               "Estimated Calories": "242 kcal",
            #                               "Protein": "6 g",
            #                               "Grams": "80 g"
            #                             }},
            #                             "sabzi": {{
            #                               "Estimated Calories": "120 kcal",
            #                               "Protein": "2 g",
            #                               "Grams": "120 g"
            #                             }},
            #                             "Total Nutrition": {{
            #                               "Estimated Calories": "362 kcal",
            #                               "Protein": "8 g",
            #                               "Grams": "200 g"
            #                             }}
            #                           }}
            #                         }}
            #                         """

            prompt = f"""
            You are a food nutrition assistant.

            Given an image of a dish and this menu list (Gujarati or English): {menu_items},

            ### Tasks

            Step 1: Detection (STRICT)
            1. For each item in the given menu list:
               - If the item is clearly visible in the image → add it to "items_food".
               - If the item is not clearly visible → add it to "missing_items".
               - You MUST NOT add a menu item to "items_food" unless it is visible in the image.
               - Do not assume, infer, or guess based on typical thali items.
               - If unsure, always put it in "missing_items".

            Step 2: Extras
            2. If any foods are visible in the image but not in the menu list, add them under "extras_found".

            Step 3: Nutrition
            3. For each item in "items_food":
               - If it is countable (રોટલી, ભાખરી, puri, chapati, samosa):
                    * Count ONLY fully visible, separate, round pieces.
                    * Folded, half-visible, or torn roti still counts as ONE piece only.
                    * If 2 rotis are stacked but only one edge is visible, count as 1 (not 2).
                    * Always choose the lowest visible count.
                    * Estimate grams = count × avg grams (roti≈40g, bhakhri≈50g).
               - If it is non-countable (rice, dal, sabzi, poha):
                   * Report as one standard portion with estimated grams
                     (rice≈100g, dal≈120g, sabzi≈120g).
            4. Provide nutrition for each detected item:
               - Calories (kcal)
               - Protein (g)
               - Fat (g)
               - Carbohydrates (g)
               - Fiber (g)               
               - Calcium (%DV)               
               - Scale nutrition based on count for countable items or portion grams for non-countable items.

            5. Add a "Total Nutrition" entry summing all detected items.

            ### Important Rules
            - STRICT: Never add a menu item to "items_food" if it is not visible.  
            - If unsure, always put it in "missing_items".  
            - Do not auto-complete the list to include all menu items.  
            - Output must remain faithful to the image.  
            - If any menu item is placed in "items_food" but not visible in the image, the answer is INVALID.

            ### Synonym Normalization
            - ડુંગળી, કાંદો → Onion  
            - બટાકા, આલુ → Potato  
            - રોટલી, ચપાટી → Roti  
            - ભાખરી → Bhakhri  
            - ભાત, ચોખા → Rice  
            - ભુંગળા → Bhungala  

            ### Response Format
            Respond ONLY in strict JSON:
            - "items_food": detected menu items
            - "missing_items": menu items not visible
            - "extras_found": visible foods not in menu list
            - "nutritions": nutrition info per item + "Total Nutrition"

            ### Output Language
            Respond in {"Gujarati" if lang == "gu" else "English"} only.

            ### Example Gujarati:
            {{
              "items_food": ["રોટલી (2)", "શાક"],
              "missing_items": ["દાળ"],
              "extras_found": ["પાપડ", "દહીં"],
              "nutritions": {{
                "રોટલી (2)": {{
                  "અંદાજિત કેલરી": "242 કિલોકેલરી",
                  "પ્રોટીન": "6 ગ્રામ",
                  "ગ્રામ": "80 ગ્રામ"
                }},
                "શાક": {{
                  "અંદાજિત કેલરી": "120 કિલોકેલરી",
                  "પ્રોટીન": "2 ગ્રામ",
                  "ગ્રામ": "120 ગ્રામ"
                }},
                "કુલ પોષણ": {{
                  "અંદાજિત કેલરી": "362 કિલોકેલરી",
                  "પ્રોટીન": "8 ગ્રામ",
                  "ગ્રામ": "200 ગ્રામ"
                }}
              }}
            }}

            ### Example English:
            {{
              "items_food": ["roti (2)", "sabzi"],
              "missing_items": ["dal"],
              "extras_found": ["papad", "curd"],
              "nutritions": {{
                "roti (2)": {{
                  "Estimated Calories": "242 kcal",
                  "Protein": "6 g",
                  "Grams": "80 g"
                }},
                "sabzi": {{
                  "Estimated Calories": "120 kcal",
                  "Protein": "2 g",
                  "Grams": "120 g"
                }},
                "Total Nutrition": {{
                  "Estimated Calories": "362 kcal",
                  "Protein": "8 g",
                  "Grams": "200 g"
                }}
              }}
            }}
            """

            response = client.chat.completions.create(
                model="chatgpt-4o-latest",  # vision-capable model
                messages=[
                    {"role": "system", "content": "You are a helpful food recognition assistant."},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                temperature=0
            )

            # Parse response text
            result_text = response.choices[0].message.content.strip()

            # Clean markdown fences if present
            if result_text.startswith("```"):
                result_text = result_text.strip("`")  # remove ```
                if result_text.startswith("json"):
                    result_text = result_text[len("json"):].strip()

            import json
            try:
                result_json = json.loads(result_text)
            except Exception:
                result_json = {
                    "items_food": [],
                    "missing_items": [],
                    "nutritions":[],
                    "raw_response": result_text  # fallback
                }

            return Response(result_json, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)