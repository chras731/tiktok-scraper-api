import json
import time
from supabase import create_client, Client
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tqdm import tqdm
import re

import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def extract_video_data_from_html(html):
    # Extract the SIGI_STATE JSON object using regex
    match = re.search(r'<script id="SIGI_STATE"[^>]*>(.*?)</script>', html)
    if not match:
        raise ValueError("SIGI_STATE script tag not found")

    json_text = match.group(1)
    data = json.loads(json_text)

    try:
        item_module = data["ItemModule"]
        for video_id, video_data in item_module.items():
            return {
                "video_id": video_id,
                "title": video_data.get("title"),
                "description": video_data.get("desc"),
                "soundName": video_data.get("music", {}).get("title"),
                "soundUrl": video_data.get("music", {}).get("playUrl"),
                "comments": video_data.get("stats", {}).get("commentCount"),
                "likes": video_data.get("stats", {}).get("diggCount"),
                "saves": video_data.get("stats", {}).get("collectCount"),
                "shares": video_data.get("stats", {}).get("shareCount"),
                "plays": video_data.get("stats", {}).get("playCount"),
                "reposts": video_data.get("stats", {}).get("forwardCount"),
                "creatorTags": video_data.get("author", {}).get("uniqueId"),
                "tags": [tag.get("tag") for tag in video_data.get("textExtra", []) if "tag" in tag],
            }
    except Exception as e:
        raise ValueError("Failed to parse video data: " + str(e))

def run_metadata_jobs():
    print("🔍 Fetching pending jobs...\n")
    jobs = supabase.table("video_metadata_jobs").select("*").eq("status", "pending").execute().data
    print(f"📦 Found {len(jobs)} pending jobs.\n")

    if not jobs:
        return

    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # Uncomment this for debugging locally
    # options.add_argument("--headless=new")

    driver = webdriver.Chrome(options=options)

    for job in tqdm(jobs, desc="Processing Metadata Jobs"):
        job_id = job["id"]
        video_url = job["video_url"]

        try:
            driver.get(video_url)

            # Wait until the SIGI_STATE script is present
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, '//script[@id="SIGI_STATE"]'))
            )
            time.sleep(1)  # Add buffer in case script is still loading

            html = driver.page_source
            video_data = extract_video_data_from_html(html)

            update_payload = {k: v for k, v in video_data.items() if v is not None}
            supabase.table("videos").update(update_payload).eq("id", job_id).execute()
            supabase.table("video_metadata_jobs").update({"status": "completed"}).eq("id", job_id).execute()

        except Exception as e:
            print(f"\nError processing {video_url}: {e}\n")
            supabase.table("video_metadata_jobs").update({"status": "failed"}).eq("id", job_id).execute()

    driver.quit()
    print("\n✅ All jobs processed.\n")
