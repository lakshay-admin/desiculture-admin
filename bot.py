import os
import json
import requests

# 1. Secrets read karna
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
BUFFER_TOKEN = os.environ.get("BUFFER_ACCESS_TOKEN")
BUFFER_PROFILE_ID = os.environ.get("BUFFER_PROFILE_ID")

# 2. Direct Gemini REST API Call
gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"

prompt = """
Find 1 trending, verified news or buzz topic from India right now in Entertainment, Bollywood, Pop Culture, Memes, or Esports.
Write an engaging Instagram news post for 'Desi Culture'.

Strict requirements:
- Language: Engaging Hinglish / English mix.
- Tone: Crisp, exciting, professional youth-focused news.
- Never assert unverified gossip as pure fact (use 'reportedly' or attribution).
- Output must be raw JSON only without markdown ticks, with two keys:
  "headline": "Short punchy hook in 6-10 words",
  "caption": "Full Instagram caption with 2-3 short bullet points, a discussion question, and 5-7 trending hashtags (#DesiCulture etc.)"
"""

headers = {"Content-Type": "application/json"}
payload = {
    "contents": [{"parts": [{"text": prompt}]}],
    "generationConfig": {"response_mime_type": "application/json"}
}

res = requests.post(gemini_url, headers=headers, json=payload)
res_json = res.json()

# Response parse karna
raw_text = res_json['candidates'][0]['content']['parts'][0]['text']
news_data = json.loads(raw_text)

full_text = f"🚨 {news_data['headline']}\n\n{news_data['caption']}"
print("Generated Post Content:\n", full_text)

# 3. Buffer API Call
buffer_url = "https://api.bufferapp.com/1/updates/create.json"
buffer_payload = {
    "access_token": BUFFER_TOKEN,
    "profile_ids[]": BUFFER_PROFILE_ID,
    "text": full_text,
    "now": True
}

buffer_res = requests.post(buffer_url, data=buffer_payload)
print("Buffer Status Code:", buffer_res.status_code)
print("Buffer Response:", buffer_res.text)
