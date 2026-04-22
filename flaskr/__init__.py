'''
unico compito è la configurazione (Application Factory):
impostare il database, registrare i Blueprint e caricare le chiavi segrete.
'''
import os
from dotenv import load_dotenv
from flask import Flask, render_template
from .db import db, login_manager, bcrypt
from config import DevelopmentConfig, ProductionConfig # Importa le tue classi


# Trova la cartella 'flaskr'
basedir = os.path.abspath(os.path.dirname(__file__))
# Carica il file .env che sta nella cartella superiore rispetto a 'flaskr'
load_dotenv(os.path.join(basedir, '..', '.env'))

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    
    #Configurazione (evita di mettere la chiave segrta)
    if os.environ.get('ENV') == 'production':
        app.config.from_object(ProductionConfig)
    else:
        app.config.from_object(DevelopmentConfig)

    #unisce l'istandza db all'app (a ogni richiesta sa come gestire la conessione al db)
    db.init_app(app)

    #dice a flask come r/w i cookie di sessione (controlla se ce un id utente nel cooki e se ce lo carica dal db)
    login_manager.init_app(app)
    bcrypt.init_app(app)

    # Se un utente prova ad accedere a una pagina protetta senza login, va automaticamente reindirizzato alla pagina di accesso.
    login_manager.login_view = 'auth.login' 

    #Le viste e il codice non vengono registrati direttamente nell'applicazione, ma vengono prima registrati nel Blueprint.
    from .auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')#Il Blueprint viene "consegnato" all'applicazione solo quando questa è disponibile nella funzione factory. Puoi definire un url_prefix che verrà aggiunto a tutti gli indirizzi di quel Blueprint es. /login -> /auth/login

    #*********vedi sce gestire nel template main/dashboard, per rendere le cose piu visibili 
    from .main import main_bp
    app.register_blueprint(main_bp)

    # Questo blocco assicura che le tabelle vengano create se non esistono
    from .models import User # Importante importare i modelli qui!
    with app.app_context():
        db.create_all()
        
    #GESTIONE ERORI provissorio 
    def page_not_found(e):
            return render_template('errors/404.html'), 404

    def internal_server_error(e):
        return render_template('errors/500.html'), 500

    app.register_error_handler(404, page_not_found)
    app.register_error_handler(500, internal_server_error)

    return app