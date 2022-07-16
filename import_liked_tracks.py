from create_monthly_playlist import load_env, sp_client
import json
import spotipy
import pandas as pd
from tqdm.tqdm import tqdm
from datetime import date
from datetime import datetime


def add_tracks_df(results):
    tracks = []
    for item in results['items']:
        track = item['track']
        data = {
            'added_at': item['added_at'],
            'artists_name': track['artists'][0]['name'],
            'track_name': track['name'],
            'spotify_id': track['id'],
            'urls': track['external_urls']['spotify'],
            'uri': track['uri'],
            'updated_date': date.today()
        }
        tracks.append(data)
    return tracks


def get_liked_tracks(result_pages=500):
    sp = sp_client(scope=['user-library-read'])
    results = sp.current_user_saved_tracks(limit=20)

    column_name = ['added_at', 'artists_name', 'track_name', 'spotify_id', 'urls', 'uri', 'updated_date']
    df = pd.DataFrame(columns=column_name)

    df = df.append(add_tracks_df(results), ignore_index=True, sort=False)

    pbar = tqdm(total=result_pages)
    while results['next']:
        try:
            results = sp.next(results)
            
            df = df.append(add_tracks_df(results), ignore_index=True, sort=False)
            pbar.update(1)
        except Exception as e:
            print(e)
        
    pbar.close()
    return df


def export_to_pickle(df):
    df.to_pickle(f'saved_track_{datetime.now().strftime("%Y%m%d")}.pkl')


if __name__ == 'main':
    try:
        df = get_liked_tracks()

        export_to_pickle(df=df)
    except Exception as e:
        print(e)
