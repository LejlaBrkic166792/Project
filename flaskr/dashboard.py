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
def require_login():
    pass

#mostra la lista delle materie dell'prof
@dash_bp.route('/') 
def dashboard():
    stmt = select(Subject).where(Subject.user_id == current_user.id)
    subjects = db.session.execute(stmt).scalars().all()
    return render_template('dashboard/subject_list.html', subjects=subjects)

#aggiunge una nuova materia
@dash_bp.route('/new_subject', methods=['GET', 'POST'])
def new_subject():
    if request.method == 'POST':
        subject_name = request.form.get('subject_name')
        files = request.files.getlist('files')

        if files and files[0].filename != '':
            try:
                reference_ad = extract_metadata(files[0], 'Attività Didattica (AD)')
               
                if not subject_name:
                    subject_name = reference_ad if reference_ad else "Materia senza nome"
                
                new_subject_obj = Subject(name=subject_name, user_id=current_user.id)
                db.session.add(new_subject_obj)
                db.session.flush()

                for file in files:
                    if file and file.filename != '' and allowed_file(file.filename):
                        
                        #BLOCCO DI SICUREZZA: Controllo Coerenza Materia
                        current_file_ad = extract_metadata(file, 'Attività Didattica (AD)')
                        
                        if reference_ad and current_file_ad and current_file_ad != reference_ad:
                            db.session.rollback()
                            flash(f'Errore: il file "{file.filename}" appartiene a "{current_file_ad}", non "{reference_ad}"')
                            return redirect(url_for('dashboard.new_subject'))
                        # -------------------------------------------------------

                        data_list = csv_to_json(file)
                        new_dataset = Dataset(
                            filename=secure_filename(file.filename),
                            data_json=data_list,
                            subject_id=new_subject_obj.id
                        )
                        db.session.add(new_dataset)
                
                
                db.session.commit()
                flash(f'Materia "{subject_name}" creato con successo!')
                return redirect(url_for('dashboard.dashboard'))
            
            except Exception as e:
                db.session.rollback()
                flash('Errore nel creare la materia')
        else:
            flash('File mancanti o erratti')

    return render_template('dashboard/new_subject.html')

#elimina la materia
@dash_bp.route('/delete_subject/<int:subject_id>', methods=['POST'])
def delete_subject(subject_id):
    stmt = select(Subject).where(Subject.id == subject_id, Subject.user_id == current_user.id)
    subject = db.session.execute(stmt).scalar_one_or_none()

    if not subject:
        flash("Operazione non consentita.", "danger")
        return redirect(url_for('dashboard.dashboard'))
    try:
        db.session.delete(subject)
        db.session.commit()
        flash(f'Materia "{subject.name}" eliminata con successo.')
    except Exception:
        db.session.rollback()
        flash("Errore durante l'eliminazione della materia.")
    
    return redirect(url_for('dashboard.dashboard'))

#cerca le materia
def get_subject_or_404(subject_id):
    stmt = (
        select(Subject)
        .options(selectinload(Subject.datasets))
        .where(Subject.id == subject_id, Subject.user_id == current_user.id)
    )
    return db.session.execute(stmt).scalar_one_or_none()

#report
@dash_bp.route('/report/<int:subject_id>')
def report(subject_id):
    subject = get_subject_or_404(subject_id)
    if not subject:
        flash("Materia non trovata.", "danger")
        return redirect(url_for('dashboard.dashboard'))
    
    return render_template('dashboard/report.html', subject=subject)

#report con solo le tabelle
@dash_bp.route('/report/<int:subject_id>/tables')
def report_tables(subject_id):
    subject = get_subject_or_404(subject_id)

    if not subject:
        flash("Materia non trovata.", "danger")
        return redirect(url_for('dashboard.dashboard'))

    datasets_ordinati = sort_datasets(subject.datasets)

    return render_template('dashboard/report_tables.html', 
                           subject=subject, 
                           datasets=datasets_ordinati)


#API
@dash_bp.route('/api/data/<int:subject_id>')
def get_report_data(subject_id):
    subject = get_subject_or_404(subject_id)
    if not subject:
        return jsonify({'error': 'Non trovato'}), 404
    
    if not subject.datasets:
        return jsonify([])

    try:
        datasets_js = prepare_datasets_for_js(subject.datasets)
        return jsonify(datasets_js)
    except Exception:
        return jsonify({'error': 'Fallito il processo dei report'}), 500
