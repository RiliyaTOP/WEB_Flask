import random
import hashlib
import redis

r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

OTP_TTL = 300
MAX_ATTEMPTS = 5
BLOCK_TIME = 300


def create_otp(email):
    code = str(random.randint(100000, 999999))
    hashed = hashlib.sha256(code.encode()).hexdigest()

    r.setex(f"otp:{email}", OTP_TTL, hashed)

    r.delete(f"otp_attempts:{email}")
    r.delete(f"otp_block:{email}")

    return code


def is_blocked(email):
    return r.exists(f"otp_block:{email}")


def verify_otp(email, code):
    if is_blocked(email):
        return "blocked"

    saved = r.get(f"otp:{email}")
    if not saved:
        return "expired"

    attempts_key = f"otp_attempts:{email}"
    attempts = r.incr(attempts_key)
    r.expire(attempts_key, OTP_TTL)

    if attempts > MAX_ATTEMPTS:
        r.setex(f"otp_block:{email}", BLOCK_TIME, 1)
        return "blocked"

    if hashlib.sha256(code.encode()).hexdigest() != saved:
        return "invalid"

    # код верный, убираем всё связанное с этим otp
    r.delete(f"otp:{email}")
    r.delete(attempts_key)

    return "ok"


def delete_otp(email):
    r.delete(f"otp:{email}")
    r.delete(f"otp_attempts:{email}")
