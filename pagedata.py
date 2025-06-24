import os
import time
import re
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from supabase import create_client, Client

# Set up Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_pending_jobs():
    response = supabase.table("video_metadata_jobs").select("id, url").eq("status", "pending").execute()
    return response.data


def update_video_metadata(video_url, metadata):
    supabase.table("videos").update(metadata).eq("url", video_url).execute()


def mark_job_complete(video_url):
    supabase.table("video_metadata_jobs").update({"status": "complete"}).eq("url", video_url).execute()


def scrape_video_metadata(video_url):
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        driver.set_page_load_timeout(15)
        driver.get(video_url)
        time.sleep(5)

        soup = BeautifulSoup(driver.page_source, "html.parser")

        title = soup.title.string if soup.title else ""
        description = ""
        author = ""
        audio_name = ""
        audio_url = ""
        comments = likes = saved = shared = play_count = repost_count = 0
        creator_keywords = ""
        tags_list = []

        scripts = soup.find_all("script")
        for script in scripts:
            if script.string and "playCount" in script.string:
                json_text = script.string

                play_count_match = re.search(r'"playCount":(\d+)', json_text)
                like_count_match = re.search(r'"diggCount":(\d+)', json_text)
                comment_count_match = re.search(r'"commentCount":(\d+)', json_text)
                share_count_match = re.search(r'"shareCount":(\d+)', json_text)
                save_count_match = re.search(r'"collectCount":(\d+)', json_text)
                repost_count_match = re.search(r'"repostCount":(\d+)', json_text)
                audio_name_match = re.search(r'"music":\{"title":"(.*?)"', json_text)
                audio_url_match = re.search(r'"playUrl":"(.*?)"', json_text)
                author_match = re.search(r'"nickname":"(.*?)"', json_text)
                desc_match = re.search(r'"desc":"(.*?)"', json_text)
                tag_matches = re.findall(r'"hashtag_name":"(.*?)"', json_text)
                creator_keywords_match = re.search(r'"uniqueId":"(.*?)"', json_text)

                play_count = int(play_count_match.group(1)) if play_count_match else 0
                likes = int(like_count_match.group(1)) if like_count_match else 0
                comments = int(comment_count_match.group(1)) if comment_count_match else 0
                shared = int(share_count_match.group(1)) if share_count_match else 0
                saved = int(save_count_match.group(1)) if save_count_match else 0
                repost_count = int(repost_count_match.group(1)) if repost_count_match else 0
                audio_name = audio_name_match.group(1) if audio_name_match else ""
                audio_url = audio_url_match.group(1).replace("\\u0026", "&") if audio_url_match else ""
                author = author_match.group(1) if author_match else ""
                description = desc_match.group(1) if desc_match else ""
                tags_list = tag_matches
                creator_keywords = creator_keywords_match.group(1) if creator_keywords_match else ""

                break

        return {
            "title": title,
            "description": description,
            "soundName": audio_name,
            "soundUrl": audio_url,
            "Comments": comments,
            "likes": likes,
            "saves": saved,
            "shares": shared,
            "plays": play_count,
            "reposts": repost_count,
            "creatorTags": creator_keywords,
            "tags": tags_list
        }

    finally:
        driver.quit()


def run_metadata_jobs():
    jobs = get_pending_jobs()
    print(f"📦 Found {len(jobs)} video metadata jobs")

    for job in jobs:
        video_url = job["url"]
        print(f"🔍 Processing: {video_url}")
        metadata = scrape_video_metadata(video_url)
        update_video_metadata(video_url, metadata)
        print(f"✅ Scraped metadata for: {video_url}")
        
        if metadata.get("plays") and metadata["plays"] > 0:
            mark_job_complete(video_url)
            print(f"🏁 Marked job as complete for: {video_url}")
        else:
            print(f"⚠️ Skipped marking complete (missing play count) for: {video_url}")


if __name__ == "__main__":
    run_metadata_jobs()
