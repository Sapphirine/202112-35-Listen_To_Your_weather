# Listen to Your Weather 
[![GitHub license](https://img.shields.io/github/license/Naereen/StrapDown.js.svg)](https://github.com/Naereen/StrapDown.js/blob/master/LICENSE)
EECS E6893 Final Project
Group 35


**Overview**

Our project constructed an hourly playlist generator system based on the real-time weather forecast using the 'OpenWeather' API, and 'Spotify' API. We performed experiments for temperature model selection by varying response encoding method, window size and model type. We finally deployed a real-time LSTM model in predicting both weather category and temperature. Due to privacy issues and access limits, we are not able to fetch global music playing data and construct any recommendation models, thus we recommend songs based on the user's playing history and top 50 music playlists provided by API. Our final product is a website where users could login, view 7 hours ahead temperature prediction results and play with the recommended playlists. 

**Usage**

1. Download the whole final_project directory

2. Create developer accounts in `openweathermap` and `spotify` API, and substitute your API keys and secrets in the files listed below

- In "/api/spotify.py" file, substitute `MY_CLIENT_ID` and `MY_CLIENT_SECRET` with your Spotify API client ID and secret, you can get them from [Spotify API](https://developer.spotify.com/dashboard/applications). 

- In `owm,py` file, substitute `MY_API_KEY` with your OpenWeather API key, you can get it from [OpenWeather API](https://home.openweathermap.org/api_keys).

3. Deploy the server using the command below: 

- Run `schedule_fetching.py` file, which is scheduled to predict weather every hour and save the predicted results into `predicted_results` folder.

- Run `main.py` file.

5. Open browser to use our application:

- Open `http://127.0.0.1:8080/` in Google Chrome. 

**Demo Webpage**

<img width="405" alt="demo" src="https://user-images.githubusercontent.com/63638608/147186517-1c6de894-df27-4932-a722-f38c033e6799.png">
