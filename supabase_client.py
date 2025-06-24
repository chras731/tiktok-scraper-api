import os
from supabase import create_client, Client

def get_supabase_client() -> Client:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    print("URL loaded at runtime:", url)
    print("KEY present?:", bool(key))
    return create_client(url, key)


def insert_videos(video_data):
    response = supabase.table("videos").insert(video_data).execute()
    return response
