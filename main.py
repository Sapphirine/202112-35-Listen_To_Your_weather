from flask import Flask, request, redirect, g, render_template, make_response, session, url_for
from datetime import datetime, timedelta
from pytz import timezone
import urllib
import urllib.parse
import secrets
import string
import requests
from urllib.parse import urlencode

from api import spotify

app = Flask(__name__)
app.secret_key = '3d6f45a5fc12445dbac2f59c3b6c7cb1'
PORT = spotify.PORT

@app.route("/")
def weather():
    global weather_word
    global weather_id

    hour = int(datetime.now(timezone('US/Eastern')).strftime("%H"))
    weather = []
    with open(f"predicted_results/data_for_demo.txt", 'r') as reader:
        for line in reader:
            weather_line = line.split(',')
            weather_line_int = [int(ele) for ele in weather_line]
            weather.append(weather_line_int)

    for wt in weather:
        wt.append(f'{hour}'+":00")
        hour += 1
        hour %= 24

    weather[0][2] = "Now"
    weather_dic = {0: "sunny", 1:"cloudy", 2:"windy", 3:"foggy", 4:"rainy", 5:"snowy"}
    weather_id = weather[1][0]
    weather_word = weather_dic[weather[1][0]]

    return render_template('weather.html', weather = weather)


@app.route('/login')
def login():
    res = spotify.getUserAuthorization()
    return res


@app.route('/callback')
def callback():

    res = spotify.getUserToken()
    res_data = res.json()

    if res_data.get('error') or res.status_code != 200:
        app.logger.error(
            'Failed to receive token: %s',
            res_data.get('error', 'No error information received.'),
        )
        abort(res.status_code)

    session['tokens'] = {
        'access_token': res_data.get('access_token'),
        'refresh_token': res_data.get('refresh_token'),
    }

    return redirect(url_for('recommend'))


@app.route("/recommend")
def recommend():
    global weather_word
    global weather_id

    authorization_header = {"Authorization": "Bearer {}".format(session['tokens'].get('access_token'))}
    profile_data = spotify.getProfileData(authorization_header)

    top_track_playlist_list = [track.get('id') for track in spotify.getTopTrack(authorization_header).get('items')]
    audio_feature_list = [(x, spotify.getAudioFeatureFromTrack(authorization_header, x)) for x in top_track_playlist_list]
    sort_variable_list = [(x[0], x[1].get('valence'), x[1].get('instrumentalness'), x[1].get('energy'),
                           x[1].get('danceability'), x[1].get('acousticness'))
                          for x in audio_feature_list]

    vw = 0 # vw = valence weight
    iw = 0 # iw = instrumentalness weight
    ew = 0 # ew = energy weight
    dw = 0 # dw = danceability weight
    aw = 0 # aw = acousticness weight

    if weather_id == 0:
        # Sunny
        vw = 1.6
        iw = -1.05
        ew = 1.7
        dw = 1.3
        aw = -1.3
    elif weather_id == 1:
        # Cloudy
        vw = -1.3
        iw = 1.5
        ew = -1.6
        dw = -1.2
        aw = 1.1
    elif weather_id == 2:
        # Windy
        vw = -1.5
        iw = 1.2
        ew = -1.7
        dw = -1.3
        aw = 1.8
    elif weather_id == 3:
        # Foggy
        vw = -1.15
        iw = 1.5
        ew = -1.5
        dw = -1.03
        aw = 1.2
    elif weather_id == 4:
        # Rainy
        vw = -1.15
        iw = 1.5
        ew = -1.5
        dw = -1.03
        aw = 1.2
    elif weather_id == 5:
        # Snowy
        vw = -1.15
        iw = 1.5
        ew = -1.5
        dw = -1.03
        aw = 1.2

    calculated_sort_variable_list = sorted([(track_data[0],
                                             ((track_data[1] * vw) + (track_data[2] * iw) + (track_data[3] * ew)
                                              + (track_data[4] * dw) + (track_data[5] * aw))
                                             )
                                            for track_data in sort_variable_list], key=lambda sort_key: sort_key[1],
                                           reverse=True)

    recommendation_tracks = spotify.getRecommendationThroughTracks(authorization_header, [x[0] for x in calculated_sort_variable_list[:5]], []).get("tracks")
    create_playlist = spotify.postBlankPlaylist(authorization_header, weather_word, profile_data.get('id'))
    spotify.postTrackToPlaylist(authorization_header,[x.get('id') for x in recommendation_tracks],create_playlist[1])

    return render_template("recommend.html",sorted_array=spotify.getIframePlaylist(create_playlist[1]), weather_word=weather_word)


if __name__ == "__main__":
    app.run(debug=True, port=PORT)
