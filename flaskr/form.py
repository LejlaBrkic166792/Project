from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from .models import User  # Serve per il controllo dello username esistente

class RegisterForm(FlaskForm):
    # Definizione dei campi
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

    # VALIDAZIONE PERSONALIZZATA:
    # Flask-WTF cerca metodi che iniziano con 'validate_' + nome_campo
    def validate_username(self, username):
        # Cerchiamo nel DB se lo username inserito dall'utente è già presente
        existing_user = User.query.filter_by(username=username.data).first()
        if existing_user:
            # Se esiste, lanciamo un errore che verrà mostrato nel template HTML
            raise ValidationError("Questo username è già occupato. Scegline un altro.")

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