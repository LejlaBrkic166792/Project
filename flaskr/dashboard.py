import csv
import io
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

# Importiamo il database e i modelli
from .db import db
from .models import Subject, Dataset 

dash_bp = Blueprint('dashboard', __name__)

ALLOWED_EXTENSIONS = {'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@dash_bp.route('/') 
@login_required
def dashboard():
    user_subjects = Subject.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard/lista_materie.html', subjects=user_subjects)

@dash_bp.route('/nuova_materia', methods=['GET', 'POST'])
@login_required
def nuova_materia():
    if request.method == 'POST':
        subject_name = request.form.get('subject_name')
        file = request.files.get('file')

        if subject_name and file and allowed_file(file.filename):
            try:
                # 1. Crea la Materia
                new_subject = Subject(name=subject_name, user_id=current_user.id)
                db.session.add(new_subject)
                #aggiunge i dati senza chiudere la transizione 
                db.session.flush() 

                # 2. Leggi CSV
                stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
                reader = csv.DictReader(stream)
                data_list = [row for row in reader]

                # 3. Salva Dataset collegato alla materia
                new_dataset = Dataset(
                    filename=secure_filename(file.filename),
                    data_json=data_list,
                    subject_id=new_subject.id
                )
                db.session.add(new_dataset)
                db.session.commit()
                
                flash(f'Materia "{subject_name}" creata con successo!')
                return redirect(url_for('dashboard.dashboard'))
            except Exception as e:
                db.session.rollback()
                flash(f'Errore: {e}')
        else:
            flash('Dati mancanti o file non valido.')

    return render_template('dashboard/nuova_materia.html')

@dash_bp.route('/report/<int:subject_id>')
@login_required
def report(subject_id):
    subject = Subject.query.filter_by(id=subject_id, user_id=current_user.id).first_or_404()
    return render_template('dashboard/report.html', subject=subject)


@dash_bp.route('/elimina_materia/<int:subject_id>', methods=['POST'])
@login_required
def elimina_materia(subject_id):
    # Cerchiamo la materia assicurandoci che appartenga all'utente loggato
    subject = Subject.query.filter_by(id=subject_id, user_id=current_user.id).first_or_404()
    
    try:
        # la materia si elimina a cascata al momento dell'eliminazione della materia
    
        db.session.delete(subject)
        db.session.commit()
        flash(f'Materia "{subject.name}" eliminata con successo.')
    except Exception as e:
        db.session.rollback()
        flash(f'Errore durante l\'eliminazione: {e}')
    
    return redirect(url_for('dashboard.dashboard'))