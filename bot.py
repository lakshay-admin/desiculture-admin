import os
import json
import base64
import textwrap
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

# 1. Credentials
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
BUFFER_TOKEN = os.environ.get("BUFFER_ACCESS_TOKEN")
BUFFER_CHANNEL_ID = os.environ.get("BUFFER_PROFILE_ID", "").strip()

# 2. Dynamic Model Selection
models_res = requests.get(f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_KEY}").json()
available = [
    m["name"].replace("models/", "") for m in models_res.get("models", [])
    if "generateContent" in m.get("supportedGenerationMethods", [])
]
chosen_models = [m for m in available if "flash" in m.lower()] + available

prompt_text = """
You are a senior digital editor for Indian pop culture page 'Desi Culture'.
Pick 1 massive trending news right now from India or Global in:
- Cinema / Bollywood / Hollywood / OTT
- Gaming / Esports / GTA / Anime
- Viral Drama / Memes / Big Personalities

Return raw JSON ONLY:
{
  "red_tag": "2-3 WORDS ALL CAPS ATTENTION HOOK e.g. HUGE UPDATE, SHOCKING, BIG REVEAL, CONFIRMED, PEACE OFFER",
  "headline": "Punchy viral headline in 7 to 12 words in Hinglish or English that creates instant curiosity",
  "sub_text": "Short 1-line key takeaway or attribution (e.g. ~ OFFICIAL STATEMENT or ~ SOURCES CONFIRM)",
  "search_keyword": "single relevant visual search term e.g. cinema, stadium, gaming, supercar, concert, tech",
  "caption": "Full Instagram caption with hook, emojis, 2-line detail, engagement question, and 7 hashtags #DesiCulture"
}
"""

raw_text = ""
for model in chosen_models:
    try:
        gen_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_KEY}"
        payload = {
            "contents": [{"parts": [{"text": prompt_text}]}],
            "generationConfig": {"response_mime_type": "application/json"}
        }
        res = requests.post(gen_url, json=payload, timeout=25).json()
        if "candidates" in res and res["candidates"]:
            raw_text = res["candidates"][0]["content"]["parts"][0]["text"]
            print(f"Generated using model: {model}")
            break
    except Exception as e:
        print(f"Failed with {model}:", e)

if not raw_text:
    raise Exception("Could not generate content from Gemini.")

if "```json" in raw_text:
    raw_text = raw_text.split("```json")[1].split("```")[0].strip()
elif "```" in raw_text:
    raw_text = raw_text.split("```")[1].split("```")[0].strip()

news = json.loads(raw_text)
red_tag = str(news.get("red_tag", "BREAKING UPDATE")).upper()
headline = str(news.get("headline", "Major News Update Just Dropped")).upper()
sub_text = str(news.get("sub_text", "~ DESI CULTURE EXCLUSIVE"))
search_kw = str(news.get("search_keyword", "entertainment"))
caption = str(news.get("caption", ""))

full_caption = f"🚨 {red_tag}: {headline}\n\n{caption}"
print("\n--- GENERATED POST ---\n", full_caption)

# 3. Canvas Construction: Ghantaa / RVCJ High-Reach Layout (1080x1350 px)
canvas = Image.new("RGB", (1080, 1350), color=(255, 255, 255))
draw = ImageDraw.Draw(canvas)

# System Font Helper with fallback
def get_font(size, bold=True):
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf" if bold else "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
    ]
    for p in font_paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()

font_tag = get_font(72, bold=True)
font_head = get_font(46, bold=True)
font_sub = get_font(26, bold=True)
font_foot = get_font(28, bold=True)

