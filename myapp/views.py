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

            # 🧠 Run GPT calls in parallel
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
                    "no food", "sorry", "not detect", "could not see", "unable to identify"
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
                # "nutrition": (
                #     "આ છબીમાં દેખાતા દરેક ખોરાક માટે તેનું નામ અને અંદાજિત પોષક માહિતી આપો "
                #     "(જેમ કે કેલરી, પ્રોટીન, ચરબી, કાર્બોહાઇડ્રેટ્સ). ફક્ત ગુજરાતી ભાષામાં."
                # ),
                "nutrition": ( "તમામ માહિતી કૃપા કરીને ફક્ત ગુજરાતી ભાષામાં આપો"
                    "આ છબીમાં તમને કયા ખાદ્ય પદાર્થો દેખાય છે? "
                    "દરેક ખોરાક વસ્તુ માટે પહેલે તેનું નામ લખો અને પછી તેની અંદાજિત પોષક માહિતી આપો — "
                    "જેમ કે કેલરી, પ્રોટીન."
                    "દરેક ખોરાક વસ્તુને અલગ રીતે જણાવો. "
                    "Finally, provide a total row for all detected items in the format: "
                    "'કુલ (સર્વ કરેલી માત્રા માટે)': {'અંદાજિત કેલરી': '~XXX કિલોકેલરી', 'પ્રોટીન': '~YY ગ્રામ'}."
                    "તમામ માહિતી કૃપા કરીને ફક્ત ગુજરાતી ભાષામાં આપો."),
            }
        else:
            return {
                "food": "What food items do you see in this image? Just list them in English.",
                "nutrition": "For each food item visible, give approximate nutrition (calories, protein, fat, carbs) in English."
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
            line = line.strip()
            if not line:
                continue
            match_item = re.match(r"^(?:\d+\.\s*)?\*{2}(.+?)\*{2}", line)
            if match_item:
                current = match_item.group(1).strip()
                nutritions[current] = {}
                continue
            if current:
                num = re.match(r"[-*]?\s*\*{0,2}([\w\u0A80-\u0AFF\s():]+)\*{0,2}\s*[:：]\s*(.+)", line)
                if num:
                    nutritions[current][num.group(1).strip().lower()] = num.group(2).strip()
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


