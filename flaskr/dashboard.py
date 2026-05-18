from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from .db import db
from .models import Subject, Dataset 
from .stat_report import *

dash_bp = Blueprint('dashboard', __name__)

ALLOWED_EXTENSIONS = {'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@dash_bp.before_request
@login_required
def controllo_accessi():
    pass

#mostra la lista delle materie dell'prof
@dash_bp.route('/') 
def dashboard():
    lista = select(Subject).where(Subject.user_id == current_user.id)
    materie = db.session.execute(lista).scalars().all()
    return render_template('dashboard/lista_materie.html', subjects=materie)

#aggiunge una nuova materia
@dash_bp.route('/nuova_materia', methods=['GET', 'POST'])
def nuova_materia():
    if request.method == 'POST':
        nome_materia = request.form.get('subject_name')
        files = request.files.getlist('files')

        if files and files[0].filename != '':
            try:
                if not nome_materia:
                    nome_materia = estrai_valore(files[0], 'Attività Didattica (AD)')
                   
                    if not nome_materia:
                        nome_materia = "Materia senza nome (estrazione fallita)"
                
                nuova_materia_obj = Subject(name=nome_materia, user_id=current_user.id)
                db.session.add(nuova_materia_obj)
                db.session.flush()
                

                for file in files:
                    if file and file.filename != '' and allowed_file(file.filename):
                        
                        data_list = stat_csv(file)

                        new_dataset = Dataset(
                            filename=secure_filename(file.filename),
                            data_json=data_list,
                            subject_id=nuova_materia_obj.id
                        )
                        db.session.add(new_dataset)
                db.session.commit()
                
                flash(f'Materia "{nome_materia}" creata con successo!', 'success')
                return redirect(url_for('dashboard.dashboard'))
            except Exception as e:
                db.session.rollback()
                flash(f'Errore: {e}')
        else:
            flash('Dati mancanti o file non valido.')

    return render_template('dashboard/nuova_materia.html')

#elimina la materia
@dash_bp.route('/elimina_materia/<int:subject_id>', methods=['POST'])
def elimina_materia(subject_id):
    istruzione = select(Subject).where(Subject.id == subject_id, Subject.user_id == current_user.id)
    materia = db.session.execute(istruzione).scalar_one_or_none()

    if not materia:
        flash("Operazione non consentita.", "danger")
        return redirect(url_for('dashboard.dashboard'))
    
    try:
       
        db.session.delete(materia)
        db.session.commit()
        flash(f'Materia "{materia.name}" eliminata con successo.')
    except Exception as e:
        db.session.rollback()
        flash(f'Errore durante l\'eliminazione: {e}')
    
    return redirect(url_for('dashboard.dashboard'))

#cerca le materia
def get_subject_or_404(subject_id):
    istruzione = (
        select(Subject)
        .options(selectinload(Subject.datasets))
        .where(Subject.id == subject_id, Subject.user_id == current_user.id)
    )
    materia = db.session.execute(istruzione).scalar_one_or_none()
    return materia

#report
@dash_bp.route('/report/<int:subject_id>')
def report(subject_id):
    materia = get_subject_or_404(subject_id)
    if not materia:
        flash("Materia non trovata.", "danger")
        return redirect(url_for('dashboard.dashboard'))
    
    return render_template('dashboard/report.html', subject=materia)

#API
@dash_bp.route('/api/data/<int:subject_id>')
def get_report_data(subject_id):
    materia = get_subject_or_404(subject_id)
    if not materia:
        return jsonify({'error': 'Non trovato'}), 404
    
    datasets_js = prepara_dataset_per_js(materia.datasets)
    return jsonify(datasets_js)

#report con solo le tabelle
@dash_bp.route('/report/<int:subject_id>/tabelle')
def report_tabelle(subject_id):
    materia = get_subject_or_404(subject_id)

    if not materia:
        flash("Materia non trovata.", "danger")
        return redirect(url_for('dashboard.dashboard'))

    datasets_ordinati = ordina_datasets(materia.datasets)

    return render_template('dashboard/report_tabelle.html', 
                           subject=materia, 
                           datasets=datasets_ordinati)