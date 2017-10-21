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
    return track_data


def main():
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    redirect_uri = 'http://localhost/'
    code = get_code(client_id=client_id, redirect_uri=redirect_uri, scopes='playlist-read-private')
    token = get_token(code=code, client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri)

    global header
    header = {'Authorization': 'Bearer ' + token}

    playlists = get_playlists()

    for playlist in playlists:
        name = playlist['name']
        collaborative = playlist['collaborative']
        uri = playlist['uri']
        track_href = playlist['tracks']['href']
        id = playlist['id']
        user_id = playlist['owner']['id']
        get_playlist_tracks(user_id=user_id, playlist_id=id)


    print playlists


main()
