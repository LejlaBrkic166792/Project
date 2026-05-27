import os
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

class Config:
    # Fondamentale per firmare cookie e prevenire CSRF
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'cambiami-in-produzione-con-una-stringa-lunga'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    # Sicurezza Cookie e Sessioni
    SESSION_COOKIE_HTTPONLY = True
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)# Scade dopo 24 ore

    # Attiva esplicitamente la protezione CSRF globale
    WTF_CSRF_ENABLED = True


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    
    # invia i cookie solo in conessioni https
    SESSION_COOKIE_SECURE = True



class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI')

    SESSION_COOKIE_SECURE = False