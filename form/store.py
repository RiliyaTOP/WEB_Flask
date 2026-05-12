from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SubmitField, HiddenField
from wtforms.validators import DataRequired


class StoreForm(FlaskForm):
    name = StringField('Название магазина', validators=[DataRequired()])
    address = StringField('Улица и дом', validators=[DataRequired()])
    # координаты заполняются автоматически через геокодинг Яндекс Карт,
    # пользователь их не вводит руками — поля скрытые
    lat = HiddenField()
    lng = HiddenField()
    submit = SubmitField('Добавить магазин')
