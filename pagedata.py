
import os
import time
from tqdm import tqdm
from supabase import create_client, Client
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, WebDriverException
import json

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def setup_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920x1080")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def scrape_tiktok_text(url):
    try:
        driver = setup_driver()
        driver.get(url)
        time.sleep(5)  # Let JS render
        data = {}

        # Title and description
        try:
            description_elem = driver.find_element(By.XPATH, '//h1[contains(@data-e2e,"video-desc")]')
            data['description'] = description_elem.text
        except:
            data['description'] = None

        try:
            title_elem = driver.find_element(By.XPATH, '//title')
            data['title'] = title_elem.get_attribute("innerText")
        except:
            data['title'] = None

        # Sound name
        try:
            sound_elem = driver.find_element(By.XPATH, '//a[contains(@data-e2e,"browse-sound")]')
            data['soundName'] = sound_elem.text
            data['soundUrl'] = sound_elem.get_attribute('href')
        except:
            data['soundName'] = None
            data['soundUrl'] = None

        # Stats
        try:
            stats = driver.find_elements(By.XPATH, '//strong[contains(@data-e2e,"like-count") or contains(@data-e2e,"comment-count") or contains(@data-e2e,"share-count")]')
            if len(stats) >= 3:
                data['likes'] = int(stats[0].text.replace(',', ''))
                data['comments'] = int(stats[1].text.replace(',', ''))
                data['shares'] = int(stats[2].text.replace(',', ''))
            else:
                data['likes'] = data['comments'] = data['shares'] = None
        except:
            data['likes'] = data['comments'] = data['shares'] = None

        # Reposts and saves not accessible from public page currently
        data['reposts'] = None
        data['saves'] = None
        data['plays'] = None  # Not publicly available
        data['tags'] = None
        data['creatorTags'] = None

        driver.quit()
        return data
    except Exception as e:
        print(f"Scrape error: {e}")
        return None

def run_metadata_jobs():
    print("🔍 Fetching pending jobs...")
    jobs = supabase.table("video_metadata_jobs").select("*").eq("status", "pending").limit(10).execute().data
    print(f"📦 Found {len(jobs)} pending jobs.")
    for job in tqdm(jobs, desc="Processing Metadata Jobs"):
        video_url = job["video_url"]
        video_id = job["id"]
        try:
            metadata = scrape_tiktok_text(video_url)
            if metadata:
                supabase.table("videos").update(metadata).eq("url", video_url).execute()
                supabase.table("video_metadata_jobs").update({"status": "completed"}).eq("id", video_id).execute()
            else:
                supabase.table("video_metadata_jobs").update({"status": "failed"}).eq("id", video_id).execute()
        except Exception as e:
            print(f"Error processing {video_url}: {e}")
            supabase.table("video_metadata_jobs").update({"status": "failed"}).eq("id", video_id).execute()

if __name__ == "__main__":
    run_metadata_jobs()
