import requests
import base64
import json
import pandas
import os
import webbrowser
import urllib


def get_code(client_id, redirect_uri, scopes):
    params = {'response_type': 'code',
              'redirect_uri': redirect_uri,
              'client_id': client_id,
              'scope': scopes}
    url = 'https://accounts.spotify.com/authorize'
    requests.get(url=url, params=params)

    auth_url = url + '?' + urllib.urlencode(params)
    webbrowser.open(auth_url)

    try:
        response = raw_input("Enter the URL you were redirected to: ")
    except NameError:
        response = input("Enter the URL you were redirected to: ")

    code = response

    return code


def get_token(code, client_id, client_secret, redirect_uri):
    url = 'https://accounts.spotify.com/api/token'
    payload = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_uri
    }
    headers = {
        'Authorization': 'Basic ' + base64.b64encode(client_id + ':' + client_secret)
    }

    data = requests.post(url=url, data=payload, headers=headers)
    data = json.loads(data.text)

    access_token = data['access_token']

    return access_token


def get_playlists():
    url = 'https://api.spotify.com/v1/me/playlists'

    limit = 50
    offset = 0
    params = {'limit': limit,
              'offset': offset
              }
    data = requests.get(url=url, headers=header, params=params)
    playlist_data = json.loads(data.text)

    playlists = playlist_data['items']

    while playlist_data['next'] is not None:
        offset = offset + limit
        params = {'limit': limit,
                  'offset': offset}
        data = requests.get(url=url, headers=header, params=params)
        playlist_data = json.loads(data.text)
        playlists = playlists + playlist_data['items']

    return playlists


def get_playlist_tracks(user_id, playlist_id):
    url = 'https://api.spotify.com/v1/users/' + user_id + '/playlists/' + playlist_id + '/tracks'
    limit = 100
    offset = 0
    params = {'limit': limit,
              'offset': offset
              }
    data = requests.get(url=url, headers=header, params=params)
    track_data = json.loads(data.text)
    df = pandas.DataFrame(track_data['items'])

    if df.empty:
        return df
    else:
        track_info = pandas.DataFrame(df['track'].tolist())

        tracks = track_info[['id', 'name']]
        artists = track_info[['artists']].apply(lambda x: x[0][0]['name'], 1)
        tracks.loc[:, 'artist'] = artists
        return tracks


def get_track_info(track_ids):
    url = 'https://api.spotify.com/v1/audio-features'
    tracks = ",".join(track_ids)
    params = {
        'ids': tracks
    }
    data = requests.get(url, params=params, headers=header)
    feature_data = pandas.DataFrame(json.loads(data.text)['audio_features'])
    return feature_data


def main():
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    redirect_uri = 'http://localhost/'
    scopes = 'playlist-read-private'
    code = get_code(client_id=client_id, redirect_uri=redirect_uri, scopes=scopes)
    token = get_token(code=code, client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri)

    global header
    header = {'Authorization': 'Bearer ' + token}

    playlists = get_playlists()

    playlist_track_data = pandas.DataFrame(columns=['acousticness', 'analysis_url', 'danceability', 'duration_ms',
                                                    'energy', 'track_id', 'instrumentalness', 'key', 'liveness',
                                                    'loudness', 'mode', 'speechiness', 'tempo', 'time_signature',
                                                    'track_href', 'type', 'uri', 'valence', 'playlist_name',
                                                    'playlist_id', 'user_id'])

    for playlist in playlists:
        playlist_id = playlist['id']
        playlist_name = playlist['name']
        user_id = playlist['owner']['id']

        print playlist_id, user_id

        tracks = get_playlist_tracks(user_id=user_id, playlist_id=playlist_id)
        if tracks.empty:
            continue

        tracks = tracks[tracks['id'].notnull()]
        if tracks.empty:
            continue

        track_features = get_track_info(tracks['id'])

        track_features.loc[:, 'playlist_name'] = playlist_name
        track_features.loc[:, 'playlist_id'] = playlist_id
        track_features.loc[:, 'user_id'] = user_id
        track_features = track_features.rename(columns={'id': 'track_id'})

        playlist_track_data = playlist_track_data.append(track_features)

    playlist_track_data.to_csv('/Users/jasonjea/playlist-project/playlist_track_data.txt', sep='\t')


main()
