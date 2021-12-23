### Load Pre-trained Model
import tensorflow as tf
from tensorflow import keras
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import pickle
import owm

### Init Model
class NNMultistepModel_tp():

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
        empty_model.compile(loss=losses.MeanAbsoluteError(), optimizer=optimizer)

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

### Load Model
def load_model():
    filename = "deployed_models/Temperature_prediction_lstm_model.h5"
    # loaded_model = pickle.load(open(filename, 'rb'))
    loaded_model = keras.models.load_model(filename)
    # print(loaded_model)
    return loaded_model

### Get prediction
def get_predicted_temperature():
    """
    :return:
    """
    lst = []
    # use current weather information as the baseline data
    from datetime import datetime, timedelta, timezone
    from pyowm.utils import timestamps, formatting
    now = formatting.to_UNIXtime(datetime.now(timezone.utc))
    baseline = owm.get_features(now, keep=False)
    # init the lst of the next 7 hours
    for time in owm.lag_48(lag_time=-7):
        lst.append(owm.get_features(time, keep=False, baseline=baseline))
    pd_final_seven = pd.DataFrame(lst, columns=['temp', 'day_cos', 'day_sin', 'month_sin',
                                                'month_cos', 'pressure', 'wind_speed']
                                  )
    lst = []
    for time in owm.lag_48(48):
        lst.append(owm.get_features(time, keep=False, baseline=baseline))
    pd_final_test = pd.DataFrame(lst, columns=['temp', 'day_cos', 'day_sin', 'month_sin',
                                               'month_cos', 'pressure', 'wind_speed']
                                 )
    np_final_test = pd_final_test.values
    results = []
    for counter in range(7):
        X, _ = owm.create_X_Y( np_final_test, 48, n_ahead=1, target_index=0)
        # print(X.shape)
        loaded_model = load_model()
        result = loaded_model.predict(X)[0][0]
        temperature_to_use = np.round(result-273.16, 2)
        # print(result)
        results.append(temperature_to_use)
        new_instance = np.append(result, pd_final_seven.values[counter][1:]).reshape(-1, 1).T
        np_final_test = np.append(pd_final_test.values[1:], new_instance, axis=0)
    # print(results)
    baseline_temp = np.round(baseline[0] - 273.16, 2)
    return results, baseline_temp
# get_predicted_temperature()