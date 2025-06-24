# main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from scraper import onboard_creator, refresh_creator

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/onboard")
async def onboard(request: Request):
    data = await request.json()
    handle = data.get("handle")
    return onboard_creator(handle)  # removed 'await'

@app.post("/refresh")
async def refresh(request: Request):
    data = await request.json()
    handle = data.get("handle")
    return refresh_creator(handle)  # removed 'await'
