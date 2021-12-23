from datetime import datetime, timezone

import numpy as np
import pandas as pd
import tensorflow as tf
from keras import losses
from keras.callbacks import EarlyStopping
from keras.layers import Dense, LSTM
from keras.models import Input, Model
from pyowm.utils import formatting
from pyspark import SparkContext, SparkConf
from pyspark.sql import SQLContext
from pyspark.streaming import StreamingContext
from tensorflow import keras

import owm
from get_prediction import map_to_id


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


def load_id_model():
    loaded_model = keras.models.load_model("deployed_models/Id_prediction_lstm_model.h5")
    return loaded_model


def load_temp_model():
    loaded_model = keras.models.load_model("deployed_models/Temperature_prediction_lstm_model.h5")
    return loaded_model


def save_temp():
    lst = []
    now = formatting.to_UNIXtime(datetime.now(timezone.utc))
    baseline = owm.get_features(now, keep=False)
    for time in owm.lag_48(48):
        lst.append(owm.get_features(time, keep=False, baseline=baseline))
    pd_final_test = pd.DataFrame(lst, columns=['temp', 'day_cos', 'day_sin', 'month_sin',
                                               'month_cos', 'pressure', 'wind_speed']
                                 )
    np_final_test = pd_final_test.values
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H")
    np.savetxt(f"./input_data/{now}_lag48_temp.csv", np_final_test, delimiter=',')


def save_id():
    lst = []
    now = formatting.to_UNIXtime(datetime.now(timezone.utc))
    baseline = owm.get_features(now, keep=True)
    for time in owm.lag_48(48):
        lst.append(owm.get_features(time, keep=True, baseline=baseline))
    pd_final_test = pd.DataFrame(lst, columns=['temp', 'day_cos', 'day_sin', 'month_sin',
                                               'month_cos', 'pressure', 'wind_speed', 'weather_main']
                                 )
    np_final_test = map_to_id(pd_final_test).values
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H")
    np.savetxt(f"./input_data/{now}_lag48_weather.csv", np_final_test, delimiter=',')


def rdd_processing(rdd, sql):
    if not rdd.isEmpty():
        rdd = rdd.map(lambda ln: ln.split(',', -1))
        df_final_test = sql.createDataFrame(rdd)
        # df_final_test.show()
        np_final_test = np.array(df_final_test.toPandas()).astype(float)
        now = formatting.to_UNIXtime(datetime.now(timezone.utc))

        if len(rdd.take(1)[0]) == 8:
            lst = []
            # use current weather information as the baseline data
            baseline = owm.get_features(now, keep=True)
            # init the lst of the next 7 hours
            for time in owm.lag_48(lag_time=-7):
                lst.append(owm.get_features(time, keep=True, baseline=baseline))

            columns = ['temp', 'day_cos', 'day_sin', 'month_sin', 'month_cos', 'pressure', 'wind_speed', 'weather_main']
            pd_final_seven = pd.DataFrame(lst, columns=columns)
            df_final_seven = sql.createDataFrame(pd_final_seven, schema=columns)

            results = []
            loaded_model = load_id_model()
            for counter in range(7):
                X, _ = owm.create_X_Y(np_final_test, 48, n_ahead=1, target_index=7)
                result = loaded_model.predict(X.astype(float))
                result = np.around(result).astype(np.uint64)[0][0]
                results.append(result)
                # new_instance = np.append(pd_final_seven.values[counter][:-1], result).reshape(-1, 1).T
                new_instance = np.append(np.array(df_final_seven.head(counter + 1)[-1][:-1]), result).reshape(-1, 1).T
                # np_final_test = np.append(pd_final_test.values[1:], new_instance, axis=0)
                np_final_test = np.append(np.array(df_final_test.tail(47)), new_instance, axis=0)

            now = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H")
            print('Writing weather result...')
            with open(f"predicted_results/{now}_pred_id.txt", "w") as f:
                f.write(str(map_to_id(baseline[7])))
                for id in results:
                    f.write("\n" + str(id))
        elif len(rdd.take(1)[0]) == 7:
            lst = []
            # use current weather information as the baseline data
            baseline = owm.get_features(now, keep=False)
            # init the lst of the next 7 hours
            for time in owm.lag_48(lag_time=-7):
                lst.append(owm.get_features(time, keep=False, baseline=baseline))

            columns = ['temp', 'day_cos', 'day_sin', 'month_sin', 'month_cos', 'pressure', 'wind_speed']
            pd_final_seven = pd.DataFrame(lst, columns=columns)
            df_final_seven = sql.createDataFrame(pd_final_seven, schema=columns)

            results = []
            loaded_model = load_temp_model()
            for counter in range(7):
                X, _ = owm.create_X_Y(np_final_test, 48, n_ahead=1, target_index=0)
                result = loaded_model.predict(X.astype(float))[0][0]
                temperature_to_use = np.round(result - 273.15, 2)
                results.append(temperature_to_use)
                # new_instance = np.append(result, pd_final_seven.values[counter][1:]).reshape(-1, 1).T
                new_instance = np.append(result, np.array(df_final_seven.head(counter + 1)[-1][1:])).reshape(-1, 1).T
                # np_final_test = np.append(pd_final_test.values[1:], new_instance, axis=0)
                np_final_test = np.append(np.array(df_final_test.tail(47)), new_instance, axis=0)
            baseline_temp = np.round(baseline[0] - 273.15, 2)

            now = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H")
            print('Writing temperature result...')
            with open(f"predicted_results/{now}_pred_temp.txt", "w") as f:
                f.write(str(baseline_temp))
                for temp in results:
                    f.write("\n" + str(temp))

    else:
        pass


conf = SparkConf()
conf.setMaster('local[*]')
conf.setAppName('test')

sc = SparkContext(conf=conf)
sc.setLogLevel("ERROR")
sql = SQLContext(sc)

# # save_temp()
# # save_id()
# now = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H")
#
# rdd = sc.textFile(f"./input_data/{now}_lag48_weather.csv")
# rdd_processing(rdd, sql)
# # res = get_predicted_temperatures.get_predicted_temperature()
# # print(res)
#
# rdd = sc.textFile(f"./input_data/{now}_lag48_weather.csv")
# rdd_processing(rdd, sql)
# # res = get_prediction.get_predicted_weather_id_2()
# # print(res)


ssc = StreamingContext(sc, 10)

lst = []
for time in owm.lag_48():
    lst.append(owm.get_features(time))

dstream = ssc.textFileStream("./input_data")
dstream.foreachRDD(lambda rdd: print(rdd.collect()))
dstream.pprint()

dstream.foreachRDD(lambda rdd: rdd_processing(rdd, sql))

ssc.start()
ssc.awaitTermination()
