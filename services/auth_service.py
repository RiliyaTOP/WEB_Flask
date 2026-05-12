import redis
import random
import hashlib

# отдельное подключение к Redis для этого сервиса
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# время жизни кода — 5 минут
OTP_TTL = 300
# максимальное количество неверных попыток перед блокировкой
MAX_ATTEMPTS = 5


def create_otp(email: str):
    # генерируем код и сразу хэшируем его перед сохранением
    code = str(random.randint(100000, 999999))
    hashed = hashlib.sha256(code.encode()).hexdigest()

    r.setex(f"otp:{email}", OTP_TTL, hashed)
    # счётчик попыток обнуляем при каждом новом коде
    r.set(f"otp_attempts:{email}", 0, ex=OTP_TTL)

    return code


def verify_otp(email: str, code: str):
    saved = r.get(f"otp:{email}")
    if not saved:
        # ключ в Redis не найден — код истёк или ещё не запрашивался
        return "expired"

    attempts = r.get(f"otp_attempts:{email}") or 0
    attempts = int(attempts)

    if attempts >= MAX_ATTEMPTS:
        return "blocked"

    if hashlib.sha256(code.encode()).hexdigest() != saved:
        # увеличиваем счётчик неверных попыток
        r.set(f"otp_attempts:{email}", attempts + 1, ex=300)
        return "invalid"

    # всё верно — удаляем код чтобы нельзя было войти по нему повторно
    r.delete(f"otp:{email}")
    r.delete(f"otp_attempts:{email}")

    return "ok"
