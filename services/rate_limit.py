import redis

r = redis.Redis(host='localhost', port=6379, db=0)

RATE_TTL = 60


def check_rate(email):
    return r.exists(f"rate:{email}")


def set_rate(email):
    r.setex(f"rate:{email}", RATE_TTL, 1)