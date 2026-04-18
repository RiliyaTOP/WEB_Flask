import redis
import random
import hashlib

r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

OTP_TTL = 300
MAX_ATTEMPTS = 5


def create_otp(email: str):
    code = str(random.randint(100000, 999999))
    hashed = hashlib.sha256(code.encode()).hexdigest()

    r.setex(f"otp:{email}", OTP_TTL, hashed)
    r.set(f"otp_attempts:{email}", 0, ex=OTP_TTL)

    return code


def verify_otp(email: str, code: str):
    saved = r.get(f"otp:{email}")
    if not saved:
        return "expired"

    attempts = r.get(f"otp_attempts:{email}") or 0
    attempts = int(attempts)

    if attempts >= MAX_ATTEMPTS:
        return "blocked"

    if hashlib.sha256(code.encode()).hexdigest() != saved:
        r.set(f"otp_attempts:{email}", attempts + 1, ex=300)
        return "invalid"

    r.delete(f"otp:{email}")
    r.delete(f"otp_attempts:{email}")

    return "ok"