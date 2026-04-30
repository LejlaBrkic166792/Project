from .db import db
#con usermixin ottiene automaticamente i quattro metodi richiesti dalla documentazione di Flask-Login
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)  # Lunghezza maggiore per l'hash

    subjects = db.relationship('Subject', backref='owner', lazy=True)


class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False) 
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    datasets = db.relationship('Dataset', backref='subject', lazy=True, cascade="all, delete-orphan")

class Dataset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    data_json = db.Column(db.JSON, nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)