from flask import Flask, request, send_from_directory, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Session
from datetime import datetime
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///files.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key_here'  # Ensure this is set

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

db = SQLAlchemy(app)

class FileEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    file_number = db.Column(db.String(100), nullable=False)
    person_name = db.Column(db.String(100), nullable=False)
    file_path = db.Column(db.String(100), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<File {self.name}>'

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    name = request.form['name']
    file_number = request.form['file_number']
    person_name = request.form['person_name']
    if file:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        new_file = FileEntry(name=name, file_number=file_number, person_name=person_name, file_path=file_path)
        db.session.add(new_file)
        db.session.commit()
        flash('File successfully uploaded', 'success')
        return redirect(url_for('index'))
    flash('No file provided', 'error')
    return redirect(url_for('index'))

@app.route('/search')
def search():
    query = request.args.get('query')
    files = FileEntry.query.filter(
        (FileEntry.name.contains(query)) |
        (FileEntry.file_number.contains(query)) |
        (FileEntry.person_name.contains(query))
    ).all()
    return render_template('search_results.html', files=files)

@app.route('/view/<int:file_id>')
def view(file_id):
    with Session(bind=db.engine) as session:
        file_entry = session.get(FileEntry, file_id)
        if file_entry and file_entry.file_path.lower().endswith('.pdf'):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_entry.file_path)
            if os.path.exists(file_path):
                return send_from_directory(app.config['UPLOAD_FOLDER'], file_entry.file_path, as_attachment=False, mimetype='application/pdf')
            else:
                print(f"File does not exist at: {file_path}")
        else:
            print("No valid PDF file entry found in the database for ID:", file_id)
        return 'File not found', 404

@app.route('/download/<int:file_id>')
def download(file_id):
    with Session(bind=db.engine) as session:
        file_entry = session.get(FileEntry, file_id)
        if file_entry:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], os.path.basename(file_entry.file_path))
            if os.path.exists(file_path):
                return send_from_directory(app.config['UPLOAD_FOLDER'], os.path.basename(file_entry.file_path), as_attachment=True)
            else:
                print("File does not exist:", file_path)
        return 'File not found', 404

@app.route('/delete/<int:file_id>', methods=['POST'])
def delete_file(file_id):
    with Session(bind=db.engine) as session:
        file_entry = session.get(FileEntry, file_id)
        if file_entry:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_entry.file_path)
            if os.path.exists(file_path):
                os.remove(file_path)
            session.delete(file_entry)
            session.commit()
            flash('File successfully deleted', 'success')
        else:
            flash('File not found', 'error')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
