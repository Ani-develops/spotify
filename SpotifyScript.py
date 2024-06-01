import pandas as pd
import requests
from requests.auth import HTTPBasicAuth
import time

# Your Spotify API credentials
CLIENT_ID = '2bca54acca6748c3ba874db943c92e4f'
CLIENT_SECRET = 'dba29917cd3b422487a367a0d5dedca7'

# Simple cache to avoid redundant API calls
cache = {}

def get_spotify_token(client_id, client_secret):
    """Authenticate with the Spotify API and return an access token."""
    auth_url = 'https://accounts.spotify.com/api/token'
    response = requests.post(auth_url, data={'grant_type': 'client_credentials'}, auth=HTTPBasicAuth(client_id, client_secret))
    if response.status_code == 200:
        return response.json().get('access_token')
    else:
        raise Exception("Failed to retrieve access token")

def get_track_info(access_token, track_name, artist_name):
    """Search for a track by name and artist and return Spotify and album cover URLs."""
    # Check cache first
    cache_key = f"{track_name}||{artist_name}"
    if cache_key in cache:
        return cache[cache_key]

    search_url = 'https://api.spotify.com/v1/search'
    headers = {'Authorization': f'Bearer {access_token}'}
    query_params = {'q': f'track:"{track_name}" artist:"{artist_name}"', 'type': 'track', 'limit': 1}
    response = requests.get(search_url, headers=headers, params=query_params)
    
    if response.status_code == 200 and response.json()['tracks']['items']:
        track = response.json()['tracks']['items'][0]
        spotify_url = track['external_urls']['spotify']
        album_cover_url = track['album']['images'][0]['url'] if track['album']['images'] else 'Not Available'
        # Update cache
        cache[cache_key] = (spotify_url, album_cover_url)
        return spotify_url, album_cover_url
    elif response.status_code == 429:  # Handle rate limiting
        retry_after = int(response.headers.get('Retry-After', 1))
        time.sleep(retry_after)
        return get_track_info(access_token, track_name, artist_name)  # Retry after waiting
    else:
        # Update cache with not found
        cache[cache_key] = ('Not Found', 'Not Available')
        return 'Not Found', 'Not Available'

def update_spotify_data(csv_file_path, output_file_path):
    """Read a CSV, update it with Spotify URLs, and save to a new file."""
    df = pd.read_csv(csv_file_path, encoding='ISO-8859-1')
    
    token = get_spotify_token(CLIENT_ID, CLIENT_SECRET)

    df['Spotify_URL'] = ''
    df['Album_Cover_URL'] = ''
    for index, row in df.iterrows():
        # Using the first artist for search if there are multiple artists
        spotify_url, album_cover_url = get_track_info(token, row['track_name'], row['artist(s)_name'].split(", ")[0])
        df.at[index, 'Spotify_URL'] = spotify_url
        df.at[index, 'Album_Cover_URL'] = album_cover_url

    df.to_csv(output_file_path, index=False, encoding='ISO-8859-1')
    print(f"Updated CSV saved as {output_file_path}")

if __name__ == "__main__":
    # Replace these paths with the actual paths on your system
    input_csv = 'F:\\archive\\spotify-2023.csv'  # Adjust path as needed
    output_csv = 'F:\\archive\\updated_spotify-2023.csv'  # Adjust path as needed
    update_spotify_data(input_csv, output_csv)

