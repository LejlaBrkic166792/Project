from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from .models import User  
from sqlalchemy import select

class RegisterForm(FlaskForm):
    
    username = StringField(
        label="Username",
        validators=[InputRequired(), Length(min=4, max=20)],
        render_kw={"placeholder": "Scegli un username"}
    )
    
    password = PasswordField(
        label="Password",
        validators=[InputRequired(), Length(min=8, max=20)],
        render_kw={"placeholder": "Scegli una password"}
    )
    
    submit = SubmitField("Registrati")

    def validate_username(self, username):
        from .db import db 
        stmt = select(User).where(User.username == username.data)
        existing_user = db.session.execute(stmt).scalar_one_or_none()
        if existing_user:
            raise ValidationError("Questo username è già occupato.")

class LoginForm(FlaskForm):
    username = StringField(
        label="Username",
        validators=[InputRequired()],
        render_kw={"placeholder": "Inserisci username"}
    )
    
    password = PasswordField(
        label="Password",
        validators=[InputRequired()],
        render_kw={"placeholder": "Inserisci password"}
    )
    
    submit = SubmitField("Accedi")