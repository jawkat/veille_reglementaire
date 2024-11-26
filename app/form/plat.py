from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SubmitField, SelectField, DecimalField, DateField, IntegerField, EmailField, FieldList,FormField, SelectMultipleField
from wtforms.validators import DataRequired, NumberRange, Email, InputRequired
from app.models import Ingredient, IngredientCategory, PlatCategory




class PlatForm(FlaskForm):
    name = StringField('Nom du Plat', validators=[DataRequired()])
    categoryPlat = SelectField(
        'Catégorie',
        choices=[(category.name, category.value) for category in PlatCategory]
    ,validators=[DataRequired()])
    prix = StringField('Prix de Vente', validators=[DataRequired()])
    submit = SubmitField('Ajouter Plat')

class UpdatePlatForm(FlaskForm):
    name = StringField('Nom du Plat', validators=[DataRequired()])
    prix = DecimalField('Prix du Plat', validators=[DataRequired()])
    categoryPlat = SelectField('Catégorie', choices=[(cat.name, cat.value) for cat in PlatCategory])
    submit = SubmitField('Mettre à Jour Plat')


class AddIngredientsForm(FlaskForm):
    ingredient_id = SelectField('Sélectionner un Ingrédient', choices=[], coerce=int, validators=[DataRequired()])
    quantity = DecimalField('Quantité', validators=[DataRequired()], places=2)
    submit = SubmitField('Ajouter Ingrédient')



class AddSousPreparationsForm(FlaskForm):
    sous_preparation_id = SelectField('Sélectionner une Sous-Préparation', choices=[], coerce=int, validators=[DataRequired()])
    quantity = DecimalField('Quantité', validators=[DataRequired()], places=2)
    submit = SubmitField('Ajouter Sous-Préparation')
