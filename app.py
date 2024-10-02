
from flask import Flask, render_template, request, redirect, url_for, session
from flask_session import Session
import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error

from utils.db_utils import ejecutar_sql

load_dotenv()

app = Flask(__name__)

# Configuración de la sesión
app.config['SECRET_KEY'] = 'tu_clave_secreta'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Datos de usuario para autenticación (normalmente se guardarían en una base de datos)
users = {"admin": "password123"}

@app.route('/')
def home():
    if 'username' in session:
        return f"¡Hola, {session['username']}! <br><a href='/logout'>Cerrar sesión</a>"
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():

    resultado = ejecutar_sql("SELECT * FROM test ORDER BY test DESC LIMIT 1")
    print("Resultado de la consulta:", resultado)

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Validar el usuario
        if username in users and users[username] == password:
            session['username'] = username
            return redirect(url_for('home'))
        else:
            return "Nombre de usuario o contraseña incorrectos"
        
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
