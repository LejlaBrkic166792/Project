from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

#Definire db = SQLAlchemy() e login_manager = LoginManager() all'esterno permette di importare questi oggetti senza causare errori di inizializzazione
db = SQLAlchemy()
login_manager = LoginManager()

#bisogna gestire le sessioni e usare il fresh_login per le tratte sensibili (delete) cosi controlli da quanto tempo un user non fa login (in caso usi un remember cooky)

@login_manager.user_loader
#cookie memorizzano i dati come stringhe, int(user_id) assicura che SQLAlchemy cerchi l'ID nel formato corretto (numero intero).
def load_user(user_id):
    #Impedisce che db.py e models.py si importino a vicenda all'infinito
    from .models import User
    return User.query.get(int(user_id))