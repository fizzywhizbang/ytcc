#!/usr/bin/env python3
from apscheduler.schedulers.blocking import BlockingScheduler
import os

def channels_update():
    os.system('./ytcc.py -u -jd')


os.system('./ytcc.py -u -jd')
scheduler = BlockingScheduler()
scheduler.add_job(channels_update, 'interval', hours=1)
scheduler.start()