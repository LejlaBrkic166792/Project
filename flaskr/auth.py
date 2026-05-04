from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required
from .models import User
from sqlalchemy import select
#da vedere se usare werkzeug o bcrypt
from .db import db, bcrypt
# Importiamo le classi dei form (che definirai in un file forms.py o in cima a questo file)
from .form import RegisterForm, LoginForm 

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

'''

da decidere se sono utili
@auth_bp.before_request
def gestione_pre_richiesta():
  
@auth_bp.after_request
def gestione_post_richiesta(response):
  
'''



@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    
    # validate_on_submit() controlla che la richiesta sia POST e che i dati siano validi
    if form.validate_on_submit():
        # Cripto la password
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        new_user = User(username=form.username.data, password=hashed_pw)

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Account creato! Benvenuto.', 'success')
            return redirect(url_for('.login'))
        except Exception:
            db.session.rollback()
            flash('Errore: questo username è già occupato.', 'danger')

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