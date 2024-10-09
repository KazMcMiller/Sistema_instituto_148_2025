from flask import Flask, render_template, request, redirect, url_for, session
from flask_session import Session
from dotenv import load_dotenv
from controllers.auth_controller import AuthController  # Importa directamente desde el módulo controllers
from models import Usuario  # Importa directamente desde el módulo models

load_dotenv()

app = Flask(__name__)

# Configuración de la sesión
app.config['SECRET_KEY'] = 'tu_clave_secreta'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

@app.route('/')
def home():
    if 'nombre' in session:
        return f"¡Hola, {session['nombre']}! <br><a href='/logout'>Cerrar sesión</a>"
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    return AuthController.login()

@app.route('/logout')
def logout():
    return AuthController.logout()

@app.route('/seleccionar_perfil', methods=['GET', 'POST'])
def seleccionar_perfil():
    if 'nombre' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        perfil = request.form['perfil']
        if perfil == 'alumno':
            return redirect(url_for('dashboard_alumno'))
        elif perfil == 'admin':
            return redirect(url_for('dashboard_admin'))

    return render_template('seleccionar_perfil.html', nombre=session['nombre'])

@app.route('/dashboard_alumno')
def dashboard_alumno():
    if 'nombre' in session:
        return f"Bienvenido al dashboard del alumno, {session['nombre']}"
    return redirect(url_for('login'))

@app.route('/dashboard_admin')
def dashboard_admin():
    if 'nombre' in session:
        return f"Bienvenido al dashboard del administrador, {session['nombre']}"
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
