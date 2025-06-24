import json
import re
import time
import os
import requests
from bs4 import BeautifulSoup
from supabase import create_client, Client
from tqdm import tqdm

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
}

def extract_video_id(url):
    match = re.search(r"/video/(\d+)", url)
    return match.group(1) if match else None

def scrape_metadata(video_url):
    try:
        res = requests.get(video_url, headers=headers, timeout=10)
        if res.status_code != 200:
            raise Exception(f"Failed to load page: {res.status_code}")

        soup = BeautifulSoup(res.text, "html.parser")
        script_tag = soup.find("script", id="SIGI_STATE")
        if not script_tag:
            raise Exception("SIGI_STATE script tag not found")

        data = json.loads(script_tag.string)
        video_data = list(data["ItemModule"].values())[0]
        author_data = list(data["UserModule"]["users"].values())[0]

        return {
            "title": video_data.get("desc", ""),
            "description": video_data.get("desc", ""),
            "createTime": video_data.get("createTime", None),
            "video_id": video_data.get("id", None),
            "author": author_data.get("uniqueId", ""),
            "music": video_data.get("music", {}).get("title", ""),
            "plays": video_data.get("stats", {}).get("playCount", 0),
            "likes": video_data.get("stats", {}).get("diggCount", 0),
            "comments": video_data.get("stats", {}).get("commentCount", 0),
            "shares": video_data.get("stats", {}).get("shareCount", 0),
            "video_url": video_url
        }
    except Exception as e:
        print(f"Scrape error for {video_url}: {e}")
        return None

def process_pending_jobs():
    print("\n🔍 Fetching pending jobs from Supabase...")
    jobs = supabase.table("videos").select("id, video_url").is_("title", None).limit(20).execute()
    pending = jobs.data or []

    print(f"\n📦 Found {len(pending)} pending jobs.\n")
    
    for job in tqdm(pending, desc="Processing Metadata Jobs"):
        metadata = scrape_metadata(job["video_url"])
        if metadata:
            supabase.table("videos").update(metadata).eq("id", job["id"]).execute()

    print("\n✅ All jobs processed.\n")

if __name__ == "__main__":
    process_pending_jobs()
