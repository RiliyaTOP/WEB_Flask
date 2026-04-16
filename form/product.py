from flask_wtf import FlaskForm
from wtforms import (EmailField, SelectField, PasswordField, StringField, BooleanField, SubmitField, IntegerField)
from wtforms.validators import DataRequired



class NewProductsForm(FlaskForm):
    name = StringField('Название', validators=[DataRequired()])
    price = IntegerField("Цена", validators=[DataRequired()])
    quantity = IntegerField("Количество", validators=[DataRequired()])
    # category = Column(Enum("admin", "user", "manager", "warehouse", "support", "courier", name="user_roles"), nullable=True)

    submit = SubmitField('Раазместить продукт')