import os
import json
import random
import textwrap
import requests
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip

# 1. Credentials
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
BUFFER_TOKEN = os.environ.get("BUFFER_ACCESS_TOKEN")
BUFFER_CHANNEL_ID = os.environ.get("BUFFER_PROFILE_ID", "").strip().split(",")[0]

# 2. Dynamic Gemini Model Selection
models_res = requests.get(f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_KEY}").json()
available = [
    m["name"].replace("models/", "") for m in models_res.get("models", [])
    if "generateContent" in m.get("supportedGenerationMethods", [])
]
chosen_models = [m for m in available if "flash" in m.lower()] + available

prompt_text = """
You are a senior digital editor for viral Instagram page 'Desi Culture'.
Find 1 trending viral news/meme/gaming topic right now.
Return raw JSON ONLY:
{
  "headline": "Punchy hook in 8 to 12 words highlighting the drama, update, or fact",
  "subtext": "1 short context line under headline",
  "caption": "Viral Instagram Reel caption with engagement question, emojis, and 7 hashtags #DesiCulture"
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
            break
    except Exception:
        continue

if not raw_text:
    raise Exception("Gemini generation failed.")

if "```json" in raw_text:
    raw_text = raw_text.split("```json")[1].split("```")[0].strip()
elif "```" in raw_text:
    raw_text = raw_text.split("```")[1].split("```")[0].strip()

news = json.loads(raw_text)
headline = str(news.get("headline", "VIRAL POP CULTURE UPDATE DROPS"))
subtext = str(news.get("subtext", "CCTV / Visuals surface online"))
caption = str(news.get("caption", ""))
full_caption = f"🚨 {headline}\n\n{caption}"
print("\n--- REEL CAPTION ---\n", full_caption)

# 3. Download Vertical Royalty-Free Video (Direct URLs, Zero API Key needed)
VIDEO_FEEDS = [
    "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
    "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4",
    "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4"
]
selected_video_url = random.choice(VIDEO_FEEDS)

print("Downloading video clip...")
v_resp = requests.get(selected_video_url, timeout=30)
with open("raw_video.mp4", "wb") as f:
    f.write(v_resp.content)

# 4. Generate 9:16 Transparent Lower-Third Overlay Card
overlay = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
draw = ImageDraw.Draw(overlay)

def get_font(size, bold=True):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"
    ]
    for p in paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

font_head = get_font(44, bold=True)
font_sub = get_font(28, bold=False)
font_brand = get_font(30, bold=True)

# Build text banner blocks (fact.of.indian style)
lines = textwrap.wrap(headline, width=28)
card_y = 1220
line_height = 62

for line in lines[:3]:
    draw.rectangle([(60, card_y), (1020, card_y + line_height)], fill=(12, 60, 48, 235))
    draw.text((80, card_y + 8), line, fill=(255, 255, 255), font=font_head)
    card_y += line_height + 10

# Subtext
draw.text((60, card_y + 15), subtext, fill=(240, 240, 240, 240), font=font_sub)

# Branding & Social Icons Bar
brand_y = card_y + 85
draw.text((60, brand_y), "@THEDESICULTURE.IN", fill=(255, 255, 255, 255), font=font_brand)

def draw_icons(d, x, y):
    # Instagram
    d.rounded_rectangle([(x, y), (x+36, y+36)], radius=8, outline=(255, 255, 255), width=3)
    d.ellipse([(x+10, y+10), (x+26, y+26)], outline=(255, 255, 255), width=3)
    # X
    d.line([(x+55, y), (x+85, y+36)], fill=(255, 255, 255), width=3)
    d.line([(x+85, y), (x+55, y+36)], fill=(255, 255, 255), width=3)
    # Facebook
    d.ellipse([(x+105, y), (x+141, y+36)], outline=(255, 255, 255), width=3)
    d.text((x+118, y+5), "f", fill=(255, 255, 255), font=font_brand)

draw_icons(draw, 840, brand_y - 5)
overlay.save("overlay.png")

# 5. Composite 9:16 Video (7-second loop)
print("Rendering Reel via MoviePy...")
clip = VideoFileClip("raw_video.mp4")
dur = min(7, clip.duration)
clip = clip.subclip(0, dur).resize(height=1920)

if clip.w > 1080:
    clip = clip.crop(x_center=clip.w / 2, width=1080)
elif clip.w < 1080:
    clip = clip.resize(width=1080)

overlay_clip = ImageClip("overlay.png").set_duration(clip.duration)
final_video = CompositeVideoClip([clip, overlay_clip])
final_video.write_videofile("final_reel.mp4", codec="libx264", audio_codec="aac", fps=24, preset="ultrafast")

# 6. Upload MP4 to Direct CDN
print("Hosting Reel video file...")
with open("final_reel.mp4", "rb") as vf:
    upload = requests.post(
        "https://catbox.moe/user/api.php",
        data={"reqtype": "fileupload"},
        files={"fileToUpload": ("desi_reel.mp4", vf, "video/mp4")},
        timeout=60
    )

reel_url = upload.text.strip()
print("Direct Hosted Reel URL:", reel_url)
if not reel_url.startswith("http"):
    raise Exception("Video hosting failed: " + reel_url)

# 7. Post to Buffer as Reel
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
                "type": "reel",
                "shouldShareToFeed": True
            }
        },
        "assets": {
            "video": {
                "url": reel_url
            }
        }
    }
}

buffer_res = requests.post(graphql_url, headers=headers, json={"query": mutation, "variables": variables})
print("Buffer Status:", buffer_res.status_code)
print("Buffer Response:", buffer_res.text)
