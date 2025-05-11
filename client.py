import base64
import os
import httpx
from dotenv import load_dotenv
import time
from fastapi import HTTPException

load_dotenv()

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")
REFRESH_TOKEN = os.getenv("SPOTIFY_REFRESH_TOKEN")
ACCESS_TOKEN = None  # This will store the current access token
ACCESS_TOKEN_EXPIRY = 0  # Store the token expiry timestamp

TOKEN_URL = "https://accounts.spotify.com/api/token"

# Function to encode client credentials
def get_auth_header():
    return base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()

# Exchange authorization code for access token
async def exchange_code_for_token(code: str):
    async with httpx.AsyncClient() as client:
        headers = {
            "Authorization": f"Basic {get_auth_header()}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI
        }
        response = await client.post(TOKEN_URL, data=data, headers=headers)
        return response.json()

# Refresh access token using the refresh token
async def refresh_access_token():
    global ACCESS_TOKEN, ACCESS_TOKEN_EXPIRY, REFRESH_TOKEN
    async with httpx.AsyncClient() as client:
        headers = {
            "Authorization": f"Basic {get_auth_header()}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "grant_type": "refresh_token",
            "refresh_token": REFRESH_TOKEN
        }
        response = await client.post(TOKEN_URL, data=data, headers=headers)
        
        if response.status_code == 200:
            access_data = response.json()
            ACCESS_TOKEN = access_data.get("access_token")
            expires_in = access_data.get("expires_in")
            ACCESS_TOKEN_EXPIRY = time.time() + expires_in  # Calculate expiry time
            return ACCESS_TOKEN
        else:
            raise Exception(f"Error refreshing token: {response.status_code} - {response.text}")

# Check if the access token is expired and refresh it if necessary
async def get_access_token():
    global ACCESS_TOKEN, ACCESS_TOKEN_EXPIRY
    if ACCESS_TOKEN and time.time() < ACCESS_TOKEN_EXPIRY:
        return ACCESS_TOKEN
    else:
        return await refresh_access_token()

# Spotify GET request
# async def spotify_get(endpoint: str):
#     access_token = await get_access_token()
#     headers = {
#         "Authorization": f"Bearer {access_token}"
#     }
#     url = f"https://api.spotify.com/v1/{endpoint}"
#     async with httpx.AsyncClient() as client:
#         response = await client.get(url, headers=headers)
        
#         # Check if the response status is OK
#         if response.status_code == 200:
#             return response.json()
#         else:
#             raise Exception(f"Error fetching data: {response.status_code} - {response.text}")
import httpx

async def spotify_get(endpoint: str):
    access_token = await get_access_token()
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    url = f"https://api.spotify.com/v1/{endpoint}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        
        # Check for status code
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 204:
            return {}  # Return an empty dict if no content is available (e.g., no song playing)
        else:
            raise Exception(f"Error fetching data: {response.status_code} - {response.text}")


# Spotify PUT request
async def spotify_put(endpoint, json_data=None):
    access_token = await get_access_token()
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient() as client:
        res = await client.put(f"https://api.spotify.com/v1/{endpoint}", headers=headers, json=json_data)
        if res.status_code == 200:
            return res.json()
        elif res.status_code == 403:
            raise HTTPException(status_code=403, detail="Premium subscription required for playback control.")
        else:
            raise Exception(f"Error updating data: {res.status_code} - {res.text}")

# Spotify POST request
async def spotify_post(endpoint, json_data=None):
    access_token = await get_access_token()
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient() as client:
        res = await client.post(f"https://api.spotify.com/v1/{endpoint}", headers=headers, json=json_data)
        if res.status_code == 200:
            return res.json()
        else:
            raise Exception(f"Error posting data: {res.status_code} - {res.text}")
