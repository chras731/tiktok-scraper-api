import os
import time
import uuid
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from supabase import create_client, Client

# Supabase credentials from Railway ENV
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def create_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--window-size=1920x1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64)")
    return webdriver.Chrome(options=chrome_options)

def extract_video_metadata(url, driver):
    try:
        driver.get(url)
        time.sleep(3)
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")

        # Extract metadata
        title = soup.find("title").text if soup.find("title") else None
       
