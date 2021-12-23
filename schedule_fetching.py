from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime, timedelta, timezone
from get_prediction import map_to_id, get_predicted_weather_id_2
from get_predicted_temperatures import *
from pyowm.utils import formatting

def some_job():
    print('Getting prediction...')
    ids, id = get_predicted_weather_id_2()
    temp, curr_temp = get_predicted_temperature()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H")
    print('Writing result...')
    predfile = open(f"predicted_results/{now}_pred_id.txt", "w")
    to_id = map_to_id(id)
    predfile.write(str(to_id)+',' +str(curr_temp))
    for t, id in zip(temp, ids):
        predfile.write("\n" + str(id) + ',' + str(t))
    # predfile.write("\n" + str(curr_temp))
    predfile.close()
    print(f"Done! File predicted_results/{now}_pred_id.txt is written in this folder")

def test_job():
    # https://stackoverflow.com/questions/66662408/how-can-i-run-task-every-10-minutes-on-the-5s-using-blockingscheduler
    now = datetime.now(timezone.utc)
    print(now)

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


def save_job():
    save_temp()
    save_id()
    print(f"Done! File written")



scheduler = BlockingScheduler()
# scheduler.add_job(test_job, 'interval', minutes=1,
#                   start_date='2021-12-13 15:05:00', timezone='UTC')
scheduler.add_job(save_job, 'interval', hours=1,
                  next_run_time=datetime.now(),
                  # start_date='2021-12-14 20:01:00',
                  timezone='UTC')
scheduler.start()
