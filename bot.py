import os
import json
import requests

# 1. Secrets read karna
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
BUFFER_TOKEN = os.environ.get("BUFFER_ACCESS_TOKEN")
BUFFER_PROFILE_ID = os.environ.get("BUFFER_PROFILE_ID")

# 2. Check available models using current API key
test_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_KEY}"
test_res = requests.get(test_url)
print("Available Models / API Status:", test_res.status_code)
print(test_res.text[:500])

# 3. Direct Gemini Request
gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_KEY}"

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
    "contents": [{"parts": [{"text": prompt}]}]
}

res = requests.post(gemini_url, headers=headers, json=payload)
print("Generate Status Code:", res.status_code)
print("Generate Response Raw:", res.text)

res_json = res.json()

if "candidates" in res_json:
    raw_text = res_json['candidates'][0]['content']['parts'][0]['text']
    # Clean possible markdown block if model adds ```json
    if "```json" in raw_text:
        raw_text = raw_text.split("```json")[1].split("```")[0].strip()
    elif "```" in raw_text:
        raw_text = raw_text.split("```")[1].split("```")[0].strip()

    news_data = json.loads(raw_text)
    full_text = f"🚨 {news_data['headline']}\n\n{news_data['caption']}"
    print("\n--- GENERATED POST ---\n", full_text)

    # 4. Buffer Post
    buffer_url = "[https://api.bufferapp.com/1/updates/create.json](https://api.bufferapp.com/1/updates/create.json)"
    buffer_payload = {
        "access_token": BUFFER_TOKEN,
        "profile_ids[]": BUFFER_PROFILE_ID,
        "text": full_text,
        "now": True
    }
    buffer_res = requests.post(buffer_url, data=buffer_payload)
    print("Buffer Status Code:", buffer_res.status_code)
    print("Buffer Response:", buffer_res.text)
else:
    print("Gemini API Error:", res_json)
