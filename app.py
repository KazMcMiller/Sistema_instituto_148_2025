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
def path_inicial():
    return redirect(url_for('login'))

@app.route('/home')
def home():
    # Verifica si el usuario está autenticado y ha seleccionado un perfil
    if 'nombre' in session and 'perfil' in session:
        perfil_id = session['perfil']
        
        # Consulta para obtener los permisos asociados al perfil seleccionado
        query_permisos = """
            SELECT permisos.id_permiso, permisos.descripcion
            FROM permisos_perfiles
            INNER JOIN permisos ON permisos.id_permiso = permisos_perfiles.id_permisos
            WHERE permisos_perfiles.id_perfil = %s
        """
        permisos = ejecutar_sql(query_permisos, (perfil_id,))
        
        # Convertir los resultados a una lista de nombres de permisos
        lista_permisos = [permiso[1] for permiso in permisos]

        # Renderizar la plantilla y pasar los permisos
        return render_template('home.html', nombre=session['nombre'], permisos=lista_permisos)

    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'nombre' in session:
        return redirect(url_for('seleccionar_perfil'))

    if request.method == 'POST':
        dni = request.form['dni']
        password = request.form['password']
        
        # Validar el usuario contra la base de datos
        query = "SELECT id_usuario, nombre_apellido FROM usuarios WHERE dni = %s AND pass = %s"
        result = ejecutar_sql(query, (dni, password))
        
        if result:
            session['dni'] = dni
            session['nombre'] = result[0][1]  # Suponiendo que el nombre está en la segunda columna del resultado
            session['id_usuario'] = result[0][0]  # Suponiendo que el id_usuario está en la primera columna del resultado
        
            return redirect(url_for('seleccionar_perfil'))
        else:
            return "DNI o contraseña incorrectos"
        
    return render_template('login.html')

@app.route('/seleccionar_perfil', methods=['GET', 'POST'])
def seleccionar_perfil():
    if 'nombre' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        perfil_id = request.form.get('perfil_id')
        session['perfil'] = perfil_id
        return redirect(url_for('home'))

    id_usuario = session['id_usuario']
    query_perfil = """
        SELECT perfiles_usuarios.id_perfil, perfiles.nombre
        FROM perfiles_usuarios 
        INNER JOIN perfiles ON perfiles_usuarios.id_perfil = perfiles.id_perfil 
        WHERE perfiles_usuarios.id_usuarios = %s
    """
    perfiles = ejecutar_sql(query_perfil, (id_usuario,))

    if perfiles is None:
        return "Error al obtener los perfiles o no se encontraron perfiles asociados.", 500

    perfiles = [(perfil[0], perfil[1]) for perfil in perfiles]

    if request.method == 'GET':
        action = request.form.get('seleccionar_perfil')

        print('Perfil seleccionado' + action)

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
