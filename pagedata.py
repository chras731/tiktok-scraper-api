import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time
import json
import os
from webdriver_manager.chrome import ChromeDriverManager
from tqdm import tqdm

# Set up Selenium WebDriver
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run in headless mode
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")

# Update with your ChromeDriver path
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# Function that returns URL data
def scrape_tiktok_text(url):
    driver.get(url)
    time.sleep(5)  # Wait for page to load

    soup = BeautifulSoup(driver.page_source, "lxml")

    finder = json.loads(soup.find("script", id="__UNIVERSAL_DATA_FOR_REHYDRATION__").string)
    content = finder['__DEFAULT_SCOPE__']['webapp.video-detail']['itemInfo']['itemStruct']

    title = soup.find("meta", property="og:title")
    title_text = title['content'] if title else "No title found"
    description = content['desc'] if 'desc' in content else ""
    
    author = ""
    if 'author' in content:
        author = content['author']['uniqueId'] if 'uniqueId' in content['author'] else ""
    
    audio_name = ""
    audio_url = ""
    if 'music' in content:
        audio_name = content['music']['title'] if 'title' in content['music'] else ""
        audio_url = content['music']['playUrl'] if 'playUrl' in content['music'] else ""

    comments = ""
    likes = ""
    saved = "" 
    shared = ""
    playCount = ""
    repostCount = ""
    if 'statsV2' in content:
        comments = content['statsV2']['commentCount'] if 'desc' in content else ""
        likes = content['statsV2']['diggCount'] if 'desc' in content else ""
        saved = content['statsV2']['collectCount'] if 'desc' in content else ""
        shared = content['statsV2']['shareCount'] if 'desc' in content else ""
        playCount = content['statsV2']['playCount'] if 'desc' in content else ""
        repostCount = content['statsV2']['repostCount'] if 'desc' in content else ""

    tags = soup.find("meta", attrs={'name': 'keywords'})
    tags_list = tags['content'] if tags else "No description found"
    tags_list = [i.strip() for i in tags_list.split(",")]

    

    creatorKeywords = [i['keyword'].replace("-", " ") for i in content['keywordTags']] if 'keywordTags' in content else []

    return {
        "url": url,
        "title": title_text,
        "description": description,
        "creator": author,
        "soundName": audio_name,
        "soundUrl": audio_url,
        "Comments": comments,
        "likes": likes,
        "saves": saved,
        "shares": shared,
        "plays": playCount,
        "reposts": repostCount,
        "creatorTags": creatorKeywords,
        "tags": tags_list
    }

def process_and_save_csv(input_csv, output_csv):
    # Read input CSV
    df = pd.read_csv(input_csv)

    # Ensure input CSV has required columns
    if 'url' not in df.columns or 'keyword' not in df.columns or 'date' not in df.columns:
        print("CSV must contain 'url', 'keyword', and 'date' columns.")
        return

    all_data = []  # List to store processed rows

    # Iterate over each row in input CSV
    for _, row in tqdm(df.iterrows(), total=len(df), desc="Processing URLs", unit="row"):
        url = row['url']
        searchterm = row['keyword']
        date = row['date']

        # Fetch additional data for the URL
        additional_data = scrape_tiktok_text(url)

        # Format data in the required JSON structure
        new_row = {
            "url": url,
            "date": date,
            "searchterm": searchterm,
            "title": additional_data.get("title", ""),
            "description": additional_data.get("description", ""),
            "creator": additional_data.get("creator", ""),
            "soundName": additional_data.get("soundName", ""),
            "soundUrl": additional_data.get("soundUrl", ""),
            "Comments": additional_data.get("Comments", 0),
            "likes": additional_data.get("likes", 0),
            "saves": additional_data.get("saves", 0),
            "shares": additional_data.get("shares", 0),
            "plays": additional_data.get("plays", 0),
            "reposts": additional_data.get("reposts", 0),
            "creatorTags": additional_data.get("creatorTags", ""),
            "tags": additional_data.get("tags", ""),
        }

        # Append formatted row
        all_data.append(new_row)

    # Convert collected data into a DataFrame
    new_df = pd.DataFrame(all_data)

    # If output CSV exists, append data while maintaining column structure
    if os.path.exists(output_csv):
        existing_df = pd.read_csv(output_csv)
        new_df = pd.concat([existing_df, new_df], ignore_index=True).fillna('')

    # Save the updated DataFrame to CSV
    new_df.to_csv(output_csv, index=False)

    print(f"Processed data saved to {output_csv}")

input_csv_path = 'tiktok_video_data.csv'
output_csv_path = 'tiktok_video_data_final.csv'  # The structured output CSV
process_and_save_csv(input_csv_path, output_csv_path)

driver.quit()
