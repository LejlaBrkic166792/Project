from flask import Flask, render_template, redirect, request, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)

# Assicuriamoci che la cartella 'instance' esista per il database
if not os.path.exists('instance'):
    os.makedirs('instance')

app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///dbms.db'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Data class - le righe del db
class MyTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(100), nullable=False)
    complete = db.Column(db.Integer, default=0)
    created = db.Column(db.DateTime, default=datetime.now) # Usiamo now() invece di utcnow()

    def __repr__(self) -> str:
        return f"Task {self.id}"

# Crea il database se non esiste
with app.app_context():
    db.create_all()

@app.route("/", methods=["POST", "GET"])
def index():
    if request.method == "POST":
        current_task = request.form['content']
        # Evitiamo di aggiungere task vuoti
        if not current_task:
            return redirect("/")
            
        new_task = MyTask(content=current_task)
        try:
            db.session.add(new_task)
            db.session.commit()
            return redirect("/")
        except Exception as e:
            return f"ERRORE: {e}"
    else:
        # Recupera i task ordinati per data di creazione
        tasks = MyTask.query.order_by(MyTask.created).all()
        return render_template("index.html", tasks=tasks)

@app.route("/delete/<int:id>")
def delete(id:int):
    task_to_delete = db.get_or_404(MyTask, id) # Metodo più moderno per SQLAlchemy 3.0+
    try:
        db.session.delete(task_to_delete)
        db.session.commit()
        return redirect("/")
    except Exception as e:
        return f"ERRORE: {e}"

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id:int):
    task = db.get_or_404(MyTask, id)
    if request.method == "POST":
        task.content = request.form['content']
        try:
            db.session.commit()
            return redirect("/")
        except Exception as e:
            return f"ERRORE: {e}" 
    else:
        return render_template("edit.html", task=task)

if __name__ == "__main__":
    app.run(debug=True)