# Top Brand Badge
draw.text((1080 // 2, 45), "@THEDESICULTURE.IN", fill=(110, 115, 125), font=font_sub, anchor="mm")

# Massive Attention Red Hook
draw.text((1080 // 2, 125), red_tag, fill=(225, 29, 72), font=font_tag, anchor="mm")

# Bold Black Headline (Centered text block)
headline_lines = textwrap.wrap(headline, width=28)
y_text = 195
for line in headline_lines[:3]:
    draw.text((1080 // 2, y_text), line, fill=(18, 18, 20), font=font_head, anchor="mm")
    y_text += 58

# Attribution Subtext
draw.text((1080 // 2, y_text + 15), sub_text, fill=(120, 125, 135), font=font_sub, anchor="mm")

# Lower Half: Visual Area (From y=440 down to y=1280)
visual_box_top = 430
visual_box_height = 850

curated_sources = [
    f"https://images.unsplash.com/photo-1511512578047-dfb367046420?w=1080&h=850&fit=crop", # gaming/tech
    f"https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=1080&h=850&fit=crop", # cinema/show
    f"https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=1080&h=850&fit=crop"  # pop culture/lights
]

img_loaded = False
for src in curated_sources:
    try:
        r = requests.get(src, timeout=10)
        if r.status_code == 200:
            top_img = Image.open(BytesIO(r.content)).convert("RGB")
            top_img = top_img.resize((1080, visual_box_height))
            canvas.paste(top_img, (0, visual_box_top))
            img_loaded = True
            break
    except Exception:
        continue

# Subtle border line between header & image
draw.line([(0, visual_box_top), (1080, visual_box_top)], fill=(220, 224, 230), width=3)

# Bottom Minimal Watermark Bar
draw.rectangle([(0, 1280), (1080, 1350)], fill=(12, 14, 18))
draw.text((55, 1315), "DESI CULTURE NEWS", fill=(245, 158, 11), font=font_foot, anchor="lm")
draw.text((1025, 1315), "POP CULTURE • GAMING", fill=(160, 165, 175), font=font_sub, anchor="rm")

# 4. Direct CDN Hosting
img_bytes = BytesIO()
canvas.save(img_bytes, format="JPEG", quality=92)
raw_image = img_bytes.getvalue()
b64_image = base64.b64encode(raw_image).decode("utf-8")

img_url = ""
try:
    resp = requests.post(
        "https://freeimage.host/api/1/upload",
        data={
            "key": "6d207e02198a847aa98d0a2a901485a5",
            "action": "upload",
            "source": b64_image,
            "format": "json"
        },
        timeout=25
    )
    if resp.status_code == 200:
        img_url = resp.json().get("image", {}).get("url", "")
        if img_url:
            print("CDN Hosted URL:", img_url)
except Exception as e:
    print("FreeImage upload error:", e)

if not img_url:
    try:
        resp = requests.post(
            "https://api.imgbb.com/1/upload",
            data={
                "key": "2ba37a4c6655c6bba52a468fa35ff61a",
                "image": b64_image
            },
            timeout=25
        )
        if resp.status_code == 200:
            img_url = resp.json().get("data", {}).get("url", "")
            if img_url:
                print("ImgBB Hosted URL:", img_url)
    except Exception as e:
        print("ImgBB upload error:", e)

if not img_url:
    raise Exception("Image hosting failed.")

# 5. Buffer GraphQL API Post Submission
graphql_url = "https://api.buffer.com"
headers = {
    "Authorization": f"Bearer {BUFFER_TOKEN}",
    "Content-Type": "application/json"
}

mutation = """
mutation CreatePost($input: CreatePostInput!) {
  createPost(input: $input) {
    ... on PostActionSuccess {
      post {
        id
        status
      }
    }
    ... on MutationError {
      message
    }
  }
}
"""

variables = {
    "input": {
        "channelId": BUFFER_CHANNEL_ID,
        "text": full_caption,
        "mode": "shareNow",
        "schedulingType": "automatic",
        "metadata": {
            "instagram": {
                "type": "post",
                "shouldShareToFeed": True
            }
        },
        "assets": {
            "image": {
                "url": img_url
            }
        }
    }
}

buffer_res = requests.post(
    graphql_url,
    headers=headers,
    json={"query": mutation, "variables": variables}
)

print("Buffer GraphQL Status:", buffer_res.status_code)
print("Buffer GraphQL Response:", buffer_res.text)
