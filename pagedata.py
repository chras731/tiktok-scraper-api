import os
import time
from datetime import datetime, timezone
from dotenv import load_dotenv
from supabase_client import supabase
from utils import scroll_to_bottom
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

load_dotenv()

CUTOFF_DATE = datetime(2024, 1, 1, tzinfo=timezone.utc)


def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--user-data-dir=selenium")
    chrome_options.add_argument("--start-maximized")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)


def get_existing_video_ids():
    data = supabase.table("videos").select("id").execute()
    if data.data:
        return {entry["id"] for entry in data.data}
    return set()


def extract_videos(handle, existing_ids, is_refresh=False):
    driver = get_driver()
    driver.get(f"https://www.tiktok.com/@{handle}")
    scroll_to_bottom(driver)
    time.sleep(5)

    videos = []
    seen_count = 0
    video_elements = driver.find_elements(By.XPATH, '//a[contains(@href, "/video/")]')
    print(f"🔍 Found {len(video_elements)} video elements")

    for element in video_elements:
        try:
            href = element.get_attribute("href")
            if not href or "/video/" not in href:
                continue

            video_id = href.split("/video/")[-1].split("?")[0]
            if video_id in existing_ids:
                seen_count += 1
                if is_refresh and seen_count >= 5:
                    print("🚧 Detected 5 existing videos in a row. Stopping refresh.")
                    break
                continue

            timestamp = get_video_timestamp(video_id)
            if timestamp:
                print(f"✅ Video ID: {video_id}, Timestamp: {timestamp.isoformat()}")

                if not is_refresh and timestamp < CUTOFF_DATE:
                    print("🛑 Hit cutoff date.")
                    break

                videos.append({
                    "id": video_id,
                    "creator_handle": handle,
                    "url": href,
                    "date": timestamp.isoformat(),
                    "scraped_at": datetime.now(timezone.utc).isoformat()
                })
        except Exception as e:
            print(f"⚠️ Error extracting video info: {e}")

    driver.quit()
    return videos


def get_video_timestamp(video_id):
    try:
        timestamp_part = int(video_id) >> 32
        return datetime.fromtimestamp(timestamp_part, tz=timezone.utc)
    except Exception as e:
        print(f"⚠️ Could not parse timestamp from video_id {video_id}: {e}")
        return None


def onboard_creators(handles):
    existing_ids = get_existing_video_ids()
    for handle in handles:
        print(f"🚀 Onboarding @{handle}")
        videos = extract_videos(handle, existing_ids, is_refresh=False)
        for video in videos:
            supabase.table("videos").insert(video).execute()
            print(f"⬆️ Uploaded {video['url']}")


def refresh_creators(handles):
    existing_ids = get_existing_video_ids()
    for handle in handles:
        print(f"🔄 Refreshing @{handle}")
        videos = extract_videos(handle, existing_ids, is_refresh=True)
        for video in videos:
            supabase.table("videos").insert(video).execute()
            print(f"⬆️ Uploaded {video['url']}")


def main():
    print("Choose an option:")
    print("1: Onboard Creators")
    print("2: Refresh Creators")
    choice = input("Enter 1 or 2: ")

    handles = input("Enter TikTok handles separated by commas: ").split(",")
    handles = [h.strip().lstrip("@") for h in handles if h.strip()]

    if choice == "1":
        onboard_creators(handles)
    elif choice == "2":
        refresh_creators(handles)
    else:
        print("Invalid choice.")


if __name__ == "__main__":
    main()
