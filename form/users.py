from flask_wtf import FlaskForm
from wtforms import (EmailField, SelectField, PasswordField, StringField, BooleanField, SubmitField)
from wtforms.validators import DataRequired

class LoginForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')

class RegistrationForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    name = StringField('Имя', validators=[DataRequired()])
    role = SelectField(
        'Роль',
        choices=[
            ('manager', 'Манеджер'),
            ('warehouse', 'Складской помощник'),
            ('support', 'Поддержка'),
            ('courier', 'Курьер')
        ],
        validators=[DataRequired()]
    )
    submit = SubmitField('Войти')