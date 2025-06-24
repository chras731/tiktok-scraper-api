from utils import extract_timestamp, deduplicate_videos
from supabase_client import insert_videos

def mock_scrape_creator(handle, until_date):
    # TODO: Replace with real scraping logic
    return [
        {
            "url": f"https://www.tiktok.com/@{handle}/video/1234567890000000000",
            "date": "2024-01-02",
            "title": "Example Video",
            "description": "Test description",
            "creator": handle,
            "soundName": "Cool Song",
            "soundUrl": "https://tiktok.com/music",
            "Comments": 10,
            "likes": 100,
            "saves": 5,
            "shares": 2,
            "plays": 1000,
            "reposts": 0,
            "creatorTags": "",
            "tags": "#example"
        }
    ]

def onboard_creator(handle):
    videos = mock_scrape_creator(handle, until_date="2024-01-01")
    insert_videos(videos)
    return {"status": "onboarded", "count": len(videos)}

def refresh_creator(handle=None):
    if handle:
        videos = mock_scrape_creator(handle, until_date=None)
        new_videos = deduplicate_videos(videos)
        insert_videos(new_videos)
        return {"status": "refreshed", "count": len(new_videos)}
    else:
        return {"error": "Global refresh not implemented yet"}
