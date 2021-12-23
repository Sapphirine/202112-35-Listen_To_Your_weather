from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime, timedelta, timezone
from get_prediction import map_to_id, get_predicted_weather_id_2
from get_predicted_temperatures import *

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

scheduler = BlockingScheduler()
# scheduler.add_job(test_job, 'interval', minutes=1,
#                   start_date='2021-12-13 15:05:00', timezone='UTC')
scheduler.add_job(some_job, 'interval', hours=1,
                  next_run_time=datetime.now(),
                  # start_date='2021-12-14 20:01:00',
                  timezone='UTC')
scheduler.start()
