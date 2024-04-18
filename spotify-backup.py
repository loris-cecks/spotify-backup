import os
import requests
import subprocess
from urllib.parse import urlparse
from datetime import datetime
from dotenv import load_dotenv
import shutil

# Function to sanitize filenames
def sanitize_filename(name):
    return "".join(c if c.isalnum() or c in " -_" else "-" for c in name)

# Function to check and clean up old folders
def cleanup_old_playlists(directory, prefix="playlists_", max_folders=5):
    all_folders = [os.path.join(directory, f) for f in os.listdir(directory) if os.path.isdir(os.path.join(directory, f)) and f.startswith(prefix)]
    while len(all_folders) > max_folders:
        all_folders.sort(key=lambda x: os.path.getmtime(x))
        shutil.rmtree(all_folders.pop(0), ignore_errors=True)

# Load environment variables
load_dotenv()

# Check and load required environment variables
required_env_vars = ['SPOTIFY_USER_URL', 'SPOTIPY_CLIENT_ID', 'SPOTIPY_CLIENT_SECRET']
if not all(var in os.environ for var in required_env_vars):
    print('Missing one or more required environment variables:', required_env_vars)
    exit()

# Spotify user URL and credentials
user_url = os.getenv('SPOTIFY_USER_URL')
client_id = os.getenv('SPOTIPY_CLIENT_ID')
client_secret = os.getenv('SPOTIPY_CLIENT_SECRET')

# Extract user ID from the URL
parsed_url = urlparse(user_url)
user_id = parsed_url.path.split('/')[-1]
if not user_id:
    print("Invalid Spotify user URL.")
    exit()

# Function to handle Spotify API requests
def spotify_api_request(url, headers):
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch data: {response.json()}")
        exit()
    return response.json()

# Authenticate with Spotify
try:
    auth_response = requests.post(
        'https://accounts.spotify.com/api/token',
        data={
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret
        }
    ).json()
    access_token = auth_response.get('access_token')
    if not access_token:
        print('Authentication failed:', auth_response)
        exit()
except requests.RequestException as e:
    print(f'Error during authentication: {e}')
    exit()

headers = {'Authorization': f'Bearer {access_token}'}

# Fetch and process playlists
playlist_ids = []
destination_folder = '/home/loris_cecks/Music'
try:
    playlists = spotify_api_request(f'https://api.spotify.com/v1/users/{user_id}/playlists', headers)
    for playlist in playlists['items']:
        playlist_ids.append(playlist['id'])
        playlist_link = f"https://open.spotify.com/playlist/{playlist['id']}"
        playlist_details = spotify_api_request(f'https://api.spotify.com/v1/playlists/{playlist["id"]}', headers)
        safe_name = sanitize_filename(playlist_details['name'])
        safe_folder_path = os.path.join(destination_folder, safe_name)
        
        # Clean up existing folder and create a new one
        if os.path.exists(safe_folder_path):
            shutil.rmtree(safe_folder_path)
        os.makedirs(safe_folder_path, exist_ok=True)

        # Download playlist with spotdl in the specified folder
        subprocess.run(['git-auto'])
        subprocess.run(['spotdl', '--playlist', playlist_link, '--output', safe_folder_path])

except requests.RequestException as e:
    print(f'Error fetching playlists: {e}')
