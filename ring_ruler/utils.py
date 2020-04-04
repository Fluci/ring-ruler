import datetime

def log(msg):
    now = datetime.datetime.now()
    print(f"{now.year:04}.{now.month:02}.{now.day:02} {now.hour:02}:{now.minute:02}:{now.second:02}: {msg}")

