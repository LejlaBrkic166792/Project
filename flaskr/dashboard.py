import csv
import io
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
#uso di select
from sqlalchemy import select
from sqlalchemy.orm import selectinload

# Importiamo il database e i modelli
from .db import db
from .models import Subject, Dataset 

dash_bp = Blueprint('dashboard', __name__)

ALLOWED_EXTENSIONS = {'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

'''
valutare se ge
'''


@dash_bp.route('/') 
@login_required
def dashboard():
    istruzione = select(Subject).where(Subject.user_id == current_user.id)
    materie = db.session.execute(istruzione).scalars().all()
    return render_template('dashboard/lista_materie.html', subjects=materie)

@dash_bp.route('/nuova_materia', methods=['GET', 'POST'])
@login_required
def nuova_materia():
    if request.method == 'POST':
        nome_materia = request.form.get('subject_name')
        file = request.files.get('file')

        if nome_materia and file and allowed_file(file.filename):
            try:
                # 1. Crea la Materia
                nuova_materia_obj = Subject(name=nome_materia, user_id=current_user.id)
                db.session.add(nuova_materia_obj)
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

@dash_bp.route('/report/<int:subject_id>')
@login_required
def report(subject_id):
    istruzione = (
        select(Subject)
        .options(selectinload(Subject.datasets))
        .where(Subject.id == subject_id, Subject.user_id == current_user.id)
    )
    materia = db.session.execute(istruzione).scalar_one_or_none()
    
    if not materia:
        flash("Materia non trovata o non autorizzato.", "danger")
        return redirect(url_for('dashboard.dashboard'))
    
    return render_template('dashboard/report.html', subject=materia)


@dash_bp.route('/elimina_materia/<int:subject_id>', methods=['POST'])
@login_required
def elimina_materia(subject_id):
    # Cerchiamo la materia assicurandoci che appartenga all'utente loggato
    istruzione = select(Subject).where(Subject.id == subject_id, Subject.user_id == current_user.id)
    materia = db.session.execute(istruzione).scalar_one_or_none()

    if not materia:
        flash("Operazione non consentita.", "danger")
        return redirect(url_for('dashboard.dashboard'))
    
    try:
        # la materia si elimina a cascata al momento dell'eliminazione della materia
    
        db.session.delete(materia)
        db.session.commit()
        flash(f'Materia "{materia.name}" eliminata con successo.')
    except Exception as e:
        db.session.rollback()
        flash(f'Errore durante l\'eliminazione: {e}')
    
    return redirect(url_for('dashboard.dashboard'))