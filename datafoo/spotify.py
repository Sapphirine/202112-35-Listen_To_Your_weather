import json
import requests
import base64
from datetime import date
from flask import request
from os import environ

#  Client Keys. Located as the environment variables
# CLIENT_ID_E = environ.get('6538c75e9c3448f88cc4dd0e33e6382a')
# CLIENT_SECRET_E = environ.get('17573c607cec4502b2cd36b338a5cb50')
CLIENT_ID = '6538c75e9c3448f88cc4dd0e33e6382a'
CLIENT_SECRET = '17573c607cec4502b2cd36b338a5cb50'

# Spotify URLS
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com"
API_VERSION = "v1"
SPOTIFY_API_URL = "{}/{}".format(SPOTIFY_API_BASE_URL, API_VERSION)

# Server-side Parameters
CLIENT_SIDE_URL = "http://127.0.0.1"
PORT = 8080
REDIRECT_URI = "{}:{}/callback/q".format(CLIENT_SIDE_URL, PORT)
SCOPE = "playlist-modify-public playlist-modify-private user-top-read"
STATE = ""
SHOW_DIALOG_bool = True
SHOW_DIALOG_str = str(SHOW_DIALOG_bool).lower()

auth_query_parameters = {
    "response_type": "code",
    "redirect_uri": REDIRECT_URI,
    "scope": SCOPE,
    # "state": STATE,
    # "show_dialog": SHOW_DIALOG_str,
    "client_id": CLIENT_ID
}

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
    print("profile_response", profile_response)
    profile_data = json.loads(profile_response.text)

    return profile_data

def getTopTrack(authorization_header):
    """ Gets the current (4 weeks) top track """
    time_range = 'short_term'
    limit = 50
    # type = 'tracks'
    # top_api_endpoint = "{}/me/playlist".format(SPOTIFY_API_URL)
    # top_api_endpoint = 'https://api.spotify.com/v1/me/playlists'
    # top_api_endpoint =  'https://api.spotify.com/v1/me/top/tracks'
    # specific_top_api_endpoint = "{}?time_range={}&limit={}&offset=0".format(top_api_endpoint,time_range,limit)
    # specific_top_api_endpoint = 'https://api.spotify.com/v1/me/top/artists?time_range=long_term&limit=10&offset=1'
    specific_top_api_endpoint2 = 'https://api.spotify.com/v1/playlists/37i9dQZEVXbMDoHDwVN2tF/tracks'
    top_track_response = requests.get(specific_top_api_endpoint2, headers=authorization_header)
    if top_track_response is None:
        top_track_response = requests.get(specific_top_api_endpoint2, headers=authorization_header)
    top_track_data = json.loads(top_track_response.text)
    return top_track_data

def getPlaylistData(authorization_header, profile_data):
    """ Gets all the playlists """
    playlist_api_endpoint = "{}/playlists".format(profile_data["href"])
    playlists_response = requests.get(playlist_api_endpoint, headers=authorization_header)
    playlist_data = json.loads(playlists_response.text)

    return playlist_data

def getTrackFromPlaylistData(authorization_header, playlist_data):
    """ Gets all the tracks from a single playlist """
    tracks_api_endpoint = "{}/tracks".format(playlist_data["href"])
    tracks_response = requests.get(tracks_api_endpoint, headers=authorization_header)
    track_data = json.loads(tracks_response.text)

    return track_data

def postBlankPlaylist(authorization_header, weather, user_id):
    """ Creates a blank playlist """
    d = date.today()
    user_date = d.strftime("%m/%d/%y")
    title = '{} {}'.format(d,weather)

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
    print("edited_track_list",edited_track_list)
    post_track_api_endpoint = '{}/playlists/{}/tracks?uris={}'.format(SPOTIFY_API_URL,playlist_id,','.join(edited_track_list))
    print("post_track_api_endpoint",post_track_api_endpoint)
    post_track_api_response = requests.post(post_track_api_endpoint, headers=authorization_header)

    return post_track_api_response

def getAudioFeatureFromTrack(authorization_header, id):
    """ Gets the audio feature from a single track (id) """
    audio_feature_api_endpoint = "{}/{}/audio-features/{}".format(SPOTIFY_API_BASE_URL, API_VERSION, id)
    audio_feature_response = requests.get(audio_feature_api_endpoint, headers=authorization_header)
    audio_feature_data = json.loads(audio_feature_response.text)

    return audio_feature_data

def getPostRequest():
    """ Gets the post request """
    auth_token = str(request.args["code"])
    code_payload = {
        "grant_type": "authorization_code",
        "code": str(auth_token),
        "redirect_uri": REDIRECT_URI
    }
    val = "{}:{}".format(CLIENT_ID, CLIENT_SECRET)
    base64encodedUtf8 = base64.b64encode(bytes(val, encoding='utf-8'))
    base64encoded = base64encodedUtf8.decode("utf-8")
    headers = {"Authorization": "Basic {}".format(base64encoded)}
    post_request = requests.post(SPOTIFY_TOKEN_URL, data=code_payload, headers=headers)

    return post_request

def getAuthorizationHeader():
    """ Returns the authorization header (authorization_header), needed for a lot of the functions"""
    post_request = getPostRequest()

    response_data = json.loads(post_request.text)
    access_token = response_data.get('access_token')
    refresh_token = response_data.get('refresh_token')
    token_type = response_data.get('token_type')
    expires_in = response_data.get('expires_in')

    authorization_header = {"Authorization": "Bearer {}".format(access_token)}

    return authorization_header