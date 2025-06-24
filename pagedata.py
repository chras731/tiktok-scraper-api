import time
from supabase import create_client, Client
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from tqdm import tqdm
from datetime import datetime
import uuid
import os

# Supabase setup
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def scrape_video_metadata(url):
    """Extracts metadata from a TikTok video URL using Selenium."""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)

    driver.get(url)
    time.sleep(5)

    try:
        description = driver.find_element(By.XPATH, '//h1').text
    except:
        description = None

    try:
        sound = driver.find_element(By.XPATH, '//span[contains(text(),"original sound") or contains(text(),"🎵")]').text
    except:
        sound = None

    try:
        stats_elements = driver.find_elements(By.XPATH, '//strong')
        likes = int(stats_elements[0].text.replace(',', '')) if len(stats_elements) > 0 else None
        comments = int(stats_elements[1].text.replace(',', '')) if len(stats_elements) > 1 else None
        shares = int(stats_elements[2].text.replace(',', '')) if len(stats_elements) > 2 else None
    except:
        likes, comments, shares = None, None, None

    driver.quit()
    return {
        "description": description,
        "sound": sound,
        "likes": likes,
        "comments": comments,
        "shares": shares
    }

def run_metadata_jobs():
    # Fetch up to 10 pending jobs
    response = supabase.table("video_metadata_jobs").select("*").eq("status", "pending").limit(10).execute()
    jobs = response.data

    if not jobs:
        print("No pending metadata jobs found.")
        return

    for job in tqdm(jobs, desc="Processing Metadata Jobs"):
        video_url = job["video_url"]
        video_id = job["video_id"]
        job_id = job["id"]

        try:
            # Update job to in_progress
            supabase.table("video_metadata_jobs").update({
                "status": "in_progress",
                "started_at": datetime.utcnow().isoformat()
            }).eq("id", job_id).execute()

            metadata = scrape_video_metadata(video_url)

            # Update videos table with new metadata
            supabase.table("videos").update(metadata).eq("id", video_id).execute()

            # Mark job complete
            supabase.table("video_metadata_jobs").update({
                "status": "complete",
                "completed_at": datetime.utcnow().isoformat()
            }).eq("id", job_id).execute()

        except Exception as e:
            print(f"Failed job {job_id}: {e}")
            supabase.table("video_metadata_jobs").update({
                "status": "failed"
            }).eq("id", job_id).execute()

if __name__ == "__main__":
    run_metadata_jobs()
