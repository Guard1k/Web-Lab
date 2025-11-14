from flask import Flask, jsonify
import sqlite3

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

def get_db_connection():
    conn = sqlite3.connect('db.sqlite3')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/tasks', methods=['GET'])
def get_tasks():
    conn = get_db_connection()
    tasks = conn.execute('SELECT * FROM tasks').fetchall()
    conn.close()

    task_list = [dict(task) for task in tasks]
    html = "<h2>Список завдань:</h2><ul>"
    for task in task_list:
        html += f"<li>{task['name']}</li>"
    html += "</ul>"
    return html

@app.route('/')
def home():
    return '<h2>Flask-сервер працює: <a href="/tasks">/tasks</a>.</h2>'

if __name__ == '__main__':
    app.run(debug=True)
