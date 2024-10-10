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
    # Verifica si el usuario está autenticado
    if 'nombre' in session:
        return render_template('seleccionar_perfil.html', nombre=session['nombre'])
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():

    if 'nombre' in session:
        return redirect(url_for('seleccionar_perfil'))

    if request.method == 'POST':
        dni = request.form['dni']
        password = request.form['password']
        
        # Validar el usuario contra la base de datos
        query = "SELECT * FROM usuarios WHERE dni = %s AND pass = %s"
        result = ejecutar_sql(query, (dni, password))
        
        if result:
            session['dni'] = dni
            session['nombre'] = result[0][2]  # Suponiendo que el nombre está en la tercera columna del resultado
            session['id_usuario'] = result[0][0]  # Suponiendo que el id_usuario está en la primera columna del resultado
        
            return redirect(url_for('seleccionar_perfil'))
        
        else:
            return "DNI o contraseña incorrectos"
        
    return render_template('login.html')

@app.route('/seleccionar_perfil', methods=['GET', 'POST'])
def seleccionar_perfil():
    if request.method == 'GET':
        # Verificamos si el usuario ya está en la sesión
        if 'nombre' not in session:
            return redirect(url_for('login'))

        # Realizamos la consulta para obtener los perfiles asociados al usuario
        id_usuario = session['id_usuario']
        query_perfil = """
            SELECT perfiles_usuarios.id_perfil, perfiles.nombre 
            FROM perfiles_usuarios 
            INNER JOIN perfiles ON perfiles.id_perfil = perfiles_usuarios.id_perfil 
            WHERE id_usuarios = %s
        """
        
        # Ejecutar la consulta
        perfiles = ejecutar_sql(query_perfil, (id_usuario,))
        perfiles = [(perfil[0], perfil[1]) for perfil in perfiles]

        # Renderizar la plantilla de selección de perfil y pasar los perfiles disponibles
        return render_template('seleccionar_perfil.html', nombre=session['nombre'], perfiles=perfiles)


@app.route('/dashboard_alumno')
def dashboard_alumno():
    # Verificar si el usuario está autenticado y si es administrador
    if 'nombre' in session:
        return redirect(url_for('home'))
    return redirect(url_for('login'))

@app.route('/dashboard_admin')
def dashboard_admin():
    # Verificar si el usuario está autenticado y si es administrador
    if 'nombre' in session:
        return redirect(url_for('home'))
    return redirect(url_for('login'))

@app.route('/pre_inscripcion')
def pre_inscripcion():
    # Renderiza la página de pre-inscripción
    return render_template('pre_inscripcion.html')

@app.route('/alumnos')
def alumnos():
    # Renderiza la página de gestión de alumnos
    return render_template('alumnos.html')

@app.route('/profesores')
def profesores():
    # Renderiza la página de gestión de profesores
    return render_template('profesores.html')

@app.route('/carreras')
def carreras():
    # Renderiza la página de gestión de carreras
    return render_template('carreras.html')

@app.route('/horarios')
def horarios():
    # Renderiza la página de gestión de horarios
    return render_template('horarios.html')

@app.route('/secretaria')
def secretaria():
    # Renderiza la página de gestión de la secretaría
    return render_template('secretaria.html')

@app.route('/reportes')
def reportes():
    # Renderiza la página de generación de reportes
    return render_template('reportes.html')


@app.route('/logout')
def logout():

    session.pop('nombre', None)
    session.pop('dni', None)

    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
