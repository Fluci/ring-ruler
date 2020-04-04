import datetime

def log(msg):
    now = datetime.datetime.now()
    print(f"{now.year}.{now.month}.{now.day} {now.hour}:{now.minute}:{now.second}: {msg}")

