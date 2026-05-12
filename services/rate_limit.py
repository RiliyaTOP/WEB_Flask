import redis

r = redis.Redis(host='localhost', port=6379, db=0)

# одну минуту нельзя запрашивать новый код — защита от спама на почту
RATE_TTL = 60


def check_rate(email):
    # если флаг есть — значит код уже запрашивался меньше минуты назад
    return r.exists(f"rate:{email}")


def set_rate(email):
    # ставим флаг на 60 секунд, после чего он сам удалится
    r.setex(f"rate:{email}", RATE_TTL, 1)
