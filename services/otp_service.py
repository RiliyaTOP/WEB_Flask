import random
import hashlib
import redis

# подключаемся к локальному Redis — он хранит коды и счётчики попыток
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# код живёт 5 минут, после этого считается просроченным
OTP_TTL = 300
# после 5 неверных попыток аккаунт блокируется
MAX_ATTEMPTS = 5
# на сколько секунд блокируем после превышения попыток
BLOCK_TIME = 300


def create_otp(email):
    # генерируем шестизначный код
    code = str(random.randint(100000, 999999))
    # в Redis храним только хэш, не сам код — чтобы при утечке Redis нельзя было им воспользоваться
    hashed = hashlib.sha256(code.encode()).hexdigest()

    r.setex(f"otp:{email}", OTP_TTL, hashed)

    # сбрасываем старые счётчики при каждом новом запросе кода
    r.delete(f"otp_attempts:{email}")
    r.delete(f"otp_block:{email}")

    # возвращаем открытый код — он нужен только для отправки по почте
    return code


def is_blocked(email):
    # проверяем есть ли флаг блокировки в Redis
    return r.exists(f"otp_block:{email}")


def verify_otp(email, code):
    # сначала проверяем блокировку, чтобы не тратить время на остальное
    if is_blocked(email):
        return "blocked"

    saved = r.get(f"otp:{email}")
    if not saved:
        # ключ не найден — либо истёк, либо вообще не запрашивался
        return "expired"

    attempts_key = f"otp_attempts:{email}"
    attempts = r.incr(attempts_key)
    r.expire(attempts_key, OTP_TTL)

    if attempts > MAX_ATTEMPTS:
        # слишком много попыток — блокируем и просим подождать
        r.setex(f"otp_block:{email}", BLOCK_TIME, 1)
        return "blocked"

    if hashlib.sha256(code.encode()).hexdigest() != saved:
        return "invalid"

    # код верный, убираем всё связанное с этим otp
    r.delete(f"otp:{email}")
    r.delete(attempts_key)

    return "ok"


def delete_otp(email):
    # принудительно удаляем код и счётчик — используется если нужно сбросить вручную
    r.delete(f"otp:{email}")
    r.delete(f"otp_attempts:{email}")
