from fastapi import FastAPI, Request
from scraper import onboard_creator, refresh_creator

app = FastAPI()

@app.post("/onboard")
async def onboard(data: dict):
    handle = data.get("handle")
    return await onboard_creator(handle)

@app.post("/refresh")
async def refresh(data: dict):
    handle = data.get("handle")
    return await refresh_creator(handle)
