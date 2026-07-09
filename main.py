import os
import json
import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# ================= সিক্রেট কনফিগারেশন (গিটহাব থেকে আসবে) =================
CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
REFRESH_TOKEN = os.environ.get("GOOGLE_REFRESH_TOKEN")
BLOG_ID = os.environ.get("BLOG_ID")

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# ক্যাটাগরি লিস্ট (এখান থেকেই ধারাবাহিকভাবে পরিবর্তন হবে)
CATEGORIES = [
    "Credit Cards",
    "Loans",
    "Banking",
    "Investing",
    "Insurance",
    "Taxes",
    "Personal Finance"
]

STATE_FILE = "state.json"

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"category_index": 0, "used_titles": []}

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=4)

# ================= ওপেন রাউটার এআই (আর্টিকেল ও ৩টি এমসিকিউ) =================
def generate_blog_content(category, used_titles):
    prompt = f"""
    Act as a 'Financial Master'. Your task is to write a highly SEO-optimized, complete blog post in HTML format for a Google Blogger site.
    
    Category: {category}
    
    Instructions:
    1. Find a current trending topic in this category. The title must be highly engaging, unique, and NOT in this list: {used_titles}.
    2. Write a comprehensive blog post with real-world financial examples.
    3. Use multiple paragraphs, <h2> and <h3> tags. Keep wide spacing between paragraphs so Google Auto Ads can fit perfectly.
    4. Include a 'Meta Description' at the end.
    5. VERY IMPORTANT: At the very end of the article, you MUST create exactly 3 Multiple Choice Questions (MCQs) related to the topic.
    
    Format the output strictly as a JSON object with keys: "title", "content", "tags" (array of strings), "meta_description".
    """

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "meta-llama/llama-3-70b-instruct", 
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"}
    }
    
    print(f"[{category}] এর জন্য কন্টেন্ট তৈরি হচ্ছে...")
    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
    result = response.json()['choices'][0]['message']['content']
    return json.loads(result)

# ================= জেমিনি এআই (ছবি তৈরি) =================
def generate_gemini_image(title):
    print(f"জেমিনি এআই দিয়ে '{title}' এর জন্য ছবি তৈরি হচ্ছে...")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-001:predict?key={GEMINI_API_KEY}"
    
    payload = {
        "instances": [{"prompt": f"A highly professional, SEO-optimized blog cover image about financial mastery, trending topic: {title}. High quality, modern finance concept, without any text in the image."}],
        "parameters": {"sampleCount": 1}
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            image_data = response.json()
            base64_img = image_data['predictions'][0]['bytesBase64Encoded']
            return f"data:image/jpeg;base64,{base64_img}"
    except Exception as e:
        print(f"জেমিনি ইমেজ তৈরিতে সমস্যা: {e}")
    
    return "https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?w=800&q=80"

# ================= গুগল ব্লগার অটো-পোস্টিং =================
def post_to_blogger(blog_data, image_src, category):
    try:
        # এখানে কোনো জিমেইল বা পাসওয়ার্ড নেই, শুধু টোকেন দিয়ে ভেরিফাই হচ্ছে
        creds = Credentials(
            token=None,
            refresh_token=REFRESH_TOKEN,
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            token_uri="https://oauth2.googleapis.com/token"
        )
        
        service = build('blogger', 'v3', credentials=creds)
        title = blog_data['title']
        raw_content = blog_data['content']
        
        full_content = f'<div style="text-align: center;"><img src="{image_src}" alt="{title}" style="max-width: 100%; height: auto; border-radius: 8px;" /></div><br><br>' + raw_content
        
        labels = [category]
        if 'tags' in blog_data and isinstance(blog_data['tags'], list):
            labels.extend(blog_data['tags'])
            
        body = {
            "title": title,
            "content": full_content,
            "labels": labels
        }
        
        request = service.posts().insert(blogId=BLOG_ID, body=body, isDraft=False)
        response = request.execute()
        
        print(f"✅ সফলভাবে ব্লগারে পোস্ট হয়েছে: {response.get('url')}\n")
        return True
    except Exception as e:
        print(f"❌ ব্লগারে পোস্ট করতে সমস্যা হয়েছে: {e}\n")
        return False

# ================= মেইন ফাংশন =================
def main():
    state = load_state()
    category_index = state["category_index"]
    used_titles = state["used_titles"]
    
    # ধারাবাহিকভাবে ক্যাটাগরি পরিবর্তন করা হচ্ছে
    category = CATEGORIES[category_index % len(CATEGORIES)]
    print(f"--- বর্তমান ক্যাটাগরি: {category} ---")
    
    try:
        blog_data = generate_blog_content(category, used_titles)
        title = blog_data['title']
        
        if title in used_titles:
            print("এই টাইটেলটি আগেই পোস্ট করা হয়েছে। গিটহাব অ্যাকশনস পরবর্তী ঘণ্টায় নতুন চেষ্টা করবে।")
            return
            
        image_src = generate_gemini_image(title)
        
        is_success = post_to_blogger(blog_data, image_src, category)
        
        if is_success:
            state["used_titles"].append(title)
            state["category_index"] += 1 # পরবর্তী পোস্টের জন্য ক্যাটাগরি আপডেট
            save_state(state)
            print("✅ স্টেট আপডেট করা হয়েছে।")
            
    except Exception as e:
        print(f"⚠️ ত্রুটি দেখা দিয়েছে: {e}")

if __name__ == "__main__":
    main()

