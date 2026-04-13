from .db import db
#con usermixin ottiene automaticamente i quattro metodi richiesti dalla documentazione di Flask-Login
from flask_login import UserMixin

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)  # Lunghezza maggiore per l'hash