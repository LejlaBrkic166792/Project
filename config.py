import os
from dotenv import load_dotenv

load_dotenv()


#Se l'app crasha, l'utente vedrà un errore generico e non il tuo codice sorgente.
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-default')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class ProductionConfig(Config):
    DEBUG = False
    # In produzione userai un URL di un database vero (Postgres/MySQL)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

class DevelopmentConfig(Config):
    DEBUG = True
    # Puntiamo al database nella tua cartella instance
    SQLALCHEMY_DATABASE_URI = 'sqlite:///instance/dbms.db'

'''
In sviluppo usi SQLite (comodo e veloce), ma quando sarai sul server di produzione potrai 
collegare un database professionale (come PostgreSQL o MySQL) semplicemente cambiando 
una riga nel file .env del server, senza toccare una singola riga di codice Python.

in produzione si posso gestire piu richieste contemporaneamente
'''