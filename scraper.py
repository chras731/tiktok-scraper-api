import re
import time
import uuid
from datetime import datetime
from playwright.sync_api import sync_playwright
from supabase_client import get_supabase_client

def extract_video_id(url):
    match = re.search(r"/video/(\d+)", url)
    return match.group(1) if match else None

def extract_date_from_id(video_id):
    try:
        timestamp = int(video_id) >> 32
        return datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d")
    except:
        return None

def scrape_creator_videos(handle, until_date="2024-01-01"):
    print(f"Scraping TikTok profile for: {handle}")
    supabase = get_supabase_client()
    until_timestamp = datetime.strptime(until_date, "%Y-%m-%d")
    videos = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        url = f"https://www.tiktok.com/@{handle}"
        page.goto(url, timeout=60000)
        page.wait_for_timeout(3000)

        last_height = 0
        seen_urls = set()

        while True:
            cards = page.query_selector_all("article")
            for card in cards:
                try:
                    href = card.query_selector("a")
                    if href is None:
                        continue

                    video_url = href.get_attribute("href")
                    if video_url in seen_urls:
                        continue

                    seen_urls.add(video_url)
                    video_id = extract_video_id(video_url)
                    if not video_id:
                        continue

                    video_date = extract_date_from_id(video_id)
                    if not video_date:
                        continue

                    if datetime.strptime(video_date, "%Y-%m-%d") < until_timestamp:
                        browser.close()
                        return videos

                    video = {
                        "id": str(uuid.uuid4()),
                        "url": video_url,
                        "date": video_date,
                        "title": card.inner_text(),
                        "description": card.inner_text(),
                        "creator": handle,
                        "soundName": None,
                        "soundUrl": None,
                        "Comments": 0,
                        "likes": 0,
                        "saves": 0,
                        "shares": 0,
                        "plays": 0,
                        "reposts": 0,
                        "creatorTags": "",
                        "tags": ""
                    }
                    videos.append(video)

                except Exception as e:
                    print(f"Error parsing video: {e}")

            page.mouse.wheel(0, 2000)
            page.wait_for_timeout(2000)
            new_height = page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        browser.close()
    return videos

def onboard_creator(handle):
    videos = scrape_creator_videos(handle, until_date="2024-01-01")
    print("VIDEOS TO INSERT:", videos)
    supabase = get_supabase_client()

    creator_record = {
        "id": str(uuid.uuid4()),
        "handle": handle,
        "onboarded_at": datetime.utcnow().isoformat(),
        "last_checked": datetime.utcnow().isoformat()
    }
    supabase.table("creators").insert(creator_record).execute()
    supabase.table("videos").insert(videos).execute()

    return {"status": "onboarded", "count": len(videos)}

def refresh_creator(handle=None):
    supabase = get_supabase_client()
    if handle:
        existing = supabase.table("videos").select("url").eq("creator", handle).execute()
        existing_urls = set(row["url"] for row in existing.data)
        new_videos = scrape_creator_videos(handle, until_date=None)
        deduped = [v for v in new_videos if v["url"] not in existing_urls]

        supabase.table("videos").insert(deduped).execute()
        supabase.table("creators").update({"last_checked": datetime.utcnow().isoformat()}).eq("handle", handle).execute()

        return {"status": "refreshed", "count": len(deduped)}
    else:
        return {"error": "Global refresh not implemented yet"}
