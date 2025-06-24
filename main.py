# main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from scraper import onboard_creator, refresh_creator

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/onboard")
async def onboard(request: Request):
    body = await request.json()
    handle = body.get("handle")
    return await onboard_creator(handle)

@app.post("/refresh")
async def refresh(request: Request):
    body = await request.json()
    handle = body.get("handle")
    return await refresh_creator(handle)
