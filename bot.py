import os
import json
import textwrap
import requests
from io import BytesIO
from PIL import Image, ImageDraw

# 1. Credentials
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
BUFFER_TOKEN = os.environ.get("BUFFER_ACCESS_TOKEN")
BUFFER_PROFILE_ID = os.environ.get("BUFFER_PROFILE_ID")

# 2. Model Detection
models_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_KEY}"
models_res = requests.get(models_url).json()

supported = [
    m["name"] for m in models_res.get("models", [])
    if "generateContent" in m.get("supportedGenerationMethods", [])
]
chosen = next((m for m in supported if "flash" in m.lower()), supported[0])
model_endpoint = chosen.replace("models/", "")
print(f"Using Model: {model_endpoint}")

# 3. Global Multi-Category News & Meme Prompt
prompt = """
You are a senior social editor for 'Desi Culture' covering both GLOBAL and INDIAN youth culture.
Find 1 trending buzz topic right now from across the WORLD or INDIA in one of these categories:
- MOVIES / HOLLYWOOD / BOLLYWOOD / ANIME
- ESPORTS / GAMING
- MEME CULTURE / VIRAL INTERNET
- GLOBAL TECH / POP CULTURE

Requirements:
- Raw JSON ONLY, without markdown format tags:
{
  "category": "MOVIES or ESPORTS or GAMING or MEMES or GLOBAL BUZZ",
  "search_keyword": "1 simple english search term for visual background (e.g. cinema, controller, concert, anime)",
  "headline": "Short viral hook in 6 to 9 words",
  "bullet_points": "2 crisp facts explaining the update in Hinglish",
  "caption": "Full Instagram caption: bold opener, 2 brief points, provocative question to drive comments, and 7 high-reach hashtags (#DesiCulture #GlobalBuzz etc.)"
}
"""

gen_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_endpoint}:generateContent?key={GEMINI_KEY}"
payload = {
    "contents": [{"parts": [{"text": prompt}]}],
    "generationConfig": {"response_mime_type": "application/json"}
}

res = requests.post(gen_url, json=payload).json()
if "candidates" not in res:
    raise Exception(f"Gemini API Error: {res}")

raw_text = res["candidates"][0]["content"]["parts"][0]["text"]
if "```json" in raw_text:
    raw_text = raw_text.split("```json")[1].split("```")[0].strip()
elif "```" in raw_text:
    raw_text = raw_text.split("```")[1].split("```")[0].strip()

news = json.loads(raw_text)
category = news.get("category", "GLOBAL BUZZ").upper()
search_kw = news.get("search_keyword", "entertainment")
headline = news.get("headline", "Global Culture Update")
bullets = news.get("bullet_points", "")
caption = news.get("caption", "")
full_caption = f"🌍 🚨 {headline}\n\n{caption}"

# 4. Vertical 4:5 Poster Design (1080x1350)
canvas = Image.new("RGB", (1080, 1350), color=(15, 17, 23))

# Fetch relevant photo
try:
    img_res = requests.get(f"https://picsum.photos/1080/750?{search_kw}", timeout=10)
    if img_res.status_code == 200:
        top_img = Image.open(BytesIO(img_res.content)).convert("RGB")
        top_img = top_img.resize((1080, 750))
        canvas.paste(top_img, (0, 0))
except Exception as e:
    print("Background load fallback:", e)

draw = ImageDraw.Draw(canvas)

# Dark gradient transition
for y in range(480, 750):
    alpha = int(255 * ((y - 480) / 270))
    draw.line([(0, y), (1080, y)], fill=(15, 17, 23, alpha))

# Category Badge (Dynamic theme colors)
tag_color = (225, 29, 72) if "ESPORTS" in category or "GAMING" in category else (245, 158, 11)
draw.rounded_rectangle([(60, 60), (440, 125)], radius=12, fill=tag_color)
draw.text((85, 78), category, fill=(255, 255, 255))

# Text Card Formatting
headline_lines = textwrap.wrap(headline, width=28)
y_offset = 770
for line in headline_lines[:3]:
    draw.text((70, y_offset), line, fill=(255, 255, 255))
    y_offset += 65

y_offset += 20
bullet_lines = textwrap.wrap(bullets, width=42)
for line in bullet_lines[:4]:
    draw.text((70, y_offset), line, fill=(185, 190, 205))
    y_offset += 45

# Brand Footer
draw.line([(70, 1240), (1010, 1240)], fill=(38, 42, 53), width=2)
draw.text((70, 1265), "@thedesiculture.in", fill=(245, 158, 11))
draw.text((810, 1265), "GLOBAL CULTURE", fill=(120, 125, 140))

# 5. Image Hosting & Buffer Dispatch
img_bytes = BytesIO()
canvas.save(img_bytes, format="JPEG", quality=92)
img_bytes.seek(0)

upload = requests.post(
    "https://tmpfiles.org/api/v1/upload",
    files={"file": ("post.jpg", img_bytes, "image/jpeg")}
)

img_url = ""
if upload.status_code == 200:
    orig = upload.json().get("data", {}).get("url", "")
    img_url = orig.replace("tmpfiles.org/", "tmpfiles.org/dl/")
    print("Hosted Image URL:", img_url)

buffer_payload = {
    "access_token": BUFFER_TOKEN,
    "profile_ids[]": BUFFER_PROFILE_ID,
    "text": full_caption,
    "now": True
}
if img_url:
    buffer_payload["media[photo]"] = img_url

buffer_res = requests.post("https://api.bufferapp.com/1/updates/create.json", data=buffer_payload)
print("Buffer Status:", buffer_res.status_code)
print("Buffer Response:", buffer_res.text)
