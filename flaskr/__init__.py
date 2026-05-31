
import os
from dotenv import load_dotenv
from flask import Flask, render_template
from .db import db, login_manager, bcrypt
from flask_talisman import Talisman
from config import DevelopmentConfig 
from flask_wtf.csrf import CSRFProtect


#protegge richieste anche se non arrivano direttamente dal form
csrf = CSRFProtect()

# Trova la cartella 'flaskr'
basedir = os.path.abspath(os.path.dirname(__file__))
# Carica il file .env che sta nella cartella superiore rispetto a 'flaskr'
load_dotenv(os.path.join(basedir, '..', '.env'))

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(DevelopmentConfig)


    # Talisman da usare solo in produzione
    #Talisman(app, 
    #         content_security_policy=None if app.debug else {'default-src': "'self'"},
    #         force_https=not app.debug)


    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = 'auth.login' 

    from .auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from .dashboard import dash_bp
    app.register_blueprint(dash_bp)

    with app.app_context():
        from . import models  
        db.create_all()


    @app.errorhandler(404)
    def page_not_found(e):
        print(f"Errore intercettato: {e}")
        return render_template('errors/404.html'), 404
    

    return app