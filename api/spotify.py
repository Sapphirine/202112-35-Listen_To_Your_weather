from flask import Flask, request, redirect, g, render_template, make_response, session, url_for
from datetime import datetime, timedelta, date
from pytz import timezone
import urllib
import urllib.parse
import secrets
import string
import requests
from urllib.parse import urlencode
import json
import base64
from os import environ

CLIENT_ID = "MY_CLIENT_ID"
CLIENT_SECRET = "MY_CLIENT_SECRET"

# Spotify URLS
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com"
API_VERSION = "v1"
SPOTIFY_API_URL = "{}/{}".format(SPOTIFY_API_BASE_URL, API_VERSION)
SCOPE = "user-read-private user-read-email user-top-read playlist-modify-public playlist-modify-private"
SHOW_DIALOG_bool = True
SHOW_DIALOG_str = str(SHOW_DIALOG_bool).lower()
CLIENT_SIDE_URL = "http://127.0.0.1"
PORT = 8080
REDIRECT_URI = "{}:{}/callback".format(CLIENT_SIDE_URL, PORT)
AUTH_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'
ME_URL = 'https://api.spotify.com/v1/me'


def getUserAuthorization():
    state = ''.join(
        secrets.choice(string.ascii_uppercase + string.digits) for _ in range(16)
    )

    # scope = 'user-read-private user-read-email user-top-read playlist-modify-public playlist-modify-private'
    payload = {
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': REDIRECT_URI,
        'state': state,
        'scope': SCOPE,
    }

    res = make_response(redirect(f'{AUTH_URL}/?{urlencode(payload)}'))
    res.set_cookie('spotify_auth_state', state)

    return res


def getUserToken():
    error = request.args.get('error')
    code = request.args.get('code')
    state = request.args.get('state')
    stored_state = request.cookies.get('spotify_auth_state')

    if state is None or state != stored_state:
        app.logger.error('Error message: %s', repr(error))
        app.logger.error('State mismatch: %s != %s', stored_state, state)
        abort(400)

    payload = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
    }

    res = requests.post(TOKEN_URL, auth=(CLIENT_ID, CLIENT_SECRET), data=payload)
    return res


def getRecommendationThroughTracks(authorization_header, listOfSeedTracks, listOfAudioFeature):
    """ Utilizes a list of seed (5 max) and list of audio feature (currently none FIX) to return json of recommendation """
    limit = 20
    market = "ES"
    recommend_base_endpoint = "{}/recommendations?limit={}&market={}".format(SPOTIFY_API_URL,limit,market)
    appended_list_seed = ','.join(listOfSeedTracks)
    seed_api_endpoint = "{}&seed_tracks={}&".format(recommend_base_endpoint,appended_list_seed)
    raw_audio_feature = '&'.join("%s=%s" % (key, val) for (key, val) in listOfAudioFeature)
    audio_feature_api_endpoint = "{}{}".format(seed_api_endpoint,raw_audio_feature)

    recommend_response = requests.get(audio_feature_api_endpoint, headers=authorization_header)
    recommend_data = json.loads(recommend_response.text)

    return recommend_data

def getProfileData(authorization_header):
    """ Gets the profile data """
    user_profile_api_endpoint = "{}/me".format(SPOTIFY_API_URL)
    print("user_profile_api_endpoint:", user_profile_api_endpoint)
    profile_response = requests.get(user_profile_api_endpoint, headers=authorization_header)
    print("profile_response:", profile_response)
    profile_data = json.loads(profile_response.text)

    return profile_data

def getTopTrack(authorization_header):
    """ Gets the current (4 weeks) top track """
    time_range = 'short_term'#'short_term'
    limit = 50
    type = 'tracks'

    top_api_endpoint = "{}/me/top/{}".format(SPOTIFY_API_URL,type)
    specific_top_api_endpoint = "{}?time_range={}&limit={}".format(top_api_endpoint,time_range,limit)

    top_track_response = requests.get(specific_top_api_endpoint, headers=authorization_header)
    top_track_data = json.loads(top_track_response.text)
    return top_track_data


def postBlankPlaylist(authorization_header, weather, user_id):
    """ Creates a blank playlist """
    d = date.today()
    user_date = d.strftime("%m/%d/%y")
    title = '{} {}'.format(d,weather)
    print(title)
    playlist_post = {'name': title, 'public': 'true', 'collaborative': 'false', 'description': 'Created at {} for {} weather. Made via SpotifyWeather.'.format(user_date,weather)}
    post_playlist_api_endpoint = '{}/users/{}/playlists'.format(SPOTIFY_API_URL,user_id)
    print("post_playlist_api_endpoint",post_playlist_api_endpoint)
    
    post_playlist_api_response = requests.post(post_playlist_api_endpoint, headers=authorization_header, data=json.dumps(playlist_post))

    print("post_playlist_api_response",post_playlist_api_response)

    # ALSO GET THE PLAYLIST ID#
    post_playlist_api_json = post_playlist_api_response.json()
    playlist_id = post_playlist_api_json.get('id')

    return post_playlist_api_response, playlist_id

def postTrackToPlaylist(authorization_header, track_id_list, playlist_id):
    """ Puts a list of tracks (track_id_list) to a playlist (playlist_id) """
    edited_track_list = ['spotify:track:{}'.format(track_id) for track_id in track_id_list]
    # print("edited_track_list",edited_track_list)
    post_track_api_endpoint = '{}/playlists/{}/tracks?uris={}'.format(SPOTIFY_API_URL,playlist_id,','.join(edited_track_list))
    # print("post_track_api_endpoint",post_track_api_endpoint)
    post_track_api_response = requests.post(post_track_api_endpoint, headers=authorization_header)

    return post_track_api_response

def getAudioFeatureFromTrack(authorization_header, id):
    """ Gets the audio feature from a single track (id) """
    audio_feature_api_endpoint = "{}/{}/audio-features/{}".format(SPOTIFY_API_BASE_URL, API_VERSION, id)
    audio_feature_response = requests.get(audio_feature_api_endpoint, headers=authorization_header)
    audio_feature_data = json.loads(audio_feature_response.text)

    return audio_feature_data

def getIframePlaylist(playlist_id):
    """ Utilizes playlist_id to create a url for iframe """
    open_base_url = 'https://open.spotify.com/embed?uri=spotify'
    iframe_playlist_url = '{}:playlist:{}'.format(open_base_url,playlist_id)

    return iframe_playlist_url

