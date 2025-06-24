from fastapi import FastAPI, Request
from scraper import onboard_creator, refresh_creator

app = FastAPI()

@app.get("/healthcheck")
def healthcheck():
    return {"status": "ok"}

@app.post("/onboard")
async def onboard(req: Request):
    data = await req.json()
    handle = data.get("handle")
    if not handle:
        return {"error": "Missing TikTok handle"}
    return onboard_creator(handle)

@app.post("/refresh")
async def refresh(req: Request):
    data = await req.json()
    handle = data.get("handle")  # optional
    return refresh_creator(handle)
