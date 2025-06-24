import json
import time
import re
from supabase import create_client, Client
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from tqdm import tqdm
from urllib.parse import urlparse
import os

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def extract_video_id(url):
    match = re.search(r'/video/(\d+)', url)
    return match.group(1) if match else None

def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.page_load_strategy = "eager"
    return webdriver.Chrome(options=chrome_options)

def scrape_metadata(driver, video_url):
    try:
        driver.get(video_url)
        time.sleep(5)

        soup = BeautifulSoup(driver.page_source, "html.parser")

        script_tag = soup.find("script", id="SIGI_STATE")
        if not script_tag:
            raise Exception("SIGI_STATE script tag not found")

        data = json.loads(script_tag.string)

        video_data = list(data["ItemModule"].values())[0]
        author_data = list(data["UserModule"]["users"].values())[0]

        return {
            "title": video_data.get("desc", ""),
            "description": video_data.get("desc", ""),
            "soundName": video_data.get("music", {}).get("title", ""),
            "soundUrl": video_data.get("music", {}).get("playUrl", ""),
            "comments": video_data.get("stats", {}).get("commentCount", 0),
            "likes": video_data.get("stats", {}).get("diggCount", 0),
            "saves": video_data.get("stats", {}).get("collectCount", 0),
            "shares": video_data.get("stats", {}).get("shareCount", 0),
            "plays": video_data.get("stats", {}).get("playCount", 0),
            "reposts": video_data.get("stats", {}).get("forwardCount", 0),
            "creatorTags": author_data.get("bioUrls", []),
            "tags": video_data.get("textExtra", []),
        }

    except Exception as e:
        print(f"Scrape error: {e}")
        return None

def run_metadata_jobs():
    print("🔍 Fetching pending jobs...\n")
    jobs_response = supabase.table("video_metadata_jobs").select("*").eq("status", "pending").execute()
    jobs = jobs_response.data or []

    print(f"📦 Found {len(jobs)} pending jobs.\n")

    driver = get_driver()

    for job in tqdm(jobs, desc="Processing Metadata Jobs"):
        video_url = job["video_url"]
        video_id = extract_video_id(video_url)

        if not video_id:
            print(f"❌ Invalid video URL: {video_url}")
            supabase.table("video_metadata_jobs").update({"status": "failed"}).eq("id", job["id"]).execute()
            continue

        metadata = scrape_metadata(driver, video_url)

        if not metadata:
            supabase.table("video_metadata_jobs").update({"status": "failed"}).eq("id", job["id"]).execute()
            continue

        video_record = supabase.table("videos").select("id").eq("id", video_id).execute()

        if not video_record.data:
            print(f"⚠️ No matching video in videos table for ID {video_id}")
            supabase.table("video_metadata_jobs").update({"status": "failed"}).eq("id", job["id"]).execute()
            continue

        print(f"✅ Updating video ID {video_id} with:\n{json.dumps(metadata, indent=2)}\n")

        try:
            supabase.table("videos").update(metadata).eq("id", video_id).execute()
            supabase.table("video_metadata_jobs").update({"status": "completed"}).eq("id", job["id"]).execute()
        except Exception as e:
            print(f"🔥 Failed to update video {video_id}: {e}")
            supabase.table("video_metadata_jobs").update({"status": "failed"}).eq("id", job["id"]).execute()

    driver.quit()
    print("✅ All jobs processed.\n")

if __name__ == "__main__":
    run_metadata_jobs()
