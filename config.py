import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Fondamentale per firmare cookie e prevenire CSRF
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'cambiami-in-produzione-con-una-stringa-lunga'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # (vedere se mantenere)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    SESSION_COOKIE_HTTPONLY = True

    # vedere se mettere la durata della sessione e la protezione contro attacchi CSRF

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    
    # invia i cookie solo in conessioni https
    SESSION_COOKIE_SECURE = True

    # TRUSTED_HOSTS = ['tuodominio.com'] -> da decidere


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI')
    
    SESSION_COOKIE_SECURE = False