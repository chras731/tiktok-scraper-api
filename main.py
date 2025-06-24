from fastapi import FastAPI, Request
from scraper import onboard_creator, refresh_creator

app = FastAPI()

@app.post("/onboard")
async def onboard(request: Request):
    data = await request.json()
    handle = data.get("handle")
    return await onboard_creator(handle)

@app.post("/refresh")
async def refresh(request: Request):
    data = await request.json()
    handle = data.get("handle")
    return await refresh_creator(handle)

@app.get("/")
async def root():
    return {"message": "TikTok Scraper API is live!"}
