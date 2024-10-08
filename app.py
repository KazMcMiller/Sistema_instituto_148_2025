from flask import Flask, render_template, request, redirect, url_for, session
from flask_session import Session
from dotenv import load_dotenv
from utils.db_utils import ejecutar_sql

load_dotenv()

app = Flask(__name__)

# Configuración de la sesión
app.config['SECRET_KEY'] = 'tu_clave_secreta'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Datos de usuario para autenticación (normalmente se guardarían en una base de datos)
@app.route('/')
def home():
    if 'nombre' in session:
        return f"¡Hola, {session['nombre']}! <br><a href='/logout'>Cerrar sesión</a>"
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        dni = request.form['dni']
        password = request.form['password']
 
        # Validar el usuario contra la base de datos
        query = "SELECT * FROM usuarios WHERE dni = %s AND pass = %s"
        result = ejecutar_sql(query, (dni, password))
        
        # meto en session el dni y el nombre para usarlo desde la interfaz luego
        if result:
            session['dni'] = dni
            session['nombre'] = result[0][2]
            return redirect(url_for('home'))
        else:
            return "DNI o contraseña incorrectos"
        
    return render_template('login.html')

@app.route('/logout')
def logout():

    session.pop('nombre', None)
    session.pop('dni', None)

    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
