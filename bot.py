import os
import json
import textwrap
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

# 1. Credentials
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
BUFFER_TOKEN = os.environ.get("BUFFER_ACCESS_TOKEN")
BUFFER_PROFILE_ID = os.environ.get("BUFFER_PROFILE_ID")

# 2. Select Gemini Model Dynamically
models_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_KEY}"
models_res = requests.get(models_url).json()

supported = [
    m["name"] for m in models_res.get("models", [])
    if "generateContent" in m.get("supportedGenerationMethods", [])
]
chosen_model = next((m for m in supported if "flash" in m.lower()), supported[0])

prompt = """
Find 1 trending Indian pop-culture, Bollywood, esports, or meme buzz topic.
Output raw JSON ONLY:
{
  "category": "BOLLYWOOD or ESPORTS or TRENDING",
  "search_keyword": "1-2 generic english words to fetch a high-res photo, e.g. 'cinema', 'gaming', 'concert'",
  "headline": "Punchy viral hook in 6-10 words",
  "bullet_points": "2 concise factual takeaways",
  "caption": "Engaging Hinglish Instagram caption with hook, points, discussion question, and 5 hashtags #DesiCulture"
}
"""

gen_url = f"https://generativelanguage.googleapis.com/v1beta/{chosen_model}:generateContent?key={GEMINI_KEY}"
res = requests.post(gen_url, json={"contents": [{"parts": [{"text": prompt}]}]}).json()

raw_text = res["candidates"][0]["content"]["parts"][0]["text"]
if "```json" in raw_text:
    raw_text = raw_text.split("```json")[1].split("```")[0].strip()
elif "```" in raw_text:
    raw_text = raw_text.split("```")[1].split("```")[0].strip()

news = json.loads(raw_text)
category = news.get("category", "TRENDING").upper()
search_kw = news.get("search_keyword", "entertainment")
headline = news.get("headline", "Trending Desi Update")
bullets = news.get("bullet_points", "")
caption = news.get("caption", "")
full_caption = f"🚨 {headline}\n\n{caption}"

# 3. Canvas Setup (4:5 Ratio - 1080x1350)
canvas = Image.new("RGB", (1080, 1350), color=(15, 17, 23))

# Fetch background photo for top 55%
img_res = requests.get(f"https://picsum.photos/1080/750?{search_kw}", timeout=10)
if img_res.status_code == 200:
    top_img = Image.open(BytesIO(img_res.content)).convert("RGB")
    top_img = top_img.resize((1080, 750))
    canvas.paste(top_img, (0, 0))

# Gradient dark fade transition between photo and text box
draw = ImageDraw.Draw(canvas)
for y in range(500, 750):
    alpha = int(255 * ((y - 500) / 250))
    draw.line([(0, y), (1080, y)], fill=(15, 17, 23, alpha))

# Category Badge (Top Left over image)
draw.rounded_rectangle([(60, 60), (360, 120)], radius=12, fill=(225, 29, 72))
draw.text((85, 75), category, fill=(255, 255, 255))

# Typography: Wrapped Headline & Bullets
headline_lines = textwrap.wrap(headline, width=28)
y_offset = 780
for line in headline_lines[:3]:
    draw.text((70, y_offset), line, fill=(255, 255, 255))
    y_offset += 65

y_offset += 25
bullet_lines = textwrap.wrap(bullets, width=42)
for line in bullet_lines[:4]:
    draw.text((70, y_offset), line, fill=(180, 185, 200))
    y_offset += 45

# Branding Footer
draw.line([(70, 1240), (1010, 1240)], fill=(40, 45, 55), width=2)
draw.text((70, 1265), "@thedesiculture.in", fill=(245, 158, 11))
draw.text((820, 1265), "SWIPE >>", fill=(120, 125, 140))

# 4. Host Image Temporarily
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

# 5. Send to Buffer
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
