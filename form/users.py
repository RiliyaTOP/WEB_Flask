from flask_wtf import FlaskForm
from wtforms import (EmailField, SelectField, PasswordField, StringField, BooleanField, SubmitField)
from wtforms.validators import DataRequired, Optional

# форма входа — используется для сотрудников и как запасной вариант для покупателей
class LoginForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    # галочка передаётся в login_user, продлевает сессию на 7 дней
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')

# форма регистрации обычного покупателя
class RegistrationForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    name = StringField('Имя', validators=[DataRequired()])
    submit = SubmitField('Зарегистрироваться')

# форма регистрации сотрудника — дополнительно требует роль и табельный код
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
    # табельный код проверяется при регистрации — вводится только когда есть реальный код
    code = StringField('Код сотрудника', validators=[DataRequired()])
    submit = SubmitField('Зарегистрировать сотрудника')
