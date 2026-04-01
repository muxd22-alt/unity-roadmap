import os
import json
import urllib.request
from xml.etree import ElementTree as ET
import datetime

# Attempt to read the API key from the OpenRouter secret.
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "").strip()

data = {
    "insight": "",
    "news": []
}

# 1. Fetch OpenRouter Insight
if OPENROUTER_API_KEY:
    try:
        req_data = {
            "model": "google/gemini-2.5-flash",
            "messages": [
                {
                    "role": "system", 
                    "content": "You are a professional technical mentor guiding a developer towards AAA-tier Unity 3D Multilayer game development. Provide short, bulleted actionable facts."
                },
                {
                    "role": "user", 
                    "content": "Provide a concise 1-2 paragraph insight on a trending topic regarding 'Multiplayer 3D game development' in Unity (e.g. Netcode for GameObjects or Matchmaking). Output the response in English first, then provide a professional translation into Arabic."
                }
            ],
            "max_tokens": 500
        }
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=json.dumps(req_data).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/Unity-Roadmap",
                "X-Title": "Unity Roadmap Actions"
            }
        )
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode())
            data["insight"] = res_data["choices"][0]["message"]["content"]
    except Exception as e:
        data["insight"] = f"Error fetching AI insight from OpenRouter: {str(e)}"
else:
    data["insight"] = "🔑 **OpenRouter insight not loaded.**\nTo see daily AI insights here, please add an `OPENROUTER_API_KEY` to your GitHub Repository Secrets.\n\nالرؤية اليومية معطلة لعدم توفر مفتاح OpenRouter."

# 2. Fetch Reddit Data (/r/Unity3D top daily)
try:
    req = urllib.request.Request(
        "https://www.reddit.com/r/Unity3D/top.json?limit=3&t=day",
        headers={"User-Agent": "Mozilla/5.0 (Unity Roadmap Bot 1.0)"}
    )
    with urllib.request.urlopen(req) as response:
        reddit_data = json.loads(response.read().decode())
        count = 0
        for post in reddit_data["data"]["children"]:
            if not post["data"]["stickied"] and count < 3:
                # Format to absolute correct permalink
                url_path = post["data"]["permalink"]
                data["news"].append({
                    "title": post["data"]["title"],
                    "url": "https://www.reddit.com" + url_path,
                    "source": "Reddit /r/Unity3D",
                    "date": datetime.datetime.fromtimestamp(post["data"]["created_utc"]).strftime("%Y-%m-%d")
                })
                count += 1
except Exception as e:
    print(f"Failed to fetch Reddit: {str(e)}")

# 3. Fetch Unity Blog RSS Data
try:
    req = urllib.request.Request(
        "https://blog.unity.com/feed",
        headers={"User-Agent": "Mozilla/5.0 (Unity Roadmap Bot 1.0)"}
    )
    with urllib.request.urlopen(req) as response:
        xml_data = response.read()
        root = ET.fromstring(xml_data)
        
        # Locate the items in standard RSS XML structure
        channel = root.find('channel')
        if channel is not None:
            count = 0
            for item in channel.findall('item'):
                if count >= 3:
                    break
                
                title_el = item.find('title')
                link_el = item.find('link')
                pubdate_el = item.find('pubDate')
                
                title = title_el.text if title_el is not None else "Unity Blog Post"
                link = link_el.text if link_el is not None else "#"
                pubdate = pubdate_el.text if pubdate_el is not None else ""
                
                date_clean = pubdate[:16].strip() if pubdate else ""
                
                data["news"].append({
                    "title": title,
                    "url": link,
                    "source": "Unity Blog",
                    "date": date_clean
                })
                count += 1
except Exception as e:
    print(f"Failed to fetch Unity RSS: {str(e)}")

# Generate docs/data.json payload locally
docs_path = os.path.join(os.getcwd(), "docs")
os.makedirs(docs_path, exist_ok=True)
json_path = os.path.join(docs_path, "data.json")

with open(json_path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Data update complete. Built successfully to {json_path}")
