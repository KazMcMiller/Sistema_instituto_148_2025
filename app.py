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
    else:
        return redirect(url_for('login'))

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


@app.route('/alumnos', methods=['GET'])
def alumnos():
    if 'nombre' not in session:
        return redirect(url_for('login'))

    # Consulta para la lista de alumnos con todos los campos
    query_alumnos = """
        SELECT dni, nombre_apellido, id_usuario, id_sexo, fecha_nacimiento, lugar_nacimiento,
        id_estado_civil, cantidad_hijos, familiares_a_cargo, domicilio, piso, id_localidad,
        id_pais, id_provincia, codigo_postal, telefono, telefono_alt, telefono_alt_propietario,
        email, titulo_base, anio_egreso, id_institucion, otros_estudios, anio_egreso_otros,
        trabaja, actividad, horario_habitual, obra_social, pass, activo
        FROM usuarios
    """
    usuarios = ejecutar_sql(query_alumnos)

    # Consulta para la lista de personas en pre-inscripciones con todos los campos
    query_pre_inscripciones = """
        SELECT dni, nombre_apellido, id_usuario, id_sexo, fecha_nacimiento, lugar_nacimiento,
        id_estado_civil, cantidad_hijos, familiares_a_cargo, domicilio, piso, id_localidad,
        id_pais, id_provincia, codigo_postal, telefono, telefono_alt, telefono_alt_propietario,
        email, titulo_base, anio_egreso, id_institucion, otros_estudios, anio_egreso_otros,
        trabaja, actividad, horario_habitual, obra_social, pass, activo
        FROM pre_inscripciones
    """
    pre_inscripciones = ejecutar_sql(query_pre_inscripciones)

    return render_template('alumnos.html', usuarios=usuarios, pre_inscripciones=pre_inscripciones)

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

@app.route('/pre_inscripcion')
def pre_inscripcion():
    if 'nombre' not in session:
        return redirect(url_for('login'))
    # Renderiza la página de pre-inscripción
    return render_template('pre_inscripcion.html')


@app.route('/pre_inscripcion_2', methods=['POST'])
def pre_inscripcion_2():
    if 'nombre' not in session:
        return redirect(url_for('login'))

    # Recibir los datos del formulario anterior
    datos_personales = request.form.to_dict()
    
    # Guardar en la sesión para usarlos más adelante
    session['datos_personales'] = datos_personales

    return render_template('pre_inscripcion_2.html', **datos_personales)

@app.route('/guardar_pre_inscripcion', methods=['POST'])
def guardar_pre_inscripcion():
    # Verificar si el usuario está autenticado

 # Obtener todos los datos desde la sesión
    datos = session.get('datos_completos', {})
    
    # Ajustar campos que pueden no estar presentes
    trabaja = datos.get('trabaja', '2')  # Si no está presente, asumimos que la respuesta es 'no'
    actividad = datos.get('actividad', '') if trabaja == '1' else None
    horario_habitual = datos.get('horario_habitual', '') if trabaja == '1' else None
    obra_social = datos.get('obra_social', '') if trabaja == '1' else None
    anio_egreso_otros = datos.get('anio_egreso_otros', None)
    if anio_egreso_otros == '':
        anio_egreso_otros = None

    # Consulta SQL para insertar en la tabla usuarios
    query_usuario = """
        INSERT INTO pre_inscripciones (
            dni, nombre_apellido, id_sexo, fecha_nacimiento, lugar_nacimiento, id_estado_civil,
            cantidad_hijos, familiares_a_cargo, domicilio, piso, id_localidad, id_pais,
            id_provincia, codigo_postal, telefono, telefono_alt, telefono_alt_propietario, email,
            titulo_base, anio_egreso, id_institucion, otros_estudios, anio_egreso_otros,
            trabaja, actividad, horario_habitual, obra_social
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    # Ejecutar la consulta
    ejecutar_sql(query_usuario, (
        datos['dni'], datos['nombre_apellido'], datos['id_sexo'],
        datos['fecha_nacimiento'], datos['lugar_nacimiento'], datos['id_estado_civil'],
        datos['cantidad_hijos'], datos['familiares_a_cargo'], datos['domicilio'],
        datos['piso'], datos['id_localidad'], datos['id_pais'],
        datos['id_provincia'], datos['codigo_postal'], datos['telefono'],
        datos['telefono_alt'], datos['telefono_alt_propietario'], datos['email'],
        datos['titulo_base'], datos['anio_egreso'], datos['id_institucion'],
        datos['otros_estudios'], anio_egreso_otros, trabaja,
        actividad, horario_habitual, obra_social
    ))

    # Redirigir al home una vez completada la inscripción
    return redirect(url_for('home'))




@app.route('/pre_inscripcion_3', methods=['POST'])
def pre_inscripcion_3():
    # Verificar si el usuario está autenticado
    if 'nombre' not in session:
        return redirect(url_for('login'))

    # Obtener los datos personales desde la sesión
    datos_personales = session.get('datos_personales', {})
    print(session.get('datos_personales'))
    # Recibir los datos de estudios y laborales del formulario de pre_inscripcion_2
    datos_estudios_y_laborales = request.form.to_dict()

    # Combinar todos los datos
    datos_completos = {**datos_personales, **datos_estudios_y_laborales}
    session['datos_completos'] = datos_completos

    # Renderizar pre_inscripcion_3.html con los datos combinados para la revisión
    return render_template('pre_inscripcion_3.html', **datos_completos)

@app.route('/inscribite')
def inscribite():
    # Renderiza la página de inscribite
    return render_template('inscribite.html')


@app.route('/inscribite_2', methods=['POST'])
def inscribite_2():

    # Recibir los datos del formulario anterior
    datos_personales = request.form.to_dict()
    
    # Guardar en la sesión para usarlos más adelante
    session['datos_personales'] = datos_personales

    return render_template('inscribite_2.html', **datos_personales)

@app.route('/inscribite_3', methods=['POST'])
def inscribite_3():

    # Obtener los datos personales desde la sesión
    datos_personales = session.get('datos_personales', {})
    print(session.get('datos_personales'))
    # Recibir los datos de estudios y laborales del formulario de pre_inscripcion_2
    datos_estudios_y_laborales = request.form.to_dict()

    # Combinar todos los datos
    datos_completos = {**datos_personales, **datos_estudios_y_laborales}
    session['datos_completos'] = datos_completos

    # Renderizar inscribite_3.html con los datos combinados para la revisión
    return render_template('inscribite_3.html', **datos_completos)





@app.route('/logout')
def logout():

    session.pop('nombre', None)
    session.pop('dni', None)

    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
