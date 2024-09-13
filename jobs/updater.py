from datetime import datetime,date
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from .jobs import schedule_api

def start():
	scheduler = BackgroundScheduler()
	scheduler.add_job(schedule_api,trigger=CronTrigger(
        day_of_week="fri", hour="10", minute="30",second=00
      ),
	  max_instances=1,replace_existing=True,)
	scheduler.add_job(schedule_api,trigger=CronTrigger(
        day_of_week="fri", hour="13", minute="00",second=00
      ),
	  max_instances=1,replace_existing=True,)
	scheduler.start()