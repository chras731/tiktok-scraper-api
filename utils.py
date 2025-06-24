def extract_timestamp(video_id: str):
    try:
        tagNo = int(video_id)
        ts = tagNo >> 32
        return ts
    except:
        return None

def deduplicate_videos(videos):
    # TODO: compare against existing Supabase entries
    return videos
