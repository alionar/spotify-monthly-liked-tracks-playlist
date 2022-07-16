import argparse
import pandas as pd
from tqdm.tqdm import tqdm
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.oauth2 import SpotifyClientCredentials

# Helper
## Load .env as Environment Variable
def load_env():
    dotenv_path = Path('spotipy.env')
    load_dotenv(dotenv_path=dotenv_path)


def arg_pars():
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', action='store', dest='file', help='pkl file of dataframe')
    parser.add_argument('--month', action='store', dest='month', help='month of liked tracks')
    parser.add_argument('--year', action='store', dest='year', help='year of liked tracks')
    results = parser.parse_args()
    return results


def get_saved_tracks(month, year, file):
    df = pd.read_pickle(file)
    df['added_at'] = pd.to_datetime(df['added_at']).dt.tz_convert('Asia/Jakarta')
    return df[df['added_at'].dt.to_period('M') == f'{year}-{month}'].copy()


def monthly_playlist_name(month, year):
    month_name = datetime.strptime(month, "%m").strftime('%B')
    year_name = datetime.strptime(year, "%Y").strftime('%y')
    return f"{month_name} '{year_name}"


def sp_client(scope=[
        'playlist-read-private', 'playlist-modify-private', 
        'user-library-read', 
        'playlist-read-collaborative', 'playlist-modify-public'
    ]):
    scope = scope
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope,open_browser=False))
    return sp


def get_user_playlist():
    scope = [
        'playlist-read-private', 'playlist-modify-private', 
        'user-library-read', 
        'playlist-read-collaborative', 'playlist-modify-public'
    ]
    sp = sp_client(scope=scope)
    playlists = sp.user_playlists(user=sp.current_user()['id'])

    all_playlists_name = []

    while playlists:
        for i, playlist in enumerate(playlists['items']):
            if playlist['owner']['id'] == sp.current_user()['id']:
                #print("%4d %s %s" % (i + 1 + playlists['offset'], playlist['uri'],  playlist['name']))
                all_playlists_name.append({"name": playlist['name'], "playlist_id": playlist['id']})

        if playlists['next']:
            playlists = sp.next(playlists)
        else:
            playlists = None
    return pd.DataFrame(all_playlists_name)


def create_playlist(playlist_name):
    sp = sp_client()
    user_id = sp.me()['id']
    playlist_create = sp.user_playlist_create(user_id, playlist_name, public=False)
    return playlist_create


def add_tracks(tracks, playlist_id):
    scope = [
        'playlist-read-private', 'playlist-modify-private', 
        'user-library-read', 
        'playlist-read-collaborative', 'playlist-modify-public'
    ]
    sp = sp_client(scope=scope)

    pbar = tqdm(tracks.itertuples(), total=tracks.shape[0])
    for row in pbar:
        added_at = row.added_at
        artists_name = row.artists_name
        track_name = row.track_name
        spotify_id = row.spotify_id
        
        pbar.set_description(f"{added_at} {artists_name} - {track_name}")
        
        sp.playlist_add_items(playlist_id=playlist_id, items=[spotify_id])


def add_saved_tracks_by_month(month, year, file, all_user_playlist):    
    # Generate playlist name
    playlist_name = monthly_playlist_name(month=month, year=year)
    
    # Get monthly tracks
    tracks = get_saved_tracks(month=month, year=year, file=file)
    
    if len(tracks) > 0:
        # Add tracks, if playlist exists -> only add, if playlist not exists -> create first and add tracks
        is_exists = all_user_playlist.loc[all_user_playlist['name'].isin([playlist_name])]
        if len(is_exists) > 0:
            print(f"Playlist ada: {playlist_name} dengan id {is_exists['playlist_id'].item()}")
            # Add tracks from df_month to playlist_id
            id_pl = is_exists['playlist_id'].item()
        else:
            print(f"Playlist tidak ada: {playlist_name}")
            # CREATE A PLAYLIST WITH playlist_name
            playlist_create = create_playlist(playlist_name)
            id_pl = playlist_create["id"]

        add_tracks(tracks=tracks, playlist_id=id_pl)
    else:
        pass


if __name__ == 'main':
    results = arg_pars()
    year = results.year
    month = results.month
    file = results.file

    try:
        load_env()

        all_user_playlist = get_user_playlist()
        add_saved_tracks_by_month(
            month=month,
            year=year, 
            file=file, 
            all_user_playlist=all_user_playlist
        )
    except Exception as e:
        print(e)
