from fastapi import FastAPI
from pagedata import run_metadata_jobs

app = FastAPI()

@app.get("/")
def root():
    return {"message": "TikTok Scraper API is running."}

@app.post("/run")
def run_jobs():
    run_metadata_jobs()
    return {"message": "Jobs executed."}
