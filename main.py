import os
import json
import requests
import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

def main():
    # কনফিগারেশন
    CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "").strip()
    CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "").strip()
    REFRESH_TOKEN = os.environ.get("GOOGLE_REFRESH_TOKEN", "").strip()
    BLOG_ID = os.environ.get("BLOG_ID", "").strip()
    OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "").strip()

    # আপনার ওয়েবসাইটের মেনু বাটন (এই নামগুলো ব্লগারে ক্যাটাগরি হিসেবে থাকবে)
    CATEGORIES = ["Credit Cards", "Loans", "Banking", "Investing", "Insurance", "Taxes", "Personal Finance"]
    
    # ধারাবাহিকভাবে ক্যাটাগরি নির্বাচনের লজিক (প্রতি ঘন্টায় একটি)
    category = CATEGORIES[datetime.datetime.now().hour % len(CATEGORIES)]

    # ভাইরাল টপিক ও এসইও করার জন্য শক্তিশালী প্রম্পট
    prompt = f"""
    You are a world-class Financial Master. Write a blog post for the category '{category}'.
    1. VIRAL TOPIC: Choose a current trending or viral topic within '{category}'.
    2. SEO TITLE: Create a highly clickable, viral SEO title that grabs attention.
    3. SEO CONTENT: Write 600 words. Use H2 and H3 for easy scanning.
    4. AD-FRIENDLY: Keep wide spacing between paragraphs for Google Auto Ads.
    5. ENGAGEMENT: Add exactly 3 Multiple Choice Questions (MCQs) at the end.
    6. FORMAT: Output ONLY in JSON format: {{"title": "...", "content": "...", "meta_description": "..."}}
    """
    
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
    
    # এআই কল
    resp = requests.post("https://openrouter.ai/api/v1/chat/completions", 
        headers=headers, 
        json={"model": "meta-llama/llama-3-8b-instruct", "messages": [{"role": "user", "content": prompt}]}
    )
    
    if resp.status_code != 200:
        print(f"Error: {resp.text}")
        return

    # JSON ডাটা এক্সট্রাক্ট করা
    text = resp.json()['choices'][0]['message']['content'].strip()
    start, end = text.find('{'), text.rfind('}') + 1
    data = json.loads(text[start:end])

    # ব্লগার এপিআই কানেকশন
    creds = Credentials(None, refresh_token=REFRESH_TOKEN, client_id=CLIENT_ID, client_secret=CLIENT_SECRET, token_uri="https://oauth2.googleapis.com/token")
    service = build('blogger', 'v3', credentials=creds)
    
    # পোস্ট পাবলিশিং (আপনার মেনু বাটন অনুযায়ী লেবেল যোগ করা হলো)
    service.posts().insert(blogId=BLOG_ID, body={
        "title": data['title'],
        "content": f"{data['content']}<br><br><small>SEO Meta: {data['meta_description']}</small>",
        "labels": [category] # এটা আপনার মেনু বাটনের সাথে হুবহু মিলে যাবে
    }).execute()
    
    print(f"Successfully posted to {category}!")

if __name__ == "__main__":
    main()
    
