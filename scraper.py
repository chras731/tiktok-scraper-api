# scraper.py
import os
import re
import time
import uuid
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from supabase_client import get_supabase_client

def extract_timestamp_from_id(video_id: str):
    try:
        binary = bin(int(video_id))[2:].zfill(64)
        timestamp_bin = binary[:32]
        return datetime.utcfromtimestamp(int(timestamp_bin, 2)).strftime('%Y-%m-%d')
    except Exception:
        return None

def parse_hashtags(text):
    return " ".join(re.findall(r"#\w+", text))

def scrape_creator_videos(handle, until_date="2024-01-01"):
    print(f"Scraping TikTok profile for: {handle}")
    base_url = f"https://www.tiktok.com/@{handle}"
    videos = []

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.get(base_url)
        time.sleep(5)

        posts = driver.find_elements(By.CSS_SELECTOR, "div[data-e2e='user-post-item']")
        for post in posts:
            try:
                link_el = post.find_element(By.TAG_NAME, "a")
                href = link_el.get_attribute("href")
                if not href or "/video/" not in href:
                    continue

                video_id = re.search(r"/video/(\d+)", href).group(1)
                video_date = extract_timestamp_from_id(video_id)
                if not video_date or video_date < until_date:
                    break

                desc = post.text
                tags = parse_hashtags(desc)

                videos.append({
                    "id": str(uuid.uuid4()),
                    "url": href,
                    "date": video_date,
                    "title": "",
                    "description": desc,
                    "creator": handle,
                    "soundName": "",
                    "soundUrl": "",
                    "Comments": 0,
                    "likes": 0,
                    "saves": 0,
                    "shares": 0,
                    "plays": 0,
                    "reposts": 0,
                    "creatorTags": "",
                    "tags": tags
                })
            except Exception as e:
                print(f"Error parsing post: {e}")
                continue
    finally:
        driver.quit()
    return videos

async def onboard_creator(handle):
    supabase = get_supabase_client()
    creator_id = str(uuid.uuid4())
    await supabase.table("creators").insert({
        "id": creator_id,
        "handle": handle,
        "onboarded_at": datetime.utcnow().isoformat(),
        "last_checked": datetime.utcnow().isoformat()
    }).execute()

    videos = scrape_creator_videos(handle)
    for v in videos:
        v["creator_id"] = creator_id
    await supabase.table("videos").insert(videos).execute()
    return {"status": "onboarded", "count": len(videos)}

async def refresh_creator(handle):
    supabase = get_supabase_client()
    result = await supabase.table("creators").select("id").eq("handle", handle).execute()
    if not result.data:
        return {"error": "Creator not found"}

    creator_id = result.data[0]["id"]
    videos = scrape_creator_videos(handle, until_date=None)

    existing = await supabase.table("videos").select("url").eq("creator_id", creator_id).execute()
    existing_urls = {v["url"] for v in existing.data}

    new_videos = [v for v in videos if v["url"] not in existing_urls]
    for v in new_videos:
        v["creator_id"] = creator_id

    await supabase.table("videos").insert(new_videos).execute()
    return {"status": "refreshed", "count": len(new_videos)}
