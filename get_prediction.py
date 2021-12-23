### Load Pre-trained Model
import tensorflow as tf
from tensorflow import keras
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import pickle
import owm

### Init Model
class NNMultistepModel():

    def __init__(
            self,
            X,
            Y,
            n_outputs,
            n_lag,
            n_ft,
            n_layer,
            batch,
            epochs,
            lr,
            Xval=None,
            Yval=None,
            mask_value=-999.0,
            min_delta=0.001,
            patience=5
    ):
        lstm_input = Input(shape=(n_lag, n_ft))

        # Series signal
        lstm_layer = LSTM(n_layer, activation='relu')(lstm_input)

        x = Dense(n_outputs)(lstm_layer)

        self.model = Model(inputs=lstm_input, outputs=x)
        self.batch = batch
        self.epochs = epochs
        self.n_layer = n_layer
        self.lr = lr
        self.Xval = Xval
        self.Yval = Yval
        self.X = X
        self.Y = Y
        self.mask_value = mask_value
        self.min_delta = min_delta
        self.patience = patience

    def trainCallback(self):
        return EarlyStopping(monitor='loss', patience=self.patience, min_delta=self.min_delta)

    def train(self):
        # Getting the untrained model
        empty_model = self.model

        # Initiating the optimizer
        optimizer = keras.optimizers.Adam(learning_rate=self.lr)

        # Compiling the model
        empty_model.compile(optimizer=optimizer,
                            loss=losses.MeanAbsoluteError(),
                            # loss=tf.keras.losses.CategoricalCrossentropy(),
                            metrics=[tf.keras.metrics.SparseCategoricalAccuracy()])

        if (self.Xval is not None) & (self.Yval is not None):
            history = empty_model.fit(
                self.X,
                self.Y,
                epochs=self.epochs,
                batch_size=self.batch,
                validation_data=(self.Xval, self.Yval),
                shuffle=False,
                callbacks=[self.trainCallback()]
            )
        else:
            history = empty_model.fit(
                self.X,
                self.Y,
                epochs=self.epochs,
                batch_size=self.batch,
                shuffle=False,
                callbacks=[self.trainCallback()]
            )

        # Saving to original model attribute in the class
        self.model = empty_model

        # Returning the training history
        return history

    def predict(self, X):
        return self.model.predict(X)

### load model
def load_model():
    filename = 'lstm_model.sav'
    # loaded_model = pickle.load(open(filename, 'rb'))
    loaded_model = keras.models.load_model("deployed_models/Id_prediction_lstm_model.h5")
    # print(loaded_model)
    return loaded_model

### Load Dataset
def load_historic_data():
    pd_final = pd.read_pickle("data/pd_final.pkl")
    return pd_final

### Get prediction
def get_predicted_weather_id():
    """
    :return:
    # Sunny Day - weather_id : 0
    # cloudy Days - weather_id : 1
    # windy Days - weather_id : 2
    # foggy Days - weather_id : 3
    # Rainy Days - weather_id : 4
    # Snowy Days - weather_id : 5
    """
    lst = []
    for time in owm.lag_48():
        lst.append(owm.get_features(time))
    pd_final_test = pd.DataFrame(lst, columns = ['temp', 'day_cos', 'day_sin', 'month_sin',
                                      'month_cos', 'pressure', 'wind_speed', 'weather_main']
                    )
    np_final_test = owm.convert_to_np(pd_final_test)
    X, Y = owm.create_X_Y(np_final_test, 48, n_ahead=1, target_index=7)
    loaded_model =  load_model()
    result = loaded_model.predict(X)
    result = np.around(result).astype(np.uint64)[0][0]
    return result

