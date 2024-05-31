import logging, datetime, os, sys
from telebot import types

def setup():
    now = datetime.datetime.now()
    os.makedirs("tmp/logs", exist_ok=True)

    logging_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    logging.basicConfig(filename="tmp/logs/{year}-{month}-{day}-{hour}-{minute}-{second}.txt".format(
        year=now.year,
        month=now.month,
        day=now.day,
        hour=now.hour,
        minute=now.minute,
        second=now.second
    ), format=logging_format)
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(logging_format)
    handler.setFormatter(formatter)
    root.addHandler(handler)