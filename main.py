from fastapi import FastAPI
from pagedata import run_metadata_jobs

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "TikTok Metadata API is live."}

@app.post("/scrape_metadata")
def run_scrape():
    run_metadata_jobs()
    return {"status": "metadata scraping started"}
