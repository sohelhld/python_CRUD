from flask import Flask,jsonify, request, current_app as app, render_template
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import logging

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:nopass@localhost:5432/flask_database'
db = SQLAlchemy(app)
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    title = db.Column(db.String(200),nullable=False)
    done = db.Column(db.Boolean, default=False)

with app.app_context():
    db.create_all()
logging.basicConfig(level=logging.INFO)
@app.route("/tasks")
def get_tasks():
    tasks = Task.query.all()
    task_list = [
        {'id':task.id, 'title':task.title, 'done':task.done} for task in tasks
    ]
    return ({"tasks":task_list})

@app.route("/tasks",methods=["POST"])
def creat_tasks():
    data = request.get_json()
    new_task = Task(title=data['title'],done= data['done'])
    db.session.add(new_task)
    db.session.commit()
    return jsonify({'message':'task created successfully'}),201

@app.route("/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    data = request.get_json()
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'message': 'task not found'}), 404
    task.title = data.get('title', task.title)
    task.done = data.get('done', task.done)
    db.session.commit()
    return jsonify({'message': 'task updated successfully'})

@app.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'message': 'task not found'}), 404
    db.session.delete(task)
    db.session.commit()
    return jsonify({'message': 'task deleted successfully'})


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'message': 'No file part in the request'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400
    if file and (file.filename.endswith('.xlsx') or file.filename.endswith('.xls')):
        try:
            try:
                df = pd.read_excel(file)
            except UnicodeDecodeError:
                df = pd.read_excel(file, encoding='latin1')
            except pd.errors.EmptyDataError:
                return jsonify({'message': 'The file is empty'}), 400
            except pd.errors.ParserError:
                return jsonify({'message': 'Error parsing the file'}), 400
            if df.empty:
                return jsonify({'message': 'No data found in the file'}), 400
            if 'title' not in df.columns or 'done' not in df.columns:
                return jsonify({'message': 'Missing required columns'}), 400
            for index, row in df.iterrows():
                new_task = Task(title=row['title'], done=row['done'])
                db.session.add(new_task)
            db.session.commit()
            return jsonify({'message': 'Excel file processed successfully'}), 201
        except Exception as e:
            logging.error(f"Error processing file: {e}")
            return jsonify({'message': 'Error processing file', 'error': str(e)}), 500
    else:
        return jsonify({'message': 'Invalid file type. Please upload an Excel file.'}), 400


if __name__ == "__main__":
    app.run(debug=True)