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
        
        if result:
            session['dni'] = dni
            session['nombre'] = result[0][2]  # Suponiendo que el nombre está en la tercera columna del resultado
            
            # Verificar si el usuario tiene el perfil múltiple (id_perfil = 1)
            query_perfil = "SELECT id_perfil FROM perfiles_usuarios WHERE id_usuarios = %s AND id_perfil = 1"
            perfil_result = ejecutar_sql(query_perfil, (result[0][0],))  # result[0][0] es el id_usuario

            # Si el usuario tiene el id_perfil = 1, redirigir a la pantalla de selección de perfil
            if perfil_result:
                return redirect(url_for('seleccionar_perfil'))

            # Redirigir según el perfil único si no tiene perfil múltiple
            elif perfil_result and perfil_result[0][0] == 2:  # Supongamos que 2 es solo "alumno"
                return redirect(url_for('dashboard_alumno'))
            elif perfil_result and perfil_result[0][0] == 3:  # Supongamos que 3 es solo "admin"
                return redirect(url_for('dashboard_admin'))
            else:
                return "Perfil de usuario no válido"
        else:
            return "DNI o contraseña incorrectos"
        
    return render_template('login.html')


@app.route('/seleccionar_perfil', methods=['GET', 'POST'])
def seleccionar_perfil():
    # Verificamos si el usuario ya está en la sesión
    if 'nombre' not in session:
        return redirect(url_for('login'))

    # Si la solicitud es POST, se obtiene el perfil seleccionado por el usuario
    if request.method == 'POST':
        perfil = request.form['perfil']

        # Redirigir según el perfil elegido
        if perfil == 'alumno':
            return redirect(url_for('dashboard_alumno'))
        elif perfil == 'admin':
            return redirect(url_for('dashboard_admin'))

    # Renderizar la plantilla de selección de perfil
    return render_template('seleccionar_perfil.html', nombre=session['nombre'])

@app.route('/dashboard_alumno')
def dashboard_alumno():
    # Verificar si el usuario está autenticado y si es alumno
    if 'nombre' in session:
        return f"Bienvenido al dashboard del alumno, {session['nombre']}"
    return redirect(url_for('login'))

@app.route('/dashboard_admin')
def dashboard_admin():
    # Verificar si el usuario está autenticado y si es administrador
    if 'nombre' in session:
        return f"Bienvenido al dashboard del administrador, {session['nombre']}"
    return redirect(url_for('login'))


@app.route('/logout')
def logout():

    session.pop('nombre', None)
    session.pop('dni', None)

    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
