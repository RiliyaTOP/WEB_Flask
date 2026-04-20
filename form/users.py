from flask_wtf import FlaskForm
from wtforms import (EmailField, SelectField, PasswordField, StringField, BooleanField, SubmitField)
from wtforms.validators import DataRequired, Optional

class LoginForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')

class RegistrationForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    name = StringField('Имя', validators=[DataRequired()])
    submit = SubmitField('Зарегистрироваться')

class StaffRegistrationForm(FlaskForm):
    name = StringField('Полное имя', validators=[DataRequired()])
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    role = SelectField(
        'Должность (роль)',
        choices=[
            ('manager', 'Менеджер'),
            ('warehouse', 'Складской работник'),
            ('support', 'Поддержка'),
            ('courier', 'Курьер'),
        ],
        validators=[DataRequired()]
    )
    code = StringField('Код сотрудника', validators=[DataRequired()])
    submit = SubmitField('Зарегистрировать сотрудника')