from flask_mail import Message

def send_otp_email(mail, email, code):
    msg = Message(
        subject="Ваш код входа",
        recipients=[email]
    )

    msg.body = f"Код входа: {code}\nДействует 5 минут."

    mail.send(msg)