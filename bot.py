import os
import json
import requests
from io import BytesIO
from PIL import Image, ImageDraw

# 1. Secrets read karna
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
BUFFER_TOKEN = os.environ.get("BUFFER_ACCESS_TOKEN")
BUFFER_PROFILE_ID = os.environ.get("BUFFER_PROFILE_ID")

# 2. Account ke available models automatically find karna
models_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_KEY}"
models_res = requests.get(models_url).json()

supported_models = [
    m["name"] for m in models_res.get("models", [])
    if "generateContent" in m.get("supportedGenerationMethods", [])
]
print("Account Supported Models:", supported_models)

if not supported_models:
    raise Exception("No valid content generation models found for this API Key.")

# Flash model ko prioritize karna, warna pehla available model lena
chosen_model = next((m for m in supported_models if "flash" in m.lower()), supported_models[0])
print("Selected Model:", chosen_model)

# 3. Dynamic Model Call
gemini_url = f"https://generativelanguage.googleapis.com/v1beta/{chosen_model}:generateContent?key={GEMINI_KEY}"

prompt = """
Find 1 trending, verified news or buzz topic from India right now in Entertainment, Bollywood, Pop Culture, Memes, or Esports.
Write an engaging Instagram news post for 'Desi Culture'.

Strict requirements:
- Language: Engaging Hinglish / English mix.
- Tone: Crisp, exciting, professional youth-focused news.
- Output raw JSON ONLY with these exact keys:
  "category": "BOLLYWOOD or ESPORTS or POP CULTURE or TRENDING",
  "headline": "Punchy headline in 6-10 words",
  "bullet_points": "2 key facts summarizing the update",
  "caption": "Full Instagram caption with hook, brief details, discussion question, and 5-7 hashtags (#DesiCulture etc.)"
"""

headers = {"Content-Type": "application/json"}
payload = {
    "contents": [{"parts": [{"text": prompt}]}],
    "generationConfig": {"response_mime_type": "application/json"}
}

res = requests.post(gemini_url, headers=headers, json=payload)
print("Gemini Status Code:", res.status_code)
res_json = res.json()

if "candidates" not in res_json:
    print("API Error Response:", res_json)
    exit(1)

raw_text = res_json['candidates'][0]['content']['parts'][0]['text']

if "```json" in raw_text:
    raw_text = raw_text.split("```json")[1].split("```")[0].strip()
elif "```" in raw_text:
    raw_text = raw_text.split("```")[1].split("```")[0].strip()

news_data = json.loads(raw_text)
headline = news_data.get("headline", "Trending Desi News")
category = news_data.get("category", "DESI CULTURE")
caption = news_data.get("caption", "")

full_caption = f"🚨 {headline}\n\n{caption}"
print("\n--- GENERATED CAPTION ---\n", full_caption)

# 4. Instagram Graphic Generate Karna (1080x1080)
img = Image.new("RGB", (1080, 1080), color=(15, 17, 23))
draw = ImageDraw.Draw(img)

# Category Tag
draw.rectangle([(80, 100), (420, 160)], fill=(225, 29, 72))
draw.text((100, 115), category.upper(), fill=(255, 255, 255))

# Headline, Body & Watermark
draw.text((80, 240), headline, fill=(255, 255, 255))
draw.text((80, 420), news_data.get("bullet_points", ""), fill=(200, 205, 215))
draw.text((80, 960), "@thedesiculture.in", fill=(120, 125, 140))

# Save image in memory
img_bytes = BytesIO()
img.save(img_bytes, format='JPEG', quality=90)
img_bytes.seek(0)

# Temporary Free Public Image Hosting for Buffer Meta upload
img_url = ""
try:
    upload_res = requests.post(
        "https
