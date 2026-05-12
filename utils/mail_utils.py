from flask_mail import Message

def send_otp_email(mail, email, code):
    # формируем письмо с кодом и отправляем через Flask-Mail
    msg = Message(
        subject="Ваш код входа",
        recipients=[email]
    )

    # простой текст без HTML — работает везде и не попадает в спам
    msg.body = f"Код входа: {code}\nДействует 5 минут."

    mail.send(msg)
