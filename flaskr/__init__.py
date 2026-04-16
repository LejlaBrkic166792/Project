'''
unico compito è la configurazione (Application Factory):
impostare il database, registrare i Blueprint e caricare le chiavi segrete.
'''
import os
from dotenv import load_dotenv
from flask import Flask
from .db import db, login_manager, bcrypt



# Trova la cartella 'flaskr'
basedir = os.path.abspath(os.path.dirname(__file__))
# Carica il file .env che sta nella cartella superiore rispetto a 'flaskr'
load_dotenv(os.path.join(basedir, '..', '.env'))

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    
    #Configurazione (evita di mettere la chiave segrta)
    app.config.update(
        SECRET_KEY=os.getenv('SECRET_KEY'),
        #SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL'), #vedi poi di cambiare da sqlite a mysql o postgres
        SQLALCHEMY_DATABASE_URI = 'sqlite:////home/lejla/Project/database.db'
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )

    #unisce l'istandza db all'app (a ogni richiesta sa come gestire la conessione al db)
    db.init_app(app)

    #dice a flask come r/w i cookie di sessione (controlla se ce un id utente nel cooki e se ce lo carica dal db)
    login_manager.init_app(app)
    bcrypt.init_app(app)

    # Se un utente prova ad accedere a una pagina protetta senza login, va automaticamente reindirizzato alla pagina di accesso.
    login_manager.login_view = 'auth.login' 

    #Le viste e il codice non vengono registrati direttamente nell'applicazione, ma vengono prima registrati nel Blueprint.
    from .auth import auth_bp
    app.register_blueprint(auth_bp)#Il Blueprint viene "consegnato" all'applicazione solo quando questa è disponibile nella funzione factory. Puoi definire un url_prefix che verrà aggiunto a tutti gli indirizzi di quel Blueprint es. /login -> /auth/login

    from .main import main_bp
    app.register_blueprint(main_bp)

    # Questo blocco assicura che le tabelle vengano create se non esistono
    from .models import User # Importante importare i modelli qui!
    with app.app_context():
        db.create_all()

    return app