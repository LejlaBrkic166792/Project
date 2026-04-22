from flask import Blueprint, render_template
from flask_login import login_required, current_user

# Definiamo il blueprint. 
# Non mettiamo url_prefix così la home sarà direttamente su "/"
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    """Questa funzione carica la pagina principale (Home)"""
    return render_template('main/home.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """
    Questa è la pagina privata. 
    Il decoratore @login_required blocca gli utenti non loggati.
    """
    # Passiamo current_user al template per mostrare il nome del docente
    return render_template('main/dashboard.html', user=current_user)