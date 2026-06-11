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


def get_subject_or_404(subject_id):
    stmt = (
        select(Subject)
        .options(selectinload(Subject.datasets))
        .where(Subject.id == subject_id, Subject.user_id == current_user.id)
    )
    return db.session.execute(stmt).scalar_one_or_none()


# Mostra la lista delle materie del prof
@dash_bp.route('/') 
def dashboard():
    stmt = select(Subject).where(Subject.user_id == current_user.id)
    subjects = db.session.execute(stmt).scalars().all()
    return render_template('dashboard/subject_list.html', subjects=subjects)


# Aggiunge i report / Crea Nuova Materia (Rotta Unificata)
@dash_bp.route('/upload', defaults={'subject_id': None}, methods=['GET', 'POST'])
@dash_bp.route('/upload/<int:subject_id>', methods=['GET', 'POST'])
def upload_reports(subject_id):
    subject = None
    
    # Se viene passato un ID, cerchiamo la materia
    if subject_id:
        subject = get_subject_or_404(subject_id)
        if not subject:
            flash("Materia non trovata.", "danger")
            return redirect(url_for('dashboard.dashboard'))

    if request.method == 'POST':
        files = request.files.getlist('files')

        if not files or files[0].filename == '':
            flash("Nessun file selezionato.", "warning")
            return redirect(url_for('dashboard.upload_reports', subject_id=subject_id))

        
        is_valid, error_msg, reference_ad = validate_files_consistency(files)
        if not is_valid:
            flash(error_msg, 'danger')
            return redirect(url_for('dashboard.upload_reports', subject_id=subject_id))

        
        existing_datasets = subject.datasets if subject else []
        is_continuous, time_error_msg = validate_years_continuity(existing_datasets, files)
        
        if not is_continuous:
            flash(time_error_msg, 'danger')
            return redirect(url_for('dashboard.upload_reports', subject_id=subject_id))

        try:
            # 3A. MODALITÀ: NUOVA MATERIA
            if not subject:
                subject_name = reference_ad or "Materia senza nome"
                subject = Subject(name=subject_name, user_id=current_user.id)
                db.session.add(subject)
                # MIGLIORIA 1: Rimosso il flush! Ci penserà SQLAlchemy a unire gli ID.
                
                msg_success = f'Materia "{subject_name}" creata con successo!'
                redirect_url = url_for('dashboard.dashboard')
            
            # 3B. MODALITÀ: AGGIORNAMENTO
            else:
                msg_success = f'Nuovi report aggiunti con successo a "{subject.name}"!'
                redirect_url = url_for('dashboard.report', subject_id=subject.id)
            
            # 4. ELABORAZIONE CSV
            files_added = 0
            for file in files:
                if file and file.filename != '' and allowed_file(file.filename):
                    data_list = csv_to_json(file)
                    new_dataset = Dataset(
                        filename=secure_filename(file.filename),
                        data_json=data_list
                        # MIGLIORIA 1: Rimosso subject_id=subject.id
                    )
                    # La "Magia" ORM: li aggiungiamo direttamente alla lista della materia
                    subject.datasets.append(new_dataset) 
                    files_added += 1

            if files_added > 0:
                db.session.commit() # Salva contemporaneamente la materia e collega tutti i dataset!
                flash(msg_success, 'success')
                return redirect(redirect_url)
            else:
                flash("Nessun file CSV valido elaborato.", "warning")
                return redirect(url_for('dashboard.upload_reports', subject_id=subject_id))

        except Exception as e:
            db.session.rollback()
            flash(f"Errore durante l'operazione: {str(e)}", "danger")
            return redirect(url_for('dashboard.upload_reports', subject_id=subject_id))

    return render_template('dashboard/upload_reports.html', subject=subject)


# Elimina la materia
@dash_bp.route('/delete_subject/<int:subject_id>', methods=['POST'])
def delete_subject(subject_id):
    subject = get_subject_or_404(subject_id)

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



# Report Grafici
@dash_bp.route('/report/<int:subject_id>')
def report(subject_id):
    subject = get_subject_or_404(subject_id)
    if not subject:
        flash("Materia non trovata.", "danger")
        return redirect(url_for('dashboard.dashboard'))
    
    return render_template('dashboard/report.html', subject=subject)


# Report con le tabelle
@dash_bp.route('/report/<int:subject_id>/tables')
def report_tables(subject_id):
    subject = get_subject_or_404(subject_id)

    if not subject:
        flash("Materia non trovata.", "danger")
        return redirect(url_for('dashboard.dashboard'))

    datasets_ordinati = sort_datasets(subject.datasets)
    return render_template('dashboard/report_tables.html', subject=subject, datasets=datasets_ordinati)


# API per il report singolo (grafici)
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



# 1. Pagina per il confronto
@dash_bp.route('/compare')
def compare_subjects():
    stmt = select(Subject).where(Subject.user_id == current_user.id)
    subjects = db.session.execute(stmt).scalars().all()
    
    if len(subjects) < 2:
        flash("Devi avere almeno due materie per poter fare un confronto.", "warning")
        return redirect(url_for('dashboard.dashboard'))
        
    return render_template('dashboard/compare.html', subjects=subjects)


# 2. API per il confronto
@dash_bp.route('/api/compare/<int:subject1_id>/<int:subject2_id>')
def get_compare_data(subject1_id, subject2_id):
    sub1 = get_subject_or_404(subject1_id)
    sub2 = get_subject_or_404(subject2_id)
    
    if not sub1 or not sub2:
        return jsonify({'error': 'Una o entrambe le materie non trovate'}), 404
        
    try:
        data_sub1 = prepare_datasets_for_js(sub1.datasets) if sub1.datasets else []
        data_sub2 = prepare_datasets_for_js(sub2.datasets) if sub2.datasets else []
        
        response_data = {
            'subject1': {
                'id': sub1.id,
                'name': sub1.name,
                'datasets': data_sub1
            },
            'subject2': {
                'id': sub2.id,
                'name': sub2.name,
                'datasets': data_sub2
            }
        }
        return jsonify(response_data)
        
    except Exception:
        return jsonify({'error': 'Errore durante elaborazione dati per il confronto'}), 500