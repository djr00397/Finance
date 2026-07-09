import os
import json
import requests
import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

def main():
    # কনফিগারেশন
    CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
    CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
    REFRESH_TOKEN = os.environ.get("GOOGLE_REFRESH_TOKEN")
    BLOG_ID = os.environ.get("BLOG_ID")
    OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

    CATEGORIES = ["Credit Cards", "Loans", "Banking", "Investing", "Insurance", "Taxes", "Personal Finance"]
    category = CATEGORIES[datetime.datetime.now().hour % len(CATEGORIES)]

    # ১. কন্টেন্ট জেনারেশন (SEO Optimized)
    prompt = f"""
    Act as a Financial Expert. Write a professional, SEO-optimized blog post in HTML format for the category: {category}.
    Title: Create a unique, trending title.
    Content: 500+ words, use <h2> and <h3> for subheadings, include real-world financial examples.
    End: Add 3 Multiple Choice Questions (MCQs) for engagement.
    SEO: Include Meta Description, Keywords.
    Output: Return ONLY a valid JSON object with keys: "title", "content", "meta_description".
    """
    
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
    resp = requests.post("https://openrouter.ai/api/v1/chat/completions", 
        headers=headers, json={"model": "meta-llama/llama-3-8b-instruct", "messages": [{"role": "user", "content": prompt}]})
    
    # JSON Parsing
    content_text = resp.json()['choices'][0]['message']['content'].strip()
    data = json.loads(content_text)

    # ২. ব্লগার API কানেকশন
    creds = Credentials(None, refresh_token=REFRESH_TOKEN, client_id=CLIENT_ID, client_secret=CLIENT_SECRET, token_uri="https://oauth2.googleapis.com/token")
    service = build('blogger', 'v3', credentials=creds)
    
    # ৩. পোস্ট পাবলিশিং
    post_body = {
        "title": data['title'],
        "content": f"<div>{data['content']}</div><br><hr><p>SEO Meta: {data['meta_description']}</p>",
        "labels": [category]
    }
    
    result = service.posts().insert(blogId=BLOG_ID, body=post_body).execute()
    print(f"Success! Post URL: {result.get('url')}")

if __name__ == "__main__":
    main()
    
