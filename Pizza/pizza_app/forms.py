from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    SelectField,
    IntegerField,
    TextAreaField,
    BooleanField,
    SubmitField,
)
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    Length,
    NumberRange,
    ValidationError,
)

from models import User


class RegistrationForm(FlaskForm):
    username = StringField(
        "Username", validators=[DataRequired(), Length(min=3, max=80)]
    )
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField(
        "Password", validators=[DataRequired(), Length(min=8, max=128)]
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
    )
    submit = SubmitField("Create Account")

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError("That username is already taken.")

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError("An account with that email already exists.")


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Stay signed in")
    submit = SubmitField("Log In")


PIZZA_SIZES = [
    ("small", "Small (10\")"),
    ("medium", "Medium (12\")"),
    ("large", "Large (14\")"),
    ("xl", "Extra Large (16\")"),
]

PIZZA_CRUSTS = [
    ("thin", "Thin Crust"),
    ("hand_tossed", "Hand Tossed"),
    ("deep_dish", "Deep Dish"),
    ("stuffed", "Stuffed Crust"),
    ("gluten_free", "Gluten Free"),
]


class PizzaOrderForm(FlaskForm):
    size = SelectField("Size", choices=PIZZA_SIZES, validators=[DataRequired()])
    crust = SelectField("Crust", choices=PIZZA_CRUSTS, validators=[DataRequired()])
    toppings = StringField(
        "Toppings",
        validators=[Length(max=255)],
        description="Comma-separated, e.g. pepperoni, mushroom, olives",
    )
    quantity = IntegerField(
        "Quantity",
        validators=[DataRequired(), NumberRange(min=1, max=20)],
        default=1,
    )
    notes = TextAreaField("Special Instructions", validators=[Length(max=1000)])
    submit = SubmitField("Save Order")
