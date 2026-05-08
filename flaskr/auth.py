from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from .models import User
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
#da vedere se usare werkzeug o bcrypt
from .db import db, bcrypt
# Importiamo le classi dei form (che definirai in un file forms.py o in cima a questo file)
from .form import RegisterForm, LoginForm 

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

#Impedisce agli utenti loggati di accedere a login/register
@auth_bp.before_request
def gestione_pre_richiesta():
    excluded_endpoints = ['auth.login', 'auth.register']
    if current_user.is_authenticated and request.endpoint in excluded_endpoints:
        return redirect(url_for('dashboard.dashboard'))

#Aggiunge header di sicurezza per le autenticazione
@auth_bp.after_request
def gestione_post_richiesta(response):
    response.headers["X-Frame-Options"] = "DENY"
    return response

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    
    # validate_on_submit() controlla che la richiesta sia POST e che i dati siano validi
    if form.validate_on_submit():
        # Cripto la password
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        new_user = User(username=form.username.data, password=hashed_pw)

        try:
            db.session.add(new_user)     # Aggiunge l'utente alla transazione corrente
            db.session.commit()          # Salva definitivamente nel database
            flash('Account creato! Benvenuto.', 'success')
            return redirect(url_for('.login')) # Reindirizza alla pagina di login (il '.' punta allo stesso Blueprint)
            
        except IntegrityError:
            # Viene attivato se il database rifiuta l'inserimento (es. username duplicato)
            db.session.rollback()        # Annulla la transazione fallita
            flash('Errore: questo username è già occupato.', 'danger')
            
        except Exception:
            # Cattura altri errori imprevisti (es. database offline)
            db.session.rollback()
            flash('Si è verificato un errore durante la registrazione.', 'danger')

    return render_template('auth/register.html', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    
    if form.validate_on_submit():
        stmt = select(User).where(User.username == form.username.data)
        user = db.session.execute(stmt).scalar_one_or_none()

        # Usa bcrypt per controllare la password
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard.dashboard'))
        
        flash('Username o password errati.', 'danger')
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Ti sei disconnesso con successo.', 'info')
    return redirect(url_for('.login'))