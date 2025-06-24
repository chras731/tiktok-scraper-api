import requests
from bs4 import BeautifulSoup
from supabase import create_client, Client
import os
from datetime import datetime
import time

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def extract_video_data(url: str) -> dict:
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"
        }
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')

        scripts = soup.find_all("script")
        data_script = next(
            (script for script in scripts if "window.__INIT_PROPS__" in script.text),
            None
        )

        if not data_script:
            print(f"No data script found for {url}")
            return {}

        # Isolate JSON from script
        text = data_script.text
        json_start = text.find("{")
        json_end = text.rfind("}") + 1
        raw_json = text[json_start:json_end]

        import json
        data = json.loads(raw_json)
        video_data = next(iter(data.values()))

        item_info = video_data.get("video", {}).get("itemInfos", {})
        music_info = video_data.get("music", {})
        author_info = video_data.get("author", {})

        return {
            "url": url,
            "title": item_info.get("text"),
            "date": datetime.fromtimestamp(item_info.get("createTime", 0)).isoformat(),
            "playCount": item_info.get("playCount"),
            "commentCount": item_info.get("commentCount"),
            "shareCount": item_info.get("shareCount"),
            "likeCount": item_info.get("diggCount"),
            "musicTitle": music_info.get("title"),
            "musicAuthor": music_info.get("authorName"),
            "musicId": music_info.get("musicId"),
            "creator": author_info.get("uniqueId"),
        }

    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return {}


def run_metadata_jobs():
    jobs = supabase.table("video_metadata_jobs").select("*").eq("status", "pending").execute()
    for job in jobs.data:
        url = job["url"]
        print(f"Processing: {url}")
        data = extract_video_data(url)

        if data:
            # Match column names to Supabase schema
            supabase.table("videos").insert({
                "url": data["url"],
                "title": data["title"],
                "date": data["date"],
                "play_count": data["playCount"],
                "comment_count": data["commentCount"],
                "share_count": data["shareCount"],
                "like_count": data["likeCount"],
                "music_title": data["musicTitle"],
                "music_author": data["musicAuthor"],
                "music_id": data["musicId"],
                "creator_handle": data["creator"]
            }).execute()

        # Mark job as completed
        supabase.table("video_metadata_jobs").update({
            "status": "completed"
        }).eq("id", job["id"]).execute()
        time.sleep(2)  # avoid rate limits


if __name__ == "__main__":
    run_metadata_jobs()
