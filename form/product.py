from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (EmailField, SelectField, PasswordField, StringField, BooleanField, SubmitField, IntegerField,
                     HiddenField, RadioField, TextAreaField)
from wtforms.validators import DataRequired, Optional

# список категорий используется в формах и в каталоге для фильтрации
CATEGORIES = ['Одежда', 'Еда', 'Напитки', 'Электроника', 'Книги', 'Спорт', 'Дом и сад', 'Красота', 'Игрушки']
# первым идёт пустой вариант — значит категория не выбрана
CATEGORY_CHOICES = [('', 'Без категории')] + [(c, c) for c in CATEGORIES]


# форма добавления нового товара в каталог
class NewProductsForm(FlaskForm):
    name = StringField('Название', validators=[DataRequired()])
    price = IntegerField("Цена", validators=[DataRequired()])
    quantity = IntegerField("Количество", validators=[DataRequired()])
    # категория необязательна — товар можно добавить без неё
    category = SelectField('Категория', choices=CATEGORY_CHOICES, validators=[Optional()])
    description = TextAreaField('Описание', validators=[Optional()])
    # допускаем только картинки, остальное FileAllowed отклонит ещё на этапе валидации
    photo = FileField('Фото товара', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 'Только изображения')])

    submit = SubmitField('Разместить продукт')


# форма редактирования существующего товара — поля те же, кнопка другая
class EditProductForm(FlaskForm):
    name = StringField('Название', validators=[DataRequired()])
    price = IntegerField("Цена", validators=[DataRequired()])
    quantity = IntegerField("Количество", validators=[DataRequired()])
    category = SelectField('Категория', choices=CATEGORY_CHOICES, validators=[Optional()])
    description = TextAreaField('Описание', validators=[Optional()])
    # при редактировании фото необязательно — если не загрузили, старое остаётся
    photo = FileField('Новое фото', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 'Только изображения')])

    submit = SubmitField('Сохранить')

# форма поиска товара для раздела поставок
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
        # стандартная валидация сначала
        if not super().validate(extra_validators):
            return False

        # дополнительно проверяем что нужное поле заполнено под выбранный режим
        if self.mode.data == 'name' and not self.name.data:
            self.name.errors.append('Введите название')
            return False

        if self.mode.data == 'id' and not self.product_id.data:
            self.product_id.errors.append('Введите ID')
            return False

        return True
