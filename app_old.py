from flask import Flask, render_template, request, redirect, url_for, session, flash
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
    # Verifica si el usuario está autenticado y ha seleccionado un perfil
     if 'nombre' in session:
        return redirect(url_for('seleccionar_perfil'))

@app.route('/home')
def home():
    # Verifica si el usuario está autenticado y ha seleccionado un perfil
    if 'nombre' in session and 'perfil' in session:
        perfil_id = session['perfil']
        

        # Renderizar la plantilla y pasar los permisos
        return render_template('home.html', nombre=session['nombre'])

    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'nombre' in session:
        return redirect(url_for('seleccionar_perfil'))

    if request.method == 'POST':
        dni = request.form['dni']
        password = request.form['password']
        
        # Validar el usuario contra la base de datos
        query = "SELECT id_usuario, nombre_apellido FROM usuarios WHERE dni = %s AND pass = %s AND activo = 1"
        result = ejecutar_sql(query, (dni, password))
        
        if result:
            session['dni'] = dni
            session['nombre'] = result[0][1]  # Suponiendo que el nombre está en la segunda columna del resultado
            session['id_usuario'] = result[0][0]  # Suponiendo que el id_usuario está en la primera columna del resultado
        
            return redirect(url_for('seleccionar_perfil'))
        else:
            flash('DNI o contraseña incorrectos', 'error')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/seleccionar_perfil', methods=['GET', 'POST'])
def seleccionar_perfil():
    if 'nombre' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Obtener el perfil seleccionado desde el formulario
        perfil_id = request.form.get('seleccionar_perfil')

        session['perfil'] = perfil_id  # Guarda el perfil en la sesión
        return redirect(url_for('home'))

    # Obtener los perfiles para la selección
    id_usuario = session['id_usuario']
    query_perfil = """
        SELECT perfiles_usuarios.id_perfil, perfiles.nombre
        FROM perfiles_usuarios 
        INNER JOIN perfiles ON perfiles_usuarios.id_perfil = perfiles.id_perfil 
        WHERE perfiles_usuarios.id_usuarios = %s
    """
    perfiles = ejecutar_sql(query_perfil, (id_usuario,))


    # Verificar si la consulta devolvió resultados
    if perfiles is None:
        return "Error al obtener los perfiles o no se encontraron perfiles asociados.", 500

    # Convertir los resultados a una lista de tuplas
    perfiles = [(perfil[0], perfil[1]) for perfil in perfiles]

    session['perfiles'] = perfiles
    
    return render_template('seleccionar_perfil.html', nombre=session['nombre'], perfiles=perfiles)

@app.context_processor
def inject_navbar_data():
    # Obtener los perfiles para la barra de navegación
    id_usuario = session.get('id_usuario')


    if id_usuario:
        perfil_seleccionado = session.get('perfil')

        query_perfil = """
            SELECT id_permisos FROM permisos_perfiles WHERE id_perfil = %s
        """
        permisos = ejecutar_sql(query_perfil, (perfil_seleccionado,))

        permisos = [permiso[0] for permiso in permisos]

    else:
        permisos = []

    return dict(permisos=permisos)


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
    if 'nombre' not in session:
        return redirect(url_for('login'))
    # Renderiza la página de pre-inscripción
    return render_template('pre_inscripcion.html')

@app.route('/alumnos', methods=['GET'])
def alumnos():
    if 'nombre' not in session:
        return redirect(url_for('login'))

    # Consultas de ejemplo para cada tabla
    query_alumnos = "SELECT id_usuario, nombre_apellido, dni FROM usuarios"

    usuarios = ejecutar_sql(query_alumnos)

    return render_template('alumnos.html', usuarios=usuarios,)

@app.route('/profesores')
def profesores():
    if 'nombre' not in session:
        return redirect(url_for('login'))
    # Renderiza la página de gestión de profesores
    return render_template('profesores.html')

@app.route('/carreras')
def carreras():
    if 'nombre' not in session:
        return redirect(url_for('login'))
    # Renderiza la página de gestión de carreras
    return render_template('carreras.html')

@app.route('/horarios')
def horarios():
    if 'nombre' not in session:
        return redirect(url_for('login'))
    # Renderiza la página de gestión de horarios
    return render_template('horarios.html')

@app.route('/secretaria')
def secretaria():
    if 'nombre' not in session:
        return redirect(url_for('login'))
    # Renderiza la página de gestión de la secretaría
    return render_template('secretaria.html')

@app.route('/reportes')
def reportes():
    if 'nombre' not in session:
        return redirect(url_for('login'))
    # Renderiza la página de generación de reportes
    return render_template('reportes.html')

@app.route('/pre_inscripcion_2', methods=['POST'])
def pre_inscripcion_2():
    if 'nombre' not in session:
            return redirect(url_for('login'))
    return render_template('pre_inscripcion_2.html')

@app.route('/guardar_pre_inscripcion', methods=['POST'])
def guardar_pre_inscripcion():
    if 'nombre' not in session:
            return redirect(url_for('login'))
    return render_template('pre_inscripcion_3.html')


    # # Recibir todos los datos desde el formulario de pre_inscripcion_3.html
    # datos = request.form.to_dict()
    
    # # Aquí realizas las consultas para guardar los datos en la base de datos.
    # # Ejemplo de una consulta para guardar en una tabla de usuarios
    # query = """
    #     INSERT INTO usuarios (
    #         nombre_apellido, dni, sexo, fecha_nacimiento, lugar_nacimiento, ...
    #     ) VALUES (%s, %s, %s, %s, %s, ...)
    # """
    # # Ejecutar la consulta
    # ejecutar_sql(query, (
    #     datos['apellido_nombres'], datos['dni'], datos['sexo'],
    #     datos['fecha_nacimiento'], datos['lugar_nacimiento'], 
    #     # Completar con los otros campos
    # ))

    # return redirect(url_for('home'))

@app.route('/logout')
def logout():

    session.pop('nombre', None)
    session.pop('dni', None)

    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
