from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SubmitField, SelectField, DecimalField, DateField, IntegerField, EmailField, BooleanField
from wtforms.validators import DataRequired, NumberRange, Email, InputRequired
from app.models import Ingredient, IngredientCategory, PlatCategory, SousPreparation

from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SelectField, BooleanField, SubmitField,SelectMultipleField
from wtforms.validators import DataRequired, InputRequired, NumberRange, Optional



class ReceptionForm(FlaskForm):

    ingredient_id = SelectField('Ingrédient', validators=[DataRequired()])
    quantity = DecimalField('Quantité', places=2, validators=[DataRequired()])
    price = DecimalField('Prix', places=2, validators=[DataRequired()])

    default_marque = StringField('Marque par défaut', render_kw={'readonly': True})  # Affichage de la marque par défaut
    actual_marque = StringField('Marque achetée')  # Champ pour saisir la marque réellement achetée
    submit = SubmitField('Ajouter la Réception')


class BonReceptionForm(FlaskForm):
    fournisseur = SelectField('Fournisseur', coerce=int, validators=[DataRequired()])
    destination = SelectField('Destination',
        choices=[
            ('Cuisine', 'Cuisine'),
            ('Patisserie', 'Patisserie'),
            ('Sushi', 'Sushi'),
            ('PIZZA', 'PIZZA'),
            ('Bar', 'Bar'),
            ('La Salle', 'La Salle')
        ],
        validators=[DataRequired()]
    )
    numero_bon = StringField('Numéro de Bon', validators=[DataRequired()])
    date_creation = DateField('Date de création', format='%Y-%m-%d', default=datetime.utcnow)
    submit = SubmitField('Ajouter Bon de Réception')

# ***************************************************************************************************************************

class PlatForm(FlaskForm):
    name = StringField('Nom du Plat', validators=[DataRequired()])
    status = BooleanField('Status')
    categoryPlat = SelectField(
        'Catégorie',
        choices=[(category.name, category.value) for category in PlatCategory]
    ,validators=[DataRequired()])
    prix = StringField('Prix de Vente', validators=[DataRequired()])

class UpdatePlatForm(FlaskForm):
    name = StringField('Nom du Plat', validators=[DataRequired()])
    prix = DecimalField('Prix du Plat', validators=[DataRequired()])
    categoryPlat = SelectField('Catégorie', choices=[(cat.name, cat.value) for cat in PlatCategory])
    submit = SubmitField('Mettre à Jour Plat')

class UpdateIngredientForm(FlaskForm):
    ingredient_id = SelectField('Ingrédient', coerce=int, validators=[DataRequired()])
    quantity = IntegerField('Quantité', validators=[DataRequired()])
    submit = SubmitField('Mettre à jour')


class AddIngredientsForm(FlaskForm):
    ingredient_id = SelectField('Sélectionner un Ingrédient', choices=[], coerce=int, validators=[DataRequired()])
    quantity = DecimalField('Quantité', validators=[DataRequired()], places=2)
    submit = SubmitField('Ajouter Ingrédient')


class AddSousPreparationsForm(FlaskForm):
    sous_preparation_id = SelectField('Sélectionner une Sous-Préparation', choices=[], coerce=int, validators=[DataRequired()])
    quantity = DecimalField('Quantité', validators=[DataRequired()], places=2)
    submit = SubmitField('Ajouter Sous-Préparation')

class UpdateSousPreparationForm(FlaskForm):
    name = StringField('Nom de la Sous-Préparation', validators=[DataRequired()])
    total_cost = DecimalField('Coût Total', validators=[DataRequired()])
    submit = SubmitField('Mettre à Jour Sous-Préparation')





#*************************************************************************************************


class FournisseurForm(FlaskForm):
    nom = StringField('Nom', validators=[DataRequired()])
    telephone = StringField('Numéro de Téléphone')
    adresse = StringField('Adresse')
    email = EmailField('Email', validators=[Email()])
    categories = SelectMultipleField(
        'Catégories',
        choices=[(category.name, category.value) for category in IngredientCategory],
        validators=[DataRequired()]
    )

    submit = SubmitField('Ajouter')


class UpdateFournisseurForm(FlaskForm):
    nom = StringField('Nom', validators=[DataRequired()])
    telephone = StringField('Numéro de Téléphone', validators=[DataRequired()])
    adresse = StringField('Adresse', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    categories = SelectMultipleField(
        'Catégories',
        choices=[(category.name, category.value) for category in IngredientCategory],
        validators=[DataRequired()]
    )
    submit = SubmitField('Mettre à Jour')


#*************************************************************************************

class TransformationForm(FlaskForm):
    main_ingredient = SelectField('Ingrédient Principal', coerce=int, validators=[DataRequired()],)
    quantity_to_subtract = IntegerField('Quantité à soustraire (kg)', validators=[DataRequired()])

    secondary_ingredient_1 = SelectField('Ingrédient Secondaire 1', coerce=int, validators=[DataRequired()])
    percentage_1 = FloatField('Pourcentage 1', validators=[DataRequired(), NumberRange(min=0, max=100)])

    secondary_ingredient_2 = SelectField('Ingrédient Secondaire 2', coerce=int, validators=[DataRequired()])
    percentage_2 = FloatField('Pourcentage 2', validators=[DataRequired(), NumberRange(min=0, max=100)])



    submit = SubmitField('Ajouter Transformation')

    def __init__(self, *args, **kwargs):
        super(TransformationForm, self).__init__(*args, **kwargs)
        # Remplir le champ des ingrédients depuis la base de données
        self.main_ingredient.choices = [(ingredient.id, ingredient.name) for ingredient in Ingredient.query.all()]
        self.secondary_ingredient_1.choices = self.main_ingredient.choices
        self.secondary_ingredient_2.choices = self.main_ingredient.choices


#******************* Sous préparation sous une autre ********************



class SousPreparationSousForm(FlaskForm):
    sous_preparation_id = SelectField(
        'Sous-Préparation Composante',
        coerce=int,
        validators=[DataRequired()]
    )
    quantity = DecimalField(
        'Quantité',
        validators=[DataRequired(), NumberRange(min=0, message="La quantité doit être positive.")]
    )
    submit = SubmitField('Ajouter Sous-Préparation')

    def __init__(self, *args, **kwargs):
        super(SousPreparationSousForm, self).__init__(*args, **kwargs)
        self.sous_preparation_id.choices = [
            (sous_prep.id, sous_prep.name) for sous_prep in SousPreparation.query.all()
        ]
