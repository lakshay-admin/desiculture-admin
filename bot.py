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

# 2. Trending Worldwide News & Meme Prompt
prompt_text = """
You are a senior digital news editor for 'Desi Culture'.
Find 1 trending viral news topic right now from across the WORLD or INDIA in one of these categories:
- MOVIES / HOLLYWOOD / BOLLYWOOD / ANIME
- ESPORTS / GAMING
- MEME CULTURE / VIRAL INTERNET
- GLOBAL TECH / POP CULTURE

Return raw JSON ONLY without markdown backticks:
{
  "category": "MOVIES or ESPORTS or GAMING or MEMES or GLOBAL BUZZ",
  "search_keyword": "single english word for visual background e.g. cinema or gamer or meme or concert",
  "headline": "Short punchy hook in 6 to 9 words",
  "bullet_points": "2 crisp facts explaining the update in Hinglish",
  "caption": "Full Instagram caption with hook, bullet points, discussion question, and 7 hashtags #DesiCulture #GlobalBuzz"
}
"""

raw_text = ""

# Method A: Try Interactions API (Google's latest format for 3.0 models)
try:
    interact_url = f"https://generativelanguage.googleapis.com/v1alpha/interactions?key={GEMINI_KEY}"
    interact_payload = {
        "model": "gemini-3.0-flash",
        "input": prompt_text,
        "response_mime_type": "application/json"
    }
    r = requests.post(interact_url, json=interact_payload, timeout=20)
    print("Interactions API Status:", r.status_code)
    if r.status_code == 200:
        data = r.json()
        raw_text = data.get("output", "") or data.get("text", "")
except Exception as e:
    print("Interactions API fallback trigger:", e)

# Method B: Fallback to dynamic listModels if Method A didn't populate raw_text
if not raw_text:
    models_res = requests.get(f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_KEY}").json()
    available = [
        m["name"] for m in models_res.get("models", [])
        if "generateContent" in m.get("supportedGenerationMethods", [])
    ]
    print("Available models in account:", available)
    
    # Try each available model until one succeeds
    for m_name in available:
        clean_name = m_name.replace("models/", "")
        gen_url = f"https://generativelanguage.googleapis.com/v1beta/models/{clean_name}:generateContent?key={GEMINI_KEY}"
        payload = {
            "contents": [{"parts": [{"text": prompt_text}]}],
            "generationConfig": {"response_mime_type": "application/json"}
        }
        res = requests.post(gen_url, json=payload)
        if res.status_code == 200:
            res_json = res.json()
            if "candidates" in res_json:
                raw_text = res_json["candidates"][0]["content"]["parts"][0]["text"]
                print(f"Successfully generated using: {clean_name}")
                break

if not raw_text:
    raise Exception("Could not generate content from any Gemini endpoint. Check API key permissions.")

# Clean JSON
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
full_caption = f"🚨 {headline}\n\n{caption}"
print("\n--- GENERATED POST ---\n", full_caption)

# 3. Vertical 4:5 Poster Design (1080x1350 px)
canvas = Image.new("RGB", (1080, 1350), color=(15, 17, 23))

# Fetch background photo
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

# Category Badge
tag_color = (225, 29, 72) if ("ESPORTS" in category or "GAMING" in category) else (245, 158, 11)
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

# 4. Image Hosting
img_bytes = BytesIO()
canvas.save(img_bytes, format="JPEG", quality=92)
img_bytes.seek(0)

img_url = ""
try:
    upload = requests.post(
        "https://tmpfiles.org/api/v1/upload",
        files={"file": ("post.jpg", img_bytes, "image/jpeg")}
    )
    if upload.status_code == 200:
        orig = upload.json().get("data", {}).get("url", "")
        img_url = orig.replace("tmpfiles.org/", "tmpfiles.org/dl/")
        print("Hosted Image URL:", img_url)
except Exception as e:
    print("Hosting error:", e)

# 5. Buffer Dispatch
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
