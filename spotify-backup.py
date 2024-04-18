import os
import requests
import subprocess
from urllib.parse import urlparse
from datetime import datetime
from dotenv import load_dotenv

# Function to sanitize filenames
def sanitize_filename(name):
    return "".join(c if c.isalnum() or c in " -_" else "-" for c in name)

# Load environment variables
load_dotenv()

# Spotify user URL
user_url = os.getenv('SPOTIFY_USER_URL')

# Extract user ID from the URL
parsed_url = urlparse(user_url)
user_id = parsed_url.path.split('/')[-1]

# Check if the user ID is valid
if not user_id:
    print('URL dell\'utente non valido.')
    exit()

# Read Spotify credentials from the environment
client_id = os.getenv('SPOTIPY_CLIENT_ID')
client_secret = os.getenv('SPOTIPY_CLIENT_SECRET')

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
except Exception as e:
    print(f'Error during authentication: {str(e)}')
    exit()

headers = {'Authorization': f'Bearer {access_token}'}

# Get current date and time and format it as a string
now = datetime.now()
timestamp = now.strftime('%Y%m%d%H%M%S')

# Create the folder name
folder_name = f'playlists_{timestamp}'
folder_path = os.path.join(os.getcwd(), folder_name)

# Create the folder
try:
    os.makedirs(folder_path, exist_ok=True)
except Exception as e:
    print(f'Errore nella creazione della cartella: {str(e)}')
    exit()

# Get the user's playlists from Spotify
try:
    response = requests.get(f'https://api.spotify.com/v1/users/{user_id}/playlists', headers=headers)
    if response.status_code != 200:
        print(f'Failed to fetch playlists: {response.json()}')
        exit()

    playlists = response.json()

    for playlist in playlists['items']:
        # Get playlist details
        playlist_response = requests.get(f'https://api.spotify.com/v1/playlists/{playlist["id"]}', headers=headers)
        if playlist_response.status_code != 200:
            print(f'Failed to fetch playlist details: {playlist_response.json()}')
            continue

        playlist_details = playlist_response.json()

        # Use the playlist title and timestamp as the filename
        safe_name = sanitize_filename(playlist_details['name'])
        filename = f"{safe_name}_{timestamp}.txt"
        filepath = os.path.join(folder_path, filename)

        # Open a text file with the playlist name and timestamp in the subfolder
        try:
            with open(filepath, 'w', encoding='utf-8') as file:
                # Iterate over each track in the playlist
                for item in playlist_details['tracks']['items']:
                    track = item['track']
                    title = track['name']
                    artists = ', '.join(artist['name'] for artist in track['artists'])
                    album = track['album']['name']

                    # Write the song details to the file
                    file.write(f"{title} - {artists} - {album}\n")

            print(f'La lista delle canzoni della playlist "{playlist_details["name"]}" è stata salvata in {filename}')
        except Exception as e:
            print(f'Error writing to file {filename}: {str(e)}')

except Exception as e:
    print(f'Error fetching user playlists: {str(e)}')

try:
    result = subprocess.run(['git-auto'], check=True, text=True, capture_output=True)
    print(f"'git-auto' command executed successfully:\n{result.stdout}")
except subprocess.CalledProcessError as e:
    print(f"'git-auto' command failed with error:\n{e.stderr}")
