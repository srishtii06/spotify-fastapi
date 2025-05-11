from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, JSONResponse
import os
from dotenv import load_dotenv
from client import exchange_code_for_token, spotify_get, spotify_post, spotify_put
from fastapi import HTTPException
from pydantic import BaseModel

load_dotenv()

app = FastAPI()

class PlayTrackRequest(BaseModel):
    track_uri: str

@app.get("/")
def root():
    return {"message": "Spotify API Ready"}

@app.get("/login")
def login():
    scopes = "user-read-currently-playing user-top-read user-follow-read user-read-playback-state user-modify-playback-state"
    return RedirectResponse(
        url=f"https://accounts.spotify.com/authorize?client_id={os.getenv('SPOTIFY_CLIENT_ID')}&response_type=code&redirect_uri={os.getenv('SPOTIFY_REDIRECT_URI')}&scope={scopes}"
    )

@app.get("/callback")
async def callback(request: Request):
    code = request.query_params.get("code")
    tokens = await exchange_code_for_token(code)
    refresh_token = tokens.get("refresh_token")
    if refresh_token:
        # Save it to your .env or secure store
        return JSONResponse(content={"refresh_token": refresh_token})
    return tokens

@app.get("/spotify/top-tracks")
async def top_tracks():
    data = await spotify_get("me/top/tracks?limit=10")
    return data

@app.get("/spotify/now-playing")
async def now_playing():
    try:
        data = await spotify_get("me/player/currently-playing")
        
        # Check if the response is empty or the user isn't playing anything
        if not data or 'item' not in data:
            return {"message": "No song is currently playing."}

        return data  # Return the currently playing song data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/spotify/followed-artists")
async def followed_artists():
    data = await spotify_get("me/following?type=artist&limit=20")
    return data

@app.post("/spotify/play")
async def play_track(request: PlayTrackRequest):
        # Attempt to play the track
        return await spotify_put("me/player/play", {"uris": [request.track_uri]})
    # except HTTPException as e:
    #     # Catch the error and inform the user
    #     if e.status_code == 403:
    #         return {"error": "Premium subscription required for playback control."}
        


@app.post("/spotify/pause")
async def pause():
    return await spotify_put("me/player/pause")
