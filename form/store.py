from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SubmitField, HiddenField
from wtforms.validators import DataRequired


class StoreForm(FlaskForm):
    name = StringField('Название магазина', validators=[DataRequired()])
    address = StringField('Улица и дом', validators=[DataRequired()])
    lat = HiddenField()
    lng = HiddenField()
    submit = SubmitField('Добавить магазин')
