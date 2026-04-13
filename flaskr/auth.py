'''
l'oggetto Blueprint: quei contenitore per tutte le tue rotte di autenticazione.
'''

from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from .models import User
from .db import db

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        #1. Recupero i dati dal form HTML
        username = request.form.get('username')
        password = request.form.get('password')
        
        # 2. Controllo se l'utente esiste già
        user_exists = User.query.filter_by(username=username).first()
        if user_exists:
            flash('Questo username è già occupato.')
            return redirect(url_for('auth.register'))

        # 3. Cripto la password e salvo il nuovo docente
        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, password=hashed_pw)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registrazione completata! Ora puoi accedere.')
        return redirect(url_for('auth.login'))

    # Se la richiesta è GET, mostro semplicemente il template
    return render_template('register.html')


#Login
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Cerco l'utente nel database
        user = User.query.filter_by(username=username).first()

        # Verifico se l'utente esiste e se la password (hashata) coincide
        if user and check_password_hash(user.password, password):
            # Flask-Login crea la sessione sicura nel browser
            login_user(user)
            
            # Reindirizzo alla dashboard (o alla pagina richiesta prima del login)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.dashboard'))
        
        flash('Username o password errati.')
    
    return render_template('login.html')