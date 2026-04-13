'''
unico compito è la configurazione (Application Factory):
impostare il database, registrare i Blueprint e caricare le chiavi segrete.
'''

from flask import Flask
from .db import db, login_manager

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config['SECRET_KEY'] = 'jvnsvAFGBY89_ekw$%wkemQWMZPé+*' # Fondamentale deve essere una chiave complessa per evitare che qualcuno manipoli i cookie di sessione.
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///project.db'

    
    db.init_app(app)
    #è l'oggetto che "istruisce" Flask su come gestire l'autenticazione.
    login_manager.init_app(app)
    
    # Se un utente prova ad accedere a una pagina protetta senza login, va automaticamente reindirizzato alla pagina di accesso.
    login_manager.login_view = 'auth.login' 

    #Le viste e il codice non vengono registrati direttamente nell'applicazione, ma vengono prima registrati nel Blueprint.
    from .auth import auth_bp
    #Il Blueprint viene "consegnato" all'applicazione solo quando questa è disponibile nella funzione factory. Puoi definire un url_prefix che verrà aggiunto a tutti gli indirizzi di quel Blueprint es. /login -> /auth/login
    app.register_blueprint(auth_bp)

    from .main import main_bp
    app.register_blueprint(main_bp)

    return app