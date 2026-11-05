import os
import json
import requests
import google.generativeai as genai

# 1. API Keys
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
BUFFER_TOKEN = os.environ.get("BUFFER_ACCESS_TOKEN")
BUFFER_PROFILE_ID = os.environ.get("BUFFER_PROFILE_ID")

# 2. Gemini Configure
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

prompt = """
Find 1 trending, verified news or buzz topic from India right now in Entertainment, Bollywood, Pop Culture, Memes, or Esports.
Write an engaging Instagram news post for 'Desi Culture'.

Strict requirements:
- Language: Engaging Hinglish / English mix.
- Tone: Crisp, exciting, professional youth-focused news.
- Never assert unverified gossip as pure fact (use 'reportedly' or attribution).
- Output must be raw JSON only with two keys:
  "headline": "Short punchy hook in 6-10 words",
  "caption": "Full Instagram caption with 2-3 short bullet points, a discussion question, and 5-7 trending hashtags (#DesiCulture etc.)"
"""

response = model.generate_content(
    prompt,
    generation_config={"response_mime_type": "application/json"}
)

news_data = json.loads(response.text)
full_text = f"🚨 {news_data['headline']}\n\n{news_data['caption']}"
print("Generated Post Content:\n", full_text)

# 3. Buffer Post
buffer_url = "https://api.bufferapp.com/1/updates/create.json"
payload = {
    "access_token": BUFFER_TOKEN,
    "profile_ids[]": BUFFER_PROFILE_ID,
    "text": full_text,
    "now": True
}

res = requests.post(buffer_url, data=payload)
print("Buffer Status Code:", res.status_code)
print("Buffer Response:", res.text)
