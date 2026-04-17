from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (EmailField, SelectField, PasswordField, StringField, BooleanField, SubmitField, IntegerField,
                     HiddenField, RadioField)
from wtforms.validators import DataRequired, Optional


class NewProductsForm(FlaskForm):
    name = StringField('Название', validators=[DataRequired()])
    price = IntegerField("Цена", validators=[DataRequired()])
    quantity = IntegerField("Количество", validators=[DataRequired()])
    photo = FileField('Фото товара', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 'Только изображения')])

    submit = SubmitField('Разместить продукт')

class Supply(FlaskForm):
    mode = RadioField(
        'Искать по',
        choices=[
            ('name', 'Название'),
            ('id', 'ID')
        ],
        validators=[DataRequired()]
    )
    name = StringField('Название', validators=[Optional()])
    product_id = IntegerField('ID товара', validators=[Optional()])
    submit = SubmitField('Найти')

    def validate(self, extra_validators=None):
        if not super().validate(extra_validators):
            return False

        if self.mode.data == 'name' and not self.name.data:
            self.name.errors.append('Введите название')
            return False

        if self.mode.data == 'id' and not self.product_id.data:
            self.product_id.errors.append('Введите ID')
            return False

        return True