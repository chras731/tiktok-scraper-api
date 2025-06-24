from utils import extract_timestamp, deduplicate_videos
from supabase_client import get_supabase_client

def mock_scrape_creator(handle, until_date):
    # TODO: Replace with real scraping logic
    return [
        {
            "url": f"https://www.tiktok.com/@{handle}/video/1234567890000000000",
            "date": "2024-01-02",
            "title": "Example Video",
            "description": "Test description",
            "creator": handle,
            "sound_name": "Cool Song",
            "sound_url": "https://tiktok.com/music",
            "comments": 10,
            "likes": 100,
            "saves": 5,
            "shares": 2,
            "plays": 1000,
            "reposts": 0,
            "creator_tags": "",
            "tags": "#example"
        }
    ]

def onboard_creator(handle):
    videos = mock_scrape_creator(handle, until_date="2024-01-01")
    print("VIDEOS TO INSERT:", videos)
    supabase = get_supabase_client()
    supabase.table("videos").insert(videos).execute()
    return {"status": "onboarded", "count": len(videos)}

def refresh_creator(handle=None):
    if handle:
        videos = mock_scrape_creator(handle, until_date=None)
        new_videos = deduplicate_videos(videos)
        supabase = get_supabase_client()
        supabase.table("videos").insert(new_videos).execute()
        return {"status": "refreshed", "count": len(new_videos)}
    else:
        return {"error": "Global refresh not implemented yet"}
