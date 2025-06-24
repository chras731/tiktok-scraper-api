import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from supabase_client import supabase
from datetime import datetime

def load_cookies(driver, path='cookies.json'):
    try:
        with open(path, 'r') as f:
            cookies = json.load(f)
        for cookie in cookies:
            if 'sameSite' in cookie and cookie['sameSite'] == 'None':
                cookie['sameSite'] = 'Strict'
            driver.add_cookie(cookie)
        print("Cookies loaded successfully.")
    except Exception as e:
        print(f"Error loading cookies: {e}")
        raise

def scrape_creator_videos(handle):
    print(f"Scraping TikTok profile for: {handle}")

    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=chrome_options)
    driver.get("https://www.tiktok.com/")
    time.sleep(5)

    try:
        load_cookies(driver)
        driver.refresh()
        time.sleep(5)
    except Exception as e:
        print(f"Failed to load cookies: {e}")
        driver.quit()
        return []

    profile_url = f"https://www.tiktok.com/@{handle}"
    driver.get(profile_url)
    time.sleep(5)

    SCROLL_PAUSE_TIME = 2
    scroll_attempts = 0
    last_height = driver.execute_script("return document.body.scrollHeight")

    while scroll_attempts < 10:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE_TIME)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
        scroll_attempts += 1

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    anchors = soup.find_all('a', href=True)
    video_urls = list(set([a['href'] for a in anchors if '/video/' in a['href']]))

    print(f"Found {len(video_urls)} videos.")

    videos = []
    for url in video_urls:
        try:
            video_id = url.split('/video/')[1].split('?')[0]
            timestamp = int(video_id) >> 32
            date_posted = datetime.utcfromtimestamp(timestamp).isoformat()

            videos.append({
                "creator_handle": handle,
                "url": url,
                "video_id": video_id,
                "date": date_posted
            })
        except Exception as e:
            print(f"Error parsing video URL {url}: {e}")

    driver.quit()
    return videos

def onboard_creator(handle):
    videos = scrape_creator_videos(handle)
    if videos:
        supabase.table("videos").insert(videos).execute()
    return {"status": "onboarded", "count": len(videos)}

def refresh_creator(handle):
    existing_ids = supabase.table("videos").select("video_id").eq("creator_handle", handle).execute()
    existing_ids = {row["video_id"] for row in existing_ids.data}
    videos = scrape_creator_videos(handle)
    new_videos = [v for v in videos if v["video_id"] not in existing_ids]
    if new_videos:
        supabase.table("videos").insert(new_videos).execute()
    return {"status": "refreshed", "new_count": len(new_videos)}
