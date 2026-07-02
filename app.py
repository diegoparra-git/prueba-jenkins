## @package app
#  Aplicación Flask de Gestor de Tareas vulnerable para evaluación DevSecOps.
#  Incluye métricas de Prometheus y logs hacia Elasticsearch.
from flask import Flask, request, render_template_string, session, redirect, url_for, flash
from prometheus_client import make_wsgi_app, Counter
from werkzeug.middleware.dispatcher import DispatcherMiddleware
import sqlite3
import os
import hashlib
import requests
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)

# ==========================================
# 1. CONFIGURACIÓN DEVSECOPS: PROMETHEUS
# ==========================================
REQUEST_COUNTER = Counter('flask_app_requests_total', 'Total de peticiones HTTP a la aplicación')
app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
    '/metrics': make_wsgi_app()
})

# ==========================================
# 2. CONFIGURACIÓN DEVSECOPS: ELASTICSEARCH
# ==========================================
ELASTICSEARCH_URL = 'http://host.docker.internal:9200/flask-logs/_doc' # NOSONAR

def log_to_elastic(level, message, endpoint):
    log_data = {
        "@timestamp": datetime.utcnow().isoformat(),
        "level": level,
        "message": message,
        "endpoint": endpoint,
        "app": "task_manager_app"
    }
    try:
        requests.post(ELASTICSEARCH_URL, json=log_data, timeout=2)
    except Exception:
        pass # Ignoramos el error para no afectar la experiencia del usuario

# ==========================================
# LÓGICA DE LA APLICACIÓN
# ==========================================
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

## @brief Función principal de renderizado de la página de inicio.
#  @return Mensaje de bienvenida.
@app.route('/')
def index():
    REQUEST_COUNTER.inc()
    return 'Welcome to the Task Manager Application!'

## @brief Ruta de autenticación de usuarios (VULNERABLE A SQL INJECTION).
#  @details Valida las credenciales contra la base de datos SQLite. Contiene un vector de inyección ' OR '.
#  @return Redirección al dashboard si es exitoso, o mensaje de error.
@app.route('/login', methods=['GET', 'POST'])
def login():
    REQUEST_COUNTER.inc()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()

        # Inyección de SQL intencional
        if "' OR '" in password:
            log_to_elastic("WARNING", f"Intento de inyección SQL detectado en el usuario: {username}", "/login")
            query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
            user = conn.execute(query).fetchone()
        else:
            query = "SELECT * FROM users WHERE username = ? AND password = ?"
            hashed_password = hash_password(password)
            user = conn.execute(query, (username, hashed_password)).fetchone()

        if user:
            session['user_id'] = user['id']
            session['role'] = user['role']
            log_to_elastic("INFO", f"Login exitoso para usuario ID: {user['id']}", "/login")
            return redirect(url_for('dashboard'))
        else:
            log_to_elastic("WARN", f"Login fallido para username: {username}", "/login")
            return 'Invalid credentials!'
            
    return '''
        <form method="post">
            Username: <input type="text" name="username"><br>
            Password: <input type="password" name="password"><br>
            <input type="submit" value="Login">
        </form>
    '''

## @brief Panel de control del usuario.
#  @details Muestra las tareas correspondientes al user_id actual de la sesión.
#  @return Plantilla HTML con las tareas.
@app.route('/dashboard')
def dashboard():
    REQUEST_COUNTER.inc()
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db_connection()
    tasks = conn.execute("SELECT * FROM tasks WHERE user_id = ?", (user_id,)).fetchall()
    conn.close()

    return render_template_string('''
        <h1>Welcome, user {{ user_id }}!</h1>
        <form action="/add_task" method="post">
            <input type="text" name="task" placeholder="New task"><br>
            <input type="submit" value="Add Task">
        </form>
        <h2>Your Tasks</h2>
        <ul>
        {% for task in tasks %}
            <li>{{ task['task'] }} <a href="/delete_task/{{ task['id'] }}">Delete</a></li>
        {% endfor %}
        </ul>
        <br><br><a href="/admin">Go to Admin Panel</a>
    ''', user_id=user_id, tasks=tasks)

## @brief Añade una nueva tarea a la base de datos.
#  @param task El texto de la tarea recibido por POST.
@app.route('/add_task', methods=['POST'])
def add_task():
    REQUEST_COUNTER.inc()
    if 'user_id' not in session:
        return redirect(url_for('login'))

    task = request.form['task']
    user_id = session['user_id']

    conn = get_db_connection()
    conn.execute("INSERT INTO tasks (user_id, task) VALUES (?, ?)", (user_id, task))
    conn.commit()
    conn.close()
    
    log_to_elastic("INFO", f"Usuario ID {user_id} añadió una nueva tarea.", "/add_task")
    return redirect(url_for('dashboard'))

## @brief Elimina una tarea de la base de datos (VULNERABLE A IDOR).
#  @param task_id ID de la tarea a eliminar.
#  @warning Esta función no valida si el task_id pertenece al usuario de la sesión actual.
@app.route('/delete_task/<int:task_id>')
def delete_task(task_id):
    REQUEST_COUNTER.inc()
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

    log_to_elastic("INFO", f"Usuario ID {session['user_id']} eliminó la tarea ID {task_id}.", "/delete_task")
    return redirect(url_for('dashboard'))

## @brief Panel de administración del sistema.
#  @details Valida que el usuario actual tenga una sesión activa y posea el rol de 'admin'.
#           Si se detecta un intento de acceso no autorizado (falta de sesión o permisos insuficientes), 
#           registra una alerta de seguridad (WARN) en Elasticsearch y deniega el acceso.
#  @return Un mensaje de bienvenida al panel si la validación es exitosa, o una redirección a la ruta de inicio de sesión.
@app.route('/admin')
def admin():
    REQUEST_COUNTER.inc()
    if 'user_id' not in session or session.get('role') != 'admin':
        log_to_elastic("CRITICAL!", f"Intento de acceso no autorizado al panel admin por usuario ID: {session.get('user_id')}", "/admin")
        return redirect(url_for('login'))

    return 'Welcome to the admin panel!'

if __name__ == '__main__':
    # Modificado para funcionar dentro del contenedor Docker
    app.run(host='0.0.0.0', port=5000, debug=True) # NOSONAR