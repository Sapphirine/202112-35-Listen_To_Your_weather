# spotify-weather


This Flask app uses your zip code to first get the current weather. With that weather, it'll look through your top-played tracks and get top 5 songs that correlate with the weather. Using the top 5 song as seeds to get recommendation from Spotify. With the recommendation tracks, this app will create a playlist with the recommendation tracks.

## Screenshots


localhost:8080
![Home Screenshot](https://i.imgur.com/AEVEI9W.png "Home Screenshot")

localhost:8080/callback/q
![Recommend Screenshot](https://i.imgur.com/KTVgzfy.png "Recommend Screenshot")


## References


Utilizes Flask with Python 3.7 and [Spotify API](https://developer.spotify.com/documentation/web-api/) & [OpenWeatherMap API](https://openweathermap.org/api) with OAuth 2.0 Authentication.

## What can be done better


In [recommendation tracks](https://developer.spotify.com/documentation/web-api/reference/browse/get-recommendations/), you're allowed to put in audio_features. So correlate audio_features and weather together to come up with better recommendation system.

Also, changing the weight of audio_features fields so that the results are better.