def map_to_id(pd_final):
    """
    # Sunny Day - weather_id : 0
    # cloudy Days - weather_id : 1
    # windy Days - weather_id : 2
    # foggy Days - weather_id : 3
    # Rainy Days - weather_id : 4
    # Snowy Days - weather_id : 5
    """
    if not type(pd_final) == str:
        sunny = pd_final.weather_main == 'Clear'
        cloudy = pd_final.weather_main == 'Clouds'
        windy = pd_final.weather_main.isin(['Squall', 'Tornado'])
        foggy = pd_final.weather_main.isin(['Mist', 'Haze', 'Dust', 'Fog', 'Smoke'])
        rainy = pd_final.weather_main.isin(['Drizzle', 'Rain', 'Thunderstorm'])
        snowy = pd_final.weather_main.isin(['Snow'])
        pd_final['weather_main'] = pd_final['weather_main'].where(~sunny, 'sunny')
        pd_final['weather_main'] = pd_final['weather_main'].where(~cloudy, 'cloudy')
        pd_final['weather_main'] = pd_final['weather_main'].where(~windy, 'windy')
        pd_final['weather_main'] = pd_final['weather_main'].where(~foggy, 'foggy')
        pd_final['weather_main'] = pd_final['weather_main'].where(~rainy, 'rainy')
        pd_final['weather_main'] = pd_final['weather_main'].where(~snowy, 'snowy')
        conditions = [
            (pd_final['weather_main'] == 'sunny'),
            (pd_final['weather_main'] == 'cloudy'),
            (pd_final['weather_main'] == 'windy'),
            (pd_final['weather_main'] == 'foggy'),
            (pd_final['weather_main'] == 'rainy'),
            (pd_final['weather_main'] == 'snowy')
        ]
        values = [0, 1, 2, 3, 4, 5]
        pd_final['weather_main'] = np.select(conditions, values)
    else:
        pd_final = 'sunny' if pd_final == 'Clear' else pd_final
        pd_final = 'cloudy' if pd_final == 'Clouds'  else pd_final
        pd_final = 'windy' if pd_final in {'Squall', 'Tornado'} else pd_final
        pd_final = 'foggy' if pd_final in {'Mist', 'Haze', 'Dust', 'Fog', 'Smoke'} else pd_final
        pd_final = 'rainy' if pd_final in {'Drizzle', 'Rain', 'Thunderstorm'} else pd_final
        pd_final = 'snowy' if pd_final == 'Snow' else pd_final
        pd_final = 0 if pd_final == 'sunny' else 1 if pd_final == 'cloudy' else 2 if pd_final == 'windy' else 3 \
        if pd_final == 'foggy' else 4 if pd_final == 'rainy' else 5
    return pd_final

def get_predicted_weather_id_2():
    lst = []
    # use current weather information as the baseline data
    from datetime import datetime, timedelta, timezone
    from pyowm.utils import timestamps, formatting
    now = formatting.to_UNIXtime(datetime.now(timezone.utc))
    baseline = owm.get_features(now, keep=True)
    # init the lst of the next 7 hours
    for time in owm.lag_48(lag_time=-7):
        lst.append(owm.get_features(time, keep=True, baseline=baseline))
    pd_final_seven = pd.DataFrame(lst, columns=['temp', 'day_cos', 'day_sin', 'month_sin',
                                               'month_cos', 'pressure', 'wind_speed', 'weather_main']
                                 )
    lst = []
    for time in owm.lag_48(48):
        lst.append(owm.get_features(time, keep=True, baseline=baseline))
    pd_final_test = pd.DataFrame(lst, columns=['temp', 'day_cos', 'day_sin', 'month_sin',
                                               'month_cos', 'pressure', 'wind_speed', 'weather_main']
                                 )
    np_final_test = map_to_id(pd_final_test).values
    results = []
    for counter in range(7):
        # print(counter)
        X, _ = owm.create_X_Y(np_final_test, 48, n_ahead=1, target_index=7)
        # print(X.shape)
        loaded_model = load_model()
        result = loaded_model.predict(X.astype(float))
        # print(result)
        result = np.around(result).astype(np.uint64)[0][0]
        # print(result)
        results.append(result)
        new_instance = np.append(pd_final_seven.values[counter][:-1],result).reshape(-1, 1).T
        np_final_test = np.append(pd_final_test.values[1:], new_instance, axis=0)
    # print(results)
    return results, baseline[7]
# print(get_predicted_weather_id_2())