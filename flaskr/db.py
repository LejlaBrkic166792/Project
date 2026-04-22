from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt

#Definire db = SQLAlchemy() e login_manager = LoginManager() all'esterno permette di importare questi oggetti senza causare errori di inizializzazione
db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()

@login_manager.user_loader
#cookie memorizzano i dati come stringhe, int(user_id) assicura che SQLAlchemy cerchi l'ID nel formato corretto (numero intero).
def load_user(user_id):
    #Impedisce che db.py e models.py si importino a vicenda all'infinito
    from .models import User
    return User.query.get(int(user_id))