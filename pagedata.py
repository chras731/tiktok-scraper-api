import os
import time
import json
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from supabase import create_client, Client
from tqdm import tqdm
from dotenv import load_dotenv

# Load Supabase credentials from environment
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Set up Selenium
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

def scrape_tiktok_text(url):
    try:
        driver.get(url)
        time.sleep(5)
        soup = BeautifulSoup(driver.page_source, "lxml")

        finder = json.loads(soup.find("script", id="__UNIVERSAL_DATA_FOR_REHYDRATION__").string)
        content = finder['__DEFAULT_SCOPE__']['webapp.video-detail']['itemInfo']['itemStruct']

        title = soup.find("meta", property="og:title")
        title_text = title['content'] if title else "No title found"
        description = content.get('desc', "")

        audio = content.get('music', {})
        audio_name = audio.get('title', "")
        audio_url = audio.get('playUrl', "")

        author = content.get('author', {}).get('uniqueId', "")

        stats = content.get('statsV2', {})
        comments = stats.get('commentCount', 0)
        likes = stats.get('diggCount', 0)
        saved = stats.get('collectCount', 0)
        shared = stats.get('shareCount', 0)
        playCount = stats.get('playCount', 0)
        repostCount = stats.get('repostCount', 0)

        tags_meta = soup.find("meta", attrs={'name': 'keywords'})
        tags = [i.strip() for i in tags_meta['content'].split(",")] if tags_meta else []

        creator_keywords = [i['keyword'].replace("-", " ") for i in content.get('keywordTags', [])]

        return {
            "title": title_text,
            "description": description,
            "soundName": audio_name,
            "soundUrl": audio_url,
            "comments": comments,
            "likes": likes,
            "saves": saved,
            "shares": shared,
            "plays": playCount,
            "reposts": repostCount,
            "creatorTags": creator_keywords,
            "tags": tags
        }
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

def run_metadata_jobs():
    print("🔍 Fetching pending jobs...")
    response = supabase.table("video_metadata_jobs").select("*").eq("status", "pending").limit(10).execute()
    jobs = response.data

    print(f"📦 Found {len(jobs)} pending jobs.")
    for job in tqdm(jobs, desc="Processing Metadata Jobs"):
        video_id = job["id"]
        video_url = job["video_url"]

        metadata = scrape_tiktok_text(video_url)
        if metadata:
            # Update videos table
            supabase.table("videos").update({
                "title": metadata["title"],
                "description": metadata["description"],
                "soundName": metadata["soundName"],
                "soundUrl": metadata["soundUrl"],
                "comments": metadata["comments"],
                "likes": metadata["likes"],
                "saves": metadata["saves"],
                "shares": metadata["shares"],
                "plays": metadata["plays"],
                "reposts": metadata["reposts"],
                "creatorTags": metadata["creatorTags"],
                "tags": metadata["tags"]
            }).eq("url", video_url).execute()

            # Mark job as complete
            supabase.table("video_metadata_jobs").update({
                "status": "complete"
            }).eq("id", video_id).execute()
        else:
            # Mark job as failed
            supabase.table("video_metadata_jobs").update({
                "status": "failed"
            }).eq("id", video_id).execute()

    print("✅ All jobs processed.")

if __name__ == "__main__":
    run_metadata_jobs()
    driver.quit()
