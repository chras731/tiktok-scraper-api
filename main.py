# main.py
from fastapi import FastAPI
from pagedata import run_metadata_jobs

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    print("Running metadata jobs on startup...")
    run_metadata_jobs()

@app.get("/")
def root():
    return {"message": "TikTok scraper API is running."}
