'''
unico compito è la configurazione (Application Factory):
impostare il database, registrare i Blueprint e caricare le chiavi segrete.
'''
import os
from dotenv import load_dotenv
from flask import Flask, render_template
from .db import db, login_manager, bcrypt
from flask_talisman import Talisman
from config import DevelopmentConfig # Importa le tue classi
from flask_wtf.csrf import CSRFProtect

#valutare in futuro se e come usare i caching

#protegge richieste anche se non arrivano direttamente dal form
csrf = CSRFProtect()

# Trova la cartella 'flaskr'
basedir = os.path.abspath(os.path.dirname(__file__))
# Carica il file .env che sta nella cartella superiore rispetto a 'flaskr'
load_dotenv(os.path.join(basedir, '..', '.env'))

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(DevelopmentConfig)


    # Configurazione rapida: Talisman attivo solo in produzione
    # Se app.debug è True, Talisman viene configurato per non rompere JS/CSS
    Talisman(app, 
             content_security_policy=None if app.debug else {'default-src': "'self'"},
             force_https=not app.debug)

    #unisce l'istandza db all'app (a ogni richiesta sa come gestire la conessione al db)
    db.init_app(app)
    #dice a flask come r/w i cookie di sessione (controlla se ce un id utente nel cooki e se ce lo carica dal db)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)

    # Se un utente prova ad accedere a una pagina protetta senza login, va automaticamente reindirizzato alla pagina di accesso.
    login_manager.login_view = 'auth.login' 

    #Le viste vengono prima registrati nel Blueprint.
    from .auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')#Il Blueprint viene "consegnato" all'applicazione solo quando questa è disponibile nella funzione factory

 
    from .dashboard import dash_bp
    app.register_blueprint(dash_bp)

    # Creazione tabelle
    with app.app_context(): #
        from . import models  
        db.create_all() #
        
    #GESTIONE ERORI provissorio 
    def page_not_found(e):
            return render_template('errors/404.html'), 404

    def internal_server_error(e):
        return render_template('errors/500.html'), 500

    app.register_error_handler(404, page_not_found)
    app.register_error_handler(500, internal_server_error)

    return app