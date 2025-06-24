
import os
import re
import uuid
import asyncio
from datetime import datetime
from supabase_client import get_supabase_client
from playwright.async_api import async_playwright

def extract_timestamp_from_id(video_id: str):
    try:
        binary = bin(int(video_id))[2:].zfill(64)
        timestamp_bin = binary[:32]
        return datetime.utcfromtimestamp(int(timestamp_bin, 2)).strftime('%Y-%m-%d')
    except Exception:
        return None

def parse_hashtags(text):
    return " ".join(re.findall(r"#\w+", text))

async def scrape_creator_videos(handle, until_date="2024-01-01"):
    print(f"Scraping TikTok profile for: {handle}")
    base_url = f"https://www.tiktok.com/@{handle}"
    videos = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(base_url, timeout=60000)
        await page.wait_for_selector("div[data-e2e='user-post-item']", timeout=10000)

        posts = await page.query_selector_all("div[data-e2e='user-post-item']")
        for post in posts:
            link_el = await post.query_selector("a")
            href = await link_el.get_attribute("href")
            if not href:
                continue
            match = re.search(r"/video/(\d+)", href)
            if not match:
                continue
            video_id = match.group(1)
            video_date = extract_timestamp_from_id(video_id)
            if not video_date or video_date < until_date:
                break

            desc = await post.inner_text()
            tags = parse_hashtags(desc)

            videos.append({
                "id": str(uuid.uuid4()),
                "url": f"https://www.tiktok.com{href}",
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

        await browser.close()
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

    videos = await scrape_creator_videos(handle)
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
    videos = await scrape_creator_videos(handle, until_date=None)

    existing = await supabase.table("videos").select("url").eq("creator_id", creator_id).execute()
    existing_urls = {v["url"] for v in existing.data}

    new_videos = [v for v in videos if v["url"] not in existing_urls]
    for v in new_videos:
        v["creator_id"] = creator_id

    await supabase.table("videos").insert(new_videos).execute()
    return {"status": "refreshed", "count": len(new_videos)}
