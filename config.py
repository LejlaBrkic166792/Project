
'''
questo e la configurazione che serve in produzione nella factory sostituiremo le app.config con questo file
'''

import os
from dotenv import load_dotenv

# Carichiamo il file .env se esiste
load_dotenv()

class Config:
    # Legge la chiave dal .env, se manca usa il default 'dev-key'
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-molto-semplice')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class ProductionConfig(Config):
    DEBUG = False
    # In produzione puntiamo al DB reale (magari un Postgres o MySQL)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

class DevelopmentConfig(Config):
    DEBUG = True
    # In sviluppo puntiamo al file SQLite nella cartella instance
    SQLALCHEMY_DATABASE_URI = 'sqlite:///instance/app.db'