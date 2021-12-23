# %pip install pyowm
# https://pyowm.readthedocs.io/en/latest/v3/code-recipes.html
import pyowm # import Python Open Weather Map to our project.
from pyowm.owm import OWM
from pyowm.utils import timestamps, formatting
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
import requests
import datetime

# APIKEY='4a39d509528e58d16ccddf16bfbf28fb'
APIKEY='d72d4c09b55d867e5ac4a2ed20866a42'
# APIKEY='ec630f7532ddd44526a04cbf39932f32'
# APIKEY = '0fd43ae99296d93c97144147e7a60c63'
place = 'New York City,US'
def owm_manager_auth(key, place):
    owm = pyowm.OWM(APIKEY)
    mgr = owm.weather_manager()
    Weather = mgr.weather_at_place(place)
    return Weather
Weather = owm_manager_auth(APIKEY, place)

def lag_48(hour=None, minute=None, lag_time =48):
    """
    return 48 hours time in timestamp format
    # check:
    for i in lag_48():
    print(datetime.datetime.utcfromtimestamp(i))
    """
    def _timedelta_hours(offset, date=None):
        if date is None:
            return datetime.now(timezone.utc) + timedelta(hours=offset)
        else:
            assert isinstance(date, datetime), __name__ + \
                ": 'date' must be a datetime.datetime object"
        return date + timedelta(hours=offset)

    from datetime import datetime, timedelta, timezone
    now = datetime.now(timezone.utc)
    if hour is None:
        hour = now.hour
    if minute is None:
        minute = now.minute
    times = []
    SIGN = np.abs(lag_time) / lag_time
    for i in range(np.abs(lag_time)):
        prev_date = _timedelta_hours(-i * SIGN, now)
        time = datetime(prev_date.year, prev_date.month,
                        prev_date.day, prev_date.hour, prev_date.minute, 0, 0, timezone.utc)
        time = formatting.to_UNIXtime(time)
        times.append(time)
    return times

def get_features(dt, keep = True, baseline = None):
    """
    :param dt: datetime used to get features
            keep: whether keep the feature `weather_main`
    :return: a list of data of the pre-defined features
    """
    from datetime import datetime, timedelta, timezone
    now = formatting.to_UNIXtime(datetime.now(timezone.utc))
    owm = pyowm.OWM(APIKEY)
    mgr = owm.weather_manager()
    if now >= dt: # 过去
        dic = mgr.one_call_history(lat=40.7128, lon=-74.0060, dt=dt).current.to_dict()
        wind_speed = dic['wind']['speed']
        pressure = dic['pressure']['press']
        weather_main = dic['status']
        temp = dic['temperature']['temp']
    else: # 未来
        wind_speed = baseline[6]
        pressure = baseline[5]
        try:
            weather_main = baseline[7]
        except:
            weather_main = 0
        temp = baseline[0]
    dt = datetime.utcfromtimestamp(dt)
    hour = dt.hour
    month = dt.month
    year = 365
    day_cos = np.round(np.cos(hour * (2 * np.pi / 24)), 3)
    day_sin = np.round(np.sin(hour * (2 * np.pi / 24)), 3)
    month_cos = np.cos((dt.timestamp()) * (2 * np.pi / year))
    month_sin = np.sin((dt.timestamp()) * (2 * np.pi / year))
    if keep:
        ls = [temp, day_cos, day_sin, month_sin, month_cos, pressure, wind_speed, weather_main]
    else:
        ls = [temp, day_cos, day_sin, month_sin, month_cos, pressure, wind_speed]
    return ls

def convert_to_np(pd_final_test):
    sunny = pd_final_test.weather_main == 'Clear'
    windy = pd_final_test.weather_main.isin(['Clouds', 'Squall', 'Thunderstorm', 'Tornado'])
    rainy = pd_final_test.weather_main.isin(['Mist', 'Drizzle', 'Rain', 'Haze', 'Dust', 'Smoke'])
    snowy = pd_final_test.weather_main .isin(['Snow', 'Fog'])
    pd_final_test['weather_main'] = pd_final_test['weather_main'].where(~sunny, 'sunny')
    pd_final_test['weather_main'] = pd_final_test['weather_main'].where(~windy, 'windy')
    pd_final_test['weather_main'] = pd_final_test['weather_main'].where(~rainy, 'rainy')
    pd_final_test['weather_main'] = pd_final_test['weather_main'].where(~snowy, 'snowy')
    conditions = [
        (pd_final_test['weather_main'] == 'sunny'),
        (pd_final_test['weather_main'] == 'windy'),
        (pd_final_test['weather_main'] == 'rainy'),
        (pd_final_test['weather_main'] == 'snowy')
    ]
    values = [0, 1, 2, 3]
    pd_final_test['weather_id'] = np.select(conditions, values)
    scaler = StandardScaler()
    np_final_test = scaler.fit_transform(pd_final_test[['temp', 'day_cos', 'day_sin', 'month_sin',\
                                                        'month_cos', 'pressure', 'wind_speed']])
    np_final_test = np.append(np_final_test, pd_final_test['weather_id'].values.reshape(-1,1).astype('int'), axis=1)
    return np_final_test



def create_X_Y(ts: np.array, _lag=48, n_ahead=1, target_index=0) -> tuple:
    """
    - ts: A time series dataframe in series form
    - lag: Number of lags (hours back) to use for models
    - n_ahead: Steps ahead to forecast
    Using <lag> number of data: x_{i}, x_{i+1}, ...x_{i+lag-1} to predict <n_ahead>
    number of data x_{i+lag}, ..., x_{i+lag+n_ahead-1}
    Thus, X = x_{i}, x_{i+1}, ...x_{i+lag-1}
        , Y = x_{i+lag}, ..., x_{i+lag+n_ahead-1}
    """
    # Extract # of features and # of observations
    n_obs = ts.shape[0]
    n_features = ts.shape[1]

    # Creating placeholder lists
    X, Y = [], []

    # if we don't have enough obs to predict Y
    if n_obs - _lag <= 0:
        X.append(ts)  # no label, only x
    else:
        for i in range(n_obs - _lag - n_ahead):
            Y.append(ts[(i + _lag):(i + _lag + n_ahead), target_index])
            X.append(ts[i:(i + _lag)])

    X, Y = np.array(X), np.array(Y)

    # Reshaping the X array to an RNN input shape
    X = np.reshape(X, (X.shape[0], _lag, n_features))

    return X, Y