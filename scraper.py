from datetime import datetime
import re
import uuid
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

def extract_video_timestamp(video_id: str) -> str:
    try:
        timestamp = int(video_id) >> 32
        return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d')
    except Exception:
        return None

def extract_hashtags(description: str) -> str:
    return ' '.join(re.findall(r"#\w+", description)) if description else ""

def scrape_creator_profile(handle: str, until_date="2024-01-01"):
    video_data = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f"https://www.tiktok.com/@{handle}")

        # Scroll to load more videos
        previous_height = 0
        while True:
            page.mouse.wheel(0, 2000)
            page.wait_for_timeout(2000)
            current_height = page.evaluate("document.body.scrollHeight")
            if current_height == previous_height:
                break
            previous_height = current_height

        soup = BeautifulSoup(page.content(), "html.parser")
        browser.close()

        video_links = soup.find_all("a", href=re.compile(r"/@[^/]+/video/\d+"))

        seen = set()
        for link in video_links:
            href = link.get("href")
            if href in seen:
                continue
            seen.add(href)

            match = re.search(r"/@([^/]+)/video/(\d+)", href)
            if not match:
                continue

            creator, video_id = match.groups()
            date = extract_video_timestamp(video_id)
            if not date or date < until_date:
                break

            video_url = f"https://www.tiktok.com{href}"
            metadata = {
                "id": str(uuid.uuid4()),
                "url": video_url,
                "date": date,
                "title": "",  # TikTok doesn't provide titles directly
                "description": "",
                "creator": creator,
                "soundName": "",
                "soundUrl": "",
                "Comments": 0,
                "likes": 0,
                "saves": 0,
                "shares": 0,
                "plays": 0,
                "reposts": 0,
                "creatorTags": "",
                "tags": extract_hashtags(""),
            }
            video_data.append(metadata)

    return video_data
