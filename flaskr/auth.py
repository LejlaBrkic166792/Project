from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from .models import User
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from .db import db, bcrypt
from .form import RegisterForm, LoginForm 

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

#Impedisce agli utenti loggati di accedere a login/register
@auth_bp.before_request
def redirect_if_authenticated():
    excluded_endpoints = ['auth.login', 'auth.register']
    if current_user.is_authenticated and request.endpoint in excluded_endpoints:
        return redirect(url_for('dashboard.dashboard'))

#Aggiunge header di sicurezza per le autenticazione
@auth_bp.after_request
def add_headers(response):
    response.headers["X-Frame-Options"] = "DENY"
    return response

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    
    #controlla che la richiesta sia POST e che i dati siano validi
    if form.validate_on_submit():
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        new_user = User(username=form.username.data, password=hashed_pw)

        try:
            db.session.add(new_user)     
            db.session.commit()          
            flash('Account creato! Benvenuto.')
            return redirect(url_for('.login')) #
            
        except IntegrityError:
            db.session.rollback()       
            flash('Errore: questo username è già occupato.')
            
        except Exception:
            db.session.rollback()
            flash('Si è verificato un errore durante la registrazione.')

    return render_template('auth/register.html', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    
    if form.validate_on_submit():
        stmt = select(User).where(User.username == form.username.data)
        user = db.session.execute(stmt).scalar_one_or_none()

        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard.dashboard'))
        
        flash('Username o password errati.')
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Ti sei disconnesso con successo.')
    return redirect(url_for('.login'))