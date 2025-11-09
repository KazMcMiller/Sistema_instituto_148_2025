from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_session import Session
from dotenv import load_dotenv
from utils.db_utils import ejecutar_sql
import json
from functools import wraps
from flask import jsonify
from io import BytesIO
from flask import send_file
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta


# Aca importamos todo lo que vayamos a usar, en el documento de requerimientos estan todas las librerias que se usan
# en la consola usen el metodo pip para instalar cosas como flask

load_dotenv() #dotenv es una biblioteca de Nodejs que permite cargar las variables de entorno desde un archivo .env.
app = Flask(__name__, template_folder='templates')

# Configuración de la sesión
app.config['SECRET_KEY'] = 'tu_clave_secreta'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

#para crear rutas en flask usamos esta estructura
@app.route('/')
def path_inicial():
    # Verifica si el usuario está autenticado y ha seleccionado un perfil, esto se hara en cada ruta necesaria
    if 'nombre' in session:
        return redirect(url_for('seleccionar_perfil'))
    else:
        return redirect(url_for('login'))

# Ruta para el home donde se mostrarán los mensajes
@app.route('/home')
def home():
    if 'nombre' not in session:
        return redirect(url_for('login'))

    nombre = session['nombre']
    # Filtrar mensajes que hayan sido enviados en los últimos 7 días
    fecha_limite = datetime.now() - timedelta(days=2)
    query_mensajes = """
        SELECT mensaje, dia FROM mensajes
        WHERE dia >= %s
        ORDER BY dia DESC
    """
    mensajes = ejecutar_sql(query_mensajes, (fecha_limite,)) #ejecutar_sql enviara una consulta sql a tu base de datos,
                                                    #espera un parametro que es la query y mas de uno si usas %s, como en este caso

    return render_template('home.html',nombre=nombre, mensajes=mensajes)

@app.route('/login', methods=['GET', 'POST']) #en las rutas, puedes definir que metodos usar para hacer una cosa dependiendo cada metodo
def login():
    if 'nombre' in session:
        return redirect(url_for('seleccionar_perfil'))

    if request.method == 'POST': #por ejemplo, aqui, si el metodo es POST, haremos todo esto en el login
        dni = request.form['dni']
        password = request.form['password']
        
        # Validar el usuario contra la base de datos
        query = "SELECT id_usuario, nombre FROM usuarios WHERE dni = %s AND pass = %s AND activo = 1"
        result = ejecutar_sql(query, (dni, password))
        
        if result: #meter en session (donde se guardan los datos)
            session['dni'] = dni
            session['nombre'] = result[0][1]  # Suponiendo que el nombre está en la segunda columna del resultado
            session['id_usuario'] = result[0][0]  # Suponiendo que el id_usuario está en la primera columna del resultado
            id_usuario = session['id_usuario']  # ID del usuario autenticado

            # Consulta para obtener el instituto asociado al usuario
            query_instituto_usuario = """
                SELECT id_instituto
                FROM instituto_usuario
                WHERE id_usuario = %s
            """
            id_instituto = ejecutar_sql(query_instituto_usuario, (id_usuario,))[0][0]

            # Guardar el ID de la institución en la sesión
            session['id_instituto'] = id_instituto
            
            return redirect(url_for('seleccionar_perfil'))
        else:
            flash('DNI o contraseña incorrectos', 'error')
            return redirect(url_for('login'))
    return render_template('login.html')

# Decorador personalizado para restringir el acceso a ciertas funciones según el perfil del usuario.
# Acepta una lista de perfiles permitidos, y si el perfil del usuario no está en esa lista, redirige a la página de inicio.
def perfil_requerido(perfiles_permitidos):
    def decorador(f):
        # Preserva la información original de la función 'f' para que el decorador no afecte su nombre o documentación.
        @wraps(f)
        def funcion_verificada(*args, **kwargs):
            # Verifica si el usuario ha seleccionado un perfil en la sesión.
            if 'perfil' not in session:
                # Si el perfil no está en la sesión, redirige al usuario a la página de selección de perfil.
                return redirect(url_for('seleccionar_perfil'))
            
            # Verifica si el perfil del usuario está en la lista de perfiles permitidos.
            if session['perfil'] not in perfiles_permitidos:
                # Si el perfil no está en la lista de permitidos, redirige al usuario a la página de inicio.
                return redirect(url_for('home'))
            
            # Si el perfil está permitido, se ejecuta la función original.
            return f(*args, **kwargs)
        
        # Retorna la función verificada que será ejecutada en lugar de la original.
        return funcion_verificada

    # Retorna el decorador configurado con los perfiles permitidos.
    return decorador

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

# Función para inyectar datos específicos en el contexto de la plantilla, permitiendo que las plantillas 
# tengan acceso a datos sobre permisos de usuario para mostrar u ocultar elementos de la barra de navegación (navbar.html).
@app.context_processor
def inject_navbar_data():
    # Obtener el ID del usuario desde la sesión
    id_usuario = session.get('id_usuario')

    # Verifica si el usuario ha iniciado sesión (si id_usuario existe en la sesión)
    if id_usuario:
        # Obtiene el perfil seleccionado por el usuario desde la sesión
        perfil_seleccionado = session.get('perfil')

        # Consulta SQL para obtener los permisos asociados al perfil seleccionado
        query_perfil = """
            SELECT id_permisos FROM permisos_perfiles WHERE id_perfil = %s
        """
        # Ejecuta la consulta para obtener los permisos del perfil
        permisos = ejecutar_sql(query_perfil, (perfil_seleccionado,))

        # Convierte los permisos obtenidos en una lista simple de IDs
        permisos = [permiso[0] for permiso in permisos]

    else:
        # Si no hay usuario en la sesión, asigna una lista vacía de permisos
        permisos = []

    # Devuelve un diccionario con la lista de permisos que estará disponible en el contexto de las plantillas
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


# esta funcion y ruta crea una tabla con un filtro de busqueda y un boton para activos e inactivos
# tanto para alumnos como para pre-inscriptos, estos ultimos si los editas podras darlos de alta mas adelante
@app.route('/alumnos', methods=['GET'])
@perfil_requerido(['1', '2'])
def alumnos():
    page = int(request.args.get('page', 1))
    table = request.args.get('table', 'alumnos')
    nombre_busqueda = request.args.get('nombre_busqueda', '')
    estado_activo = request.args.get('activo', 'all')
    per_page = 10

    # Query for usuarios (Alumnos, filtered by perfiles_usuarios with id_perfil=4)
    alumnos_query = """
        SELECT u.id_usuario, u.dni, u.nombre, u.apellido, u.localidad, u.telefono
        FROM usuarios u
        JOIN perfiles_usuarios pu ON u.id_usuario = pu.id_usuarios
        WHERE pu.id_perfil = 4
        AND (%s = '' OR CONCAT(u.nombre, ' ', u.apellido) LIKE %s)
        AND (%s = 'all' OR u.activo = %s)
        LIMIT %s OFFSET %s
    """
    alumnos_count_query = """
        SELECT COUNT(*)
        FROM usuarios u
        JOIN perfiles_usuarios pu ON u.id_usuario = pu.id_usuarios
        WHERE pu.id_perfil = 4
        AND (%s = '' OR CONCAT(u.nombre, ' ', u.apellido) LIKE %s)
        AND (%s = 'all' OR u.activo = %s)
    """
    nombre_param = '' if not nombre_busqueda else f'%{nombre_busqueda}%'
    activo_param = estado_activo if estado_activo in ['0', '1'] else 'all'
    offset = (page - 1) * per_page
    alumnos = ejecutar_sql(alumnos_query, (nombre_busqueda, nombre_param, estado_activo, activo_param, per_page, offset))
    total_alumnos = ejecutar_sql(alumnos_count_query, (nombre_busqueda, nombre_param, estado_activo, activo_param))[0][0]
    total_paginas_alumnos = (total_alumnos + per_page - 1) // per_page

    # Query for pre_inscripciones (join with inscripciones_carreras)
    pre_inscripciones_query = """
        SELECT p.id_usuario, p.dni, p.nombre, p.apellido, p.localidad, p.telefono,
               i.nombre_instituto, c.nombre AS nombre_carrera, t.descripcion AS descripcion_turno
        FROM pre_inscripciones p
        JOIN inscripciones_carreras ic ON p.id_usuario = ic.id_usuario
        LEFT JOIN institutos i ON p.id_institucion = i.id_instituto
        LEFT JOIN lista_carreras c ON ic.id_carrera = c.id_carrera
        LEFT JOIN turno_carrera t ON ic.id_turno = t.id_turno
        WHERE (%s = '' OR CONCAT(p.nombre, ' ', p.apellido) LIKE %s)
        AND (%s = 'all' OR p.activo = %s)
        LIMIT %s OFFSET %s
    """
    pre_inscripciones_count_query = """
        SELECT COUNT(*)
        FROM pre_inscripciones p
        JOIN inscripciones_carreras ic ON p.id_usuario = ic.id_usuario
        WHERE (%s = '' OR CONCAT(p.nombre, ' ', p.apellido) LIKE %s)
        AND (%s = 'all' OR p.activo = %s)
    """
    pre_inscripciones = ejecutar_sql(pre_inscripciones_query, (nombre_busqueda, nombre_param, estado_activo, activo_param, per_page, offset))
    total_pre_inscripciones = ejecutar_sql(pre_inscripciones_count_query, (nombre_busqueda, nombre_param, estado_activo, activo_param))[0][0]
    total_paginas_pre_inscripciones = (total_pre_inscripciones + per_page - 1) // per_page

    return render_template(
        'alumnos.html',
        alumnos=alumnos,
        pre_inscripciones=[{
            'id_usuario': p[0], 'dni': p[1], 'nombre': p[2], 'apellido': p[3],
            'localidad': p[4], 'telefono': p[5], 'nombre_instituto': p[6],
            'nombre_carrera': p[7], 'descripcion_turno': p[8]
        } for p in pre_inscripciones],
        table=table,
        page=page,
        total_paginas_alumnos=total_paginas_alumnos,
        total_paginas_pre_inscripciones=total_paginas_pre_inscripciones,
        nombre_busqueda=nombre_busqueda,
        estado_activo=estado_activo
    )


# aqui entraremos cuando seleccionamos un usuario, primero hara un get para tomar todos sus datos y 
# mostrarlos de la manera que queremos, despues, si cambiamos algo, hara un post para generar un update en la tabla usuarios
@app.route('/alumno/<int:id_usuario>', methods=['GET', 'POST'])
@perfil_requerido(['1', '2'])  # Solo perfiles 1 (directivo) y 2 (preseptor) pueden acceder
def editar_alumno(id_usuario):
    if 'nombre' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Recibir datos actualizados desde el formulario y actualizar en la base de datos
        datos = request.form.to_dict()

        # Convertir los campos a enteros, si es necesario
        datos['id_localidad'] = int(datos['id_localidad']) if datos['id_localidad'].isdigit() else None
        datos['id_pais'] = int(datos['id_pais']) if datos['id_pais'].isdigit() else None
        datos['id_provincia'] = int(datos['id_provincia']) if datos['id_provincia'].isdigit() else None
        datos['carrera'] = int(datos['carrera']) if datos['carrera'].isdigit() else None
        datos['turno'] = int(datos['turno']) if datos['turno'].isdigit() else None

        # Normalizar campos que pueden ser nulos
        datos['lugar_nacimiento'] = datos.get('lugar_nacimiento') or None
        datos['telefono_alt'] = datos.get('telefono_alt') or None
        datos['telefono_alt_propietario'] = datos.get('telefono_alt_propietario') or None
        datos['titulo_base'] = datos.get('titulo_base') or None
        datos['anio_egreso_otros'] = datos.get('anio_egreso_otros') or None
        datos['actividad'] = datos.get('actividad') or None
        datos['horario_habitual'] = datos.get('horario_habitual') or None
        datos['obra_social'] = datos.get('obra_social') or None
        datos['piso'] = datos.get('piso') if datos.get('piso') and datos['piso'] != 'NULL' else None

        # Consulta para actualizar los datos del alumno en usuarios
        query_update = """
            UPDATE usuarios SET 
                dni = %s, nombre = %s, apellido = %s, id_sexo = %s, fecha_nacimiento = %s, lugar_nacimiento = %s, 
                id_estado_civil = %s, cantidad_hijos = %s, familiares_a_cargo = %s, domicilio = %s, 
                piso = %s, id_localidad = %s, id_pais = %s, id_provincia = %s, codigo_postal = %s, 
                telefono = %s, telefono_alt = %s, telefono_alt_propietario = %s, email = %s, 
                titulo_base = %s, anio_egreso = %s, id_institucion = %s, otros_estudios = %s, 
                anio_egreso_otros = %s, trabaja = %s, actividad = %s, horario_habitual = %s, 
                obra_social = %s
            WHERE id_usuario = %s
        """
        ejecutar_sql(query_update, (
            datos['dni'], datos['nombre'], datos['apellido'], datos['id_sexo'], datos['fecha_nacimiento'], datos['lugar_nacimiento'],
            datos['id_estado_civil'], datos['cantidad_hijos'], datos['familiares_a_cargo'], datos['domicilio'],
            datos['piso'], datos['id_localidad'], datos['id_pais'], datos['id_provincia'], datos['codigo_postal'],
            datos['telefono'], datos['telefono_alt'], datos['telefono_alt_propietario'], datos['email'],
            datos['titulo_base'], datos['anio_egreso'], datos['id_institucion'], datos['otros_estudios'],
            datos['anio_egreso_otros'], datos['trabaja'], datos['actividad'], datos['horario_habitual'],
            datos['obra_social'], id_usuario
        ))

        # Obtener la inscripción actual
        query_inscripcion = """
            SELECT id_carrera, turno FROM inscripciones_carreras WHERE id_usuario = %s AND activo = 1
        """
        inscripcion_actual = ejecutar_sql(query_inscripcion, (id_usuario,))

        # Actualizar la carrera y el turno en inscripciones_carreras y cambiar estado_alumno a 2
        query_update_inscripcion = """
            UPDATE inscripciones_carreras SET 
                id_carrera = %s, turno = %s, estado_alumno = 'inscripto', fecha_inscripcion = %s
            WHERE id_usuario = %s AND activo = 1
        """
        ejecutar_sql(query_update_inscripcion, (
            datos['carrera'], datos['turno'], date.today(), id_usuario
        ))

        return redirect(url_for('alumnos'))

    # Si es GET, obtener los datos del alumno y preparar el formulario
    query_ingresante = "SELECT * FROM usuarios WHERE id_usuario = %s"
    ingresante = ejecutar_sql(query_ingresante, (id_usuario,))[0]


    # Obtener carrera y turno actuales del alumno en inscripciones_carreras
    query_carrera_turno = """
        SELECT id_carrera, turno FROM inscripciones_carreras WHERE id_usuario = %s AND activo = 1
    """
    resultado = ejecutar_sql(query_carrera_turno, (id_usuario,))
    alumno_carrera_id = resultado[0][0] if resultado else None
    alumno_turno = resultado[0][1] if resultado else None  # `id_turno` en vez de la descripción
    print (alumno_carrera_id)
    print (alumno_turno)

    # Obtener los países
    query_paises = "SELECT id_pais, nombre FROM paises"
    paises = ejecutar_sql(query_paises)

    # Obtener las provincias
    query_provincias = "SELECT id_provincia, nombre, id_pais FROM provincias"
    provincias = ejecutar_sql(query_provincias)

    # Obtener las localidades
    query_localidades = "SELECT id_localidad, nombre, id_provincia FROM localidades"
    localidades = ejecutar_sql(query_localidades)

    # Obtener las carreras y turnos
    query_carreras = "SELECT id_carrera, nombre FROM lista_carreras WHERE estado = 1"
    lista_carreras = ejecutar_sql(query_carreras)

 # Obtener los turnos asociados a las carreras
    query_turnos = """
        SELECT id_turno, id_carrera, descripcion FROM turno_carrera WHERE estado = 1
    """
    turnos_carreras = ejecutar_sql(query_turnos)
    turnos_carreras = [{"id_turno": turno[0], "id_carrera": turno[1], "descripcion": turno[2]} for turno in turnos_carreras]
    # Determina si el alumno está activo o inactivo basado en el valor de alumno[30]
    estado_actual = "Activo" if ingresante[30] == 1 else "Inactivo"

    return render_template(
        'editar_alumno.html',
        alumno=ingresante,
        paises=paises,
        provincias=provincias,
        localidades=localidades,
        lista_carreras=lista_carreras,
        turnos_carreras=turnos_carreras,
        alumno_carrera_id=alumno_carrera_id,
        alumno_turno=alumno_turno,
        estado_actual=estado_actual  # Enviar el estado como texto
    )


@app.route('/alumno/<int:id_usuario>/borrar', methods=['POST']) #alternar entre activo o inactivo, no los borra
@perfil_requerido(['1', '2'])  # Solo perfiles 1 (directivo) y 2 (preseptor) pueden acceder
def borrar_alumno(id_usuario):
    if 'nombre' not in session:
        return redirect(url_for('login'))

    # Consulta para alternar el valor de 'activo' entre 0 y 1
    query_toggle_activo = """
        UPDATE usuarios
        SET activo = CASE
            WHEN activo = 1 THEN 0
            ELSE 1
        END
        WHERE id_usuario = %s
    """
    ejecutar_sql(query_toggle_activo, (id_usuario,))

    return redirect(url_for('alumnos'))

#esta funcion toma todos los formularios llenados con datos de posibles estudiantes y si son correctos darlos de alta
#lo mismo que hace con alumnos pero cuando hacemos un POST, sera para darlos de alta y poder llevarlos con un insert usuarios
@app.route('/ingresante/<int:id_usuario>', methods=['GET', 'POST'])
@perfil_requerido(['1', '2'])  # Solo perfiles 1 (directivo) y 2 (preseptor) pueden acceder
def editar_ingresante(id_usuario):
    if 'nombre' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Recibir datos actualizados desde el formulario
        datos = request.form.to_dict()

        # Normalizar campos que pueden ser nulos
        datos['id_localidad'] = int(datos['id_localidad']) if datos['id_localidad'].isdigit() else None
        datos['id_pais'] = int(datos['id_pais']) if datos['id_pais'].isdigit() else None
        datos['id_provincia'] = int(datos['id_provincia']) if datos['id_provincia'].isdigit() else None
        datos['carrera'] = int(datos['carrera']) if datos['carrera'].isdigit() else None
        datos['turno'] = int(datos['turno']) if datos['turno'].isdigit() else None
        datos['lugar_nacimiento'] = datos.get('lugar_nacimiento') or None
        datos['telefono_alt'] = datos.get('telefono_alt') or None
        datos['telefono_alt_propietario'] = datos.get('telefono_alt_propietario') or None
        datos['titulo_base'] = datos.get('titulo_base') or None
        datos['anio_egreso_otros'] = datos.get('anio_egreso_otros') or None
        datos['actividad'] = datos.get('actividad') or None
        datos['horario_habitual'] = datos.get('horario_habitual') or None
        datos['obra_social'] = datos.get('obra_social') or None
        datos['piso'] = datos.get('piso') if datos.get('piso') and datos['piso'] != 'NULL' else None

        # Insertar en usuarios
        query_insert_usuario = """
            INSERT INTO usuarios (
                dni, nombre, apellido, id_sexo, fecha_nacimiento, lugar_nacimiento, id_estado_civil,
                cantidad_hijos, familiares_a_cargo, domicilio, piso, id_localidad, id_pais, id_provincia,
                codigo_postal, telefono, telefono_alt, telefono_alt_propietario, email, titulo_base,
                anio_egreso, id_institucion, otros_estudios, anio_egreso_otros, trabaja, actividad,
                horario_habitual, obra_social, pass, activo
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        values_usuario = (
            datos['dni'], datos['nombre'], datos['apellido'], datos['id_sexo'], datos['fecha_nacimiento'],
            datos['lugar_nacimiento'], datos['id_estado_civil'], datos['cantidad_hijos'], datos['familiares_a_cargo'],
            datos['domicilio'], datos['piso'], datos['id_localidad'], datos['id_pais'], datos['id_provincia'],
            datos['codigo_postal'], datos['telefono'], datos['telefono_alt'], datos['telefono_alt_propietario'],
            datos['email'], datos['titulo_base'], datos['anio_egreso'], datos['id_institucion'], datos['otros_estudios'],
            datos['anio_egreso_otros'], datos['trabaja'], datos['actividad'], datos['horario_habitual'], datos['obra_social'],
            datos['pass'], 1  # activo = 1
        )
        ejecutar_sql(query_insert_usuario, values_usuario)


        query_select_id = "SELECT id_usuario FROM usuarios WHERE dni = %s"
        id_usuario_inscripcion = ejecutar_sql(query_select_id, (datos['dni'],))[0][0]

        # Actualizar la carrera y el turno en inscripciones_carreras con el nuevo id_usuario
        query_insert_inscripcion = """
            INSERT INTO inscripciones_carreras (
                id_usuario, id_carrera, fecha_inscripcion, turno, estado_alumno, activo
            ) VALUES (%s, %s, %s, %s, 'inscripto', %s)
        """
        values_inscripcion = (
            id_usuario_inscripcion, datos['carrera'], date.today(), datos['turno'], 1  # estado_alumno = 2, activo = 1
        )
        ejecutar_sql(query_insert_inscripcion, values_inscripcion)

        # consulta para insertar el perfil de alumno y el id_usuario en perfiles usuarios
        query_ingresar_perfil = """
            INSERT INTO perfiles_usuarios (
                id_perfil, id_usuarios
            ) VALUES (%s, %s)
        """
        # 4 = alumno y buscamos el id del usuario nuevo
        values_ingresar_perfil = (
            4, id_usuario_inscripcion
        )
        ejecutar_sql(query_ingresar_perfil,values_ingresar_perfil)

        # consulta para insertar el id del instituto actual y el id_usuario en instituto usuario
        query_ingresar_instituto = """
            INSERT INTO instituto_usuario (
                id_instituto, id_usuario
            ) VALUES (%s, %s)
        """
        # Buscar el id_instituto correspondiente al usuario
        query_sesion = """
            SELECT id_institucion FROM usuarios WHERE id_usuario = %s
        """
        # Ejecutar la consulta y obtener el resultado
        instituto = ejecutar_sql(query_sesion, (id_usuario_inscripcion,))

        # Acceder al valor de id_institucion si existe en el resultado
        id_instituto = instituto[0][0]

        # metemos en el value los datos
        print (instituto)
        values_ingresar_instituto = (
            id_instituto, id_usuario_inscripcion
        )
        ejecutar_sql(query_ingresar_instituto,values_ingresar_instituto)


        # Consulta para eliminar al ingresante de la base de datos
        query_borrar = "DELETE FROM pre_inscripciones WHERE id_usuario = %s"
        ejecutar_sql(query_borrar, (id_usuario,))

        return redirect(url_for('alumnos'))

    # Si es GET, obtener los datos del ingresante desde pre_inscripciones y prepararlos para el formulario
    query_ingresante = "SELECT * FROM pre_inscripciones WHERE id_usuario = %s"
    ingresante = ejecutar_sql(query_ingresante, (id_usuario,))[0]

    # Obtener carrera y turno actuales en inscripciones_carreras
    query_carrera_turno = """
        SELECT id_carrera, turno FROM inscripciones_carreras WHERE id_usuario = %s AND activo = 1
    """
    resultado = ejecutar_sql(query_carrera_turno, (id_usuario,))
    alumno_carrera_id = resultado[0][0] if resultado else None
    alumno_turno = resultado[0][1] if resultado else None

    # Obtener los países, provincias, localidades, carreras y turnos
    query_paises = "SELECT id_pais, nombre FROM paises"
    query_provincias = "SELECT id_provincia, nombre, id_pais FROM provincias"
    query_localidades = "SELECT id_localidad, nombre, id_provincia FROM localidades"
    query_carreras = "SELECT id_carrera, nombre FROM lista_carreras WHERE estado = 1"
    query_turnos = "SELECT id_turno, id_carrera, descripcion FROM turno_carrera WHERE estado = 1"

    paises = ejecutar_sql(query_paises)
    provincias = ejecutar_sql(query_provincias)
    localidades = ejecutar_sql(query_localidades)
    lista_carreras = ejecutar_sql(query_carreras)
    turnos_carreras = [{"id_turno": turno[0], "id_carrera": turno[1], "descripcion": turno[2]} for turno in ejecutar_sql(query_turnos)]

    return render_template(
        'editar_ingresante.html',
        alumno=ingresante,
        paises=paises,
        provincias=provincias,
        localidades=localidades,
        lista_carreras=lista_carreras,
        turnos_carreras=turnos_carreras,
        alumno_carrera_id=alumno_carrera_id,
        alumno_turno=alumno_turno
    )


@app.route('/ingresante/<int:id_usuario>/borrar', methods=['POST'])
@perfil_requerido(['1', '2'])  # Solo perfiles 1 (directivo) y 2 (preseptor) pueden acceder
def borrar_ingresante(id_usuario):
    if 'nombre' not in session:
        return redirect(url_for('login'))

    # Consulta para eliminar al ingresante de la base de datos
    query_borrar = "DELETE FROM pre_inscripciones WHERE id_usuario = %s"
    ejecutar_sql(query_borrar, (id_usuario,))
    
    return redirect(url_for('alumnos'))



@app.route('/carreras')
@perfil_requerido(['1', '2'])  # Solo perfiles 1 (directivo) y 2 (preseptor) pueden acceder
def carreras():
    if 'nombre' not in session:
        return redirect(url_for('login'))
    # Renderiza la página de gestión de carreras
    return render_template('carreras.html')

@app.route('/horarios')
@perfil_requerido(['1','2', '3', '4'])  # todos los perfiles pueden acceder
def horarios():
    if 'nombre' not in session:
        return redirect(url_for('login'))
    # Renderiza la página de gestión de horarios
    return render_template('horarios.html')

# Ruta para la página de secretaria
@app.route('/secretaria')
@perfil_requerido(['1', '2'])  # Solo perfiles 1 (directivo) y 2 (secretaria) pueden acceder
def secretaria():
    if 'nombre' not in session:
        return redirect(url_for('login'))
    return render_template('secretaria.html')

# Ruta para enviar los mensajes
@app.route('/enviar_mensaje', methods=['POST'])
@perfil_requerido(['1', '2'])
def enviar_mensaje():
    if 'nombre' not in session:
        return redirect(url_for('login'))
    
    mensaje = request.form.get('mensaje')
    id_usuario = session['id_usuario']
    dia = datetime.now()

    # Insertar el mensaje en la tabla mensajes
    query_insertar_mensaje = """
        INSERT INTO mensajes (mensaje, id_usuario, dia)
        VALUES (%s, %s, %s)
    """
    ejecutar_sql(query_insertar_mensaje, (mensaje, id_usuario, dia))

    flash("Mensaje enviado a todos los usuarios", "success")
    return redirect(url_for('secretaria'))

@app.route('/reportes')
@perfil_requerido(['1', '2'])  # Solo perfiles 1 (directivo) y 3 (profesor) pueden acceder
def reportes():
    if 'nombre' not in session:
        return redirect(url_for('login'))
    # Renderiza la página de generación de reportes
    return render_template('reportes.html')

#ruta donde inscribiremos a las personas para que sean alumnos mas tarde
#primero obtiene todos los datos para los selects y si hace un POST, hace validaciones y guarda los datos para pre_inscripcion_2
@app.route('/pre_inscripcion', methods=['GET', 'POST'])
def pre_inscripcion():
    if request.method == 'GET':
        # Fetch dropdown data
        provincias = ejecutar_sql("SELECT id_provincia, nombre FROM provincias")
        paises = ejecutar_sql("SELECT id_pais, nombre FROM paises")
        institutos = ejecutar_sql("SELECT id_instituto, nombre_instituto FROM institutos")
        sexos = ejecutar_sql("SELECT id_sexo, descripcion FROM sexos")
        estados_civiles = ejecutar_sql("SELECT id_estado_civil, nombre FROM estado_civil")
        lista_carreras = ejecutar_sql("SELECT id_carrera, nombre, id_instituto FROM lista_carreras WHERE activo = 1")
        turnos_carreras = ejecutar_sql("SELECT id_turno, descripcion, id_carrera FROM turno_carrera WHERE estado = 1")
        return render_template(
            'pre_inscripcion.html',
            provincias=provincias,
            paises=paises,
            institutos=institutos,
            sexos=sexos,
            estados_civiles=estados_civiles,
            lista_carreras=[{'id_carrera': c[0], 'nombre': c[1], 'id_institucion': c[2]} for c in lista_carreras],
            turnos_carreras=[{'id_turno': t[0], 'descripcion': t[1], 'id_carrera': t[2]} for t in turnos_carreras]
        )
    # POST: Store data and redirect to pre_inscripcion_2
    try:
        form_data = {
            'nombre': request.form.get('nombre'),
            'apellido': request.form.get('apellido'),
            'id_sexo': request.form.get('id_sexo'),
            'dni': request.form.get('dni'),
            'fecha_nacimiento': request.form.get('fecha_nacimiento'),
            'lugar_nacimiento': request.form.get('lugar_nacimiento'),
            'id_estado_civil': request.form.get('id_estado_civil'),
            'cantidad_hijos': request.form.get('cantidad_hijos'),
            'familiares_a_cargo': request.form.get('familiares_a_cargo'),
            'domicilio': request.form.get('domicilio'),
            'piso': request.form.get('piso'),
            'localidad': request.form.get('localidad'),
            'id_provincia': request.form.get('id_provincia'),
            'id_pais': request.form.get('id_pais'),
            'codigo_postal': request.form.get('codigo_postal'),
            'telefono': request.form.get('telefono'),
            'telefono_alt': request.form.get('telefono_alt'),
            'telefono_alt_propietario': request.form.get('telefono_alt_propietario'),
            'email': request.form.get('email'),
            'id_institucion': request.form.get('id_institucion'),
            'carrera': request.form.get('carrera'),
            'turno': request.form.get('turno')
        }
        # Validate required fields
        if not all([form_data['nombre'], form_data['apellido'], form_data['id_sexo'], form_data['dni'],
                    form_data['fecha_nacimiento'], form_data['id_estado_civil'], form_data['cantidad_hijos'],
                    form_data['familiares_a_cargo'], form_data['domicilio'], form_data['piso'],
                    form_data['localidad'], form_data['id_provincia'], form_data['id_pais'],
                    form_data['codigo_postal'], form_data['telefono'], form_data['email'],
                    form_data['id_institucion'], form_data['carrera'], form_data['turno']]):
            flash('Todos los campos obligatorios deben completarse.', 'error')
            return redirect(url_for('pre_inscripcion'))
        session['pre_inscripcion_data'] = form_data
        return redirect(url_for('pre_inscripcion_2'))
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('pre_inscripcion'))

#sigue el formulario y guarda todo para pre_inscripcion_3
@app.route('/pre_inscripcion_2', methods=['GET', 'POST'])
def pre_inscripcion_2():
    if 'pre_inscripcion_data' not in session:
        flash('Datos de pre-inscripción no encontrados.', 'error')
        return redirect(url_for('pre_inscripcion'))
    
    if request.method == 'GET':
        paises = ejecutar_sql("SELECT id_pais, nombre FROM paises")
        provincias = ejecutar_sql("SELECT id_provincia, nombre FROM provincias")
        return render_template(
            'pre_inscripcion_2.html',
            paises=paises,
            provincias=provincias,
            id_pais_estudio=1
        )
    
    try:
        data = session['pre_inscripcion_data']
        data.update({
            'titulo_base': request.form.get('titulo_base'),
            'anio_egreso': request.form.get('anio_egreso'),
            'id_pais_estudio': request.form.get('id_pais_estudio'),
            'provincia_estudio': request.form.get('provincia_estudio'),
            'otros_estudios': request.form.get('otros_estudios'),
            'anio_egreso_otros': request.form.get('anio_egreso_otros'),
            'trabaja': request.form.get('trabaja'),
            'actividad': request.form.get('actividad'),
            'horario_habitual': request.form.get('horario_habitual'),
            'obra_social': request.form.get('obra_social')
        })
        session['pre_inscripcion_data'] = data
        return render_template(
            'pre_inscripcion_3.html',
            **data
        )
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('pre_inscripcion_2'))

@app.route('/confirmar_pre_inscripcion', methods=['POST'])
def confirmar_pre_inscripcion():
    data = session.get('pre_inscripcion_data', {})
    if not data:
        flash('Datos de pre-inscripción no encontrados.', 'error')
        return redirect(url_for('pre_inscripcion'))
    
    try:
        query = """
            INSERT INTO pre_inscripciones (
                dni, nombre, apellido, id_sexo, fecha_nacimiento, lugar_nacimiento,
                id_estado_civil, cantidad_hijos, familiares_a_cargo, domicilio, piso,
                localidad, id_provincia, id_pais, codigo_postal, telefono, telefono_alt,
                telefono_alt_propietario, email, titulo_base, anio_egreso, id_institucion,
                otros_estudios, anio_egreso_otros, trabaja, actividad, horario_habitual,
                obra_social, pass, activo
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, '12345678', 1)
        """
        ejecutar_sql(query, (
            data['dni'], data['nombre'], data['apellido'], data['id_sexo'],
            data['fecha_nacimiento'], data['lugar_nacimiento'], data['id_estado_civil'],
            data['cantidad_hijos'], data['familiares_a_cargo'], data['domicilio'],
            data['piso'], data['localidad'], data['id_provincia'], data['id_pais'],
            data['codigo_postal'], data['telefono'], data['telefono_alt'],
            data['telefono_alt_propietario'], data['email'], data['titulo_base'],
            data['anio_egreso'], data['id_institucion'], data['otros_estudios'],
            data['anio_egreso_otros'], data['trabaja'], data['actividad'],
            data['horario_habitual'], data['obra_social']
        ))
        session.pop('pre_inscripcion_data', None)
        flash('Pre-inscripción confirmada con éxito.', 'success')
        return redirect(url_for('home'))
    except Exception as e:
        flash(f'Error al guardar pre-inscripción: {str(e)}', 'error')
        return redirect(url_for('pre_inscripcion_3'))

#una vez que esta completo el formulario, guardamos al ingresante en pre_inscripciones para mas adelante darlo de alta como alumno
@app.route('/guardar_pre_inscripcion', methods=['POST'])
def guardar_pre_inscripcion():
    # Obtener todos los datos desde la sesión
    datos = session.get('datos_completos', {})

    # Ajustar campos que pueden no estar presentes
    datos['lugar_nacimiento'] = datos.get('lugar_nacimiento') or None
    datos['telefono_alt'] = datos.get('telefono_alt') or None
    datos['telefono_alt_propietario'] = datos.get('telefono_alt_propietario') or None
    datos['titulo_base'] = datos.get('titulo_base') or None
    datos['anio_egreso_otros'] = datos.get('anio_egreso_otros') or None
    datos['piso'] = datos.get('piso') if datos.get('piso') != 'NULL' else None

    # Ajustar los campos relacionados con el trabajo
    trabaja = datos.get('trabaja')
    actividad = datos.get('actividad', '') if trabaja == 'si' else None
    horario_habitual = datos.get('horario_habitual', '') if trabaja == 'si' else None
    obra_social = datos.get('obra_social', '') if trabaja == 'si' else None

    # Usar los IDs originales para la inserción en inscripciones_carreras
    id_carrera = datos.get('id_carrera_original')
    id_turno = datos.get('id_turno_original')
    id_pais = datos.get('id_pais_original')
    id_provincia = datos.get('id_provincia_original')
    id_localidad = datos.get('id_localidad_original')
    id_institucion = datos.get('id_instituto_original')
    id_sexo = datos.get('id_sexo_original')
    id_estado_civil = datos.get('id_estado_civil_original')

    # Insertar el usuario en la tabla pre_inscripciones sin id_carrera ni id_turno
    query_usuario = """
        INSERT INTO pre_inscripciones (
            dni, nombre, apellido, id_sexo, fecha_nacimiento, lugar_nacimiento, id_estado_civil,
            cantidad_hijos, familiares_a_cargo, domicilio, piso, id_localidad, id_pais,
            id_provincia, codigo_postal, telefono, telefono_alt, telefono_alt_propietario, email,
            titulo_base, anio_egreso, id_institucion, otros_estudios, anio_egreso_otros,
            trabaja, actividad, horario_habitual, obra_social
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    ejecutar_sql(query_usuario, (
        datos['dni'], datos['nombre'], datos['apellido'], id_sexo,
        datos['fecha_nacimiento'], datos['lugar_nacimiento'], id_estado_civil,
        datos['cantidad_hijos'], datos['familiares_a_cargo'], datos['domicilio'],
        datos['piso'], id_localidad, id_pais,
        id_provincia, datos['codigo_postal'], datos['telefono'],
        datos['telefono_alt'], datos['telefono_alt_propietario'], datos['email'],
        datos['titulo_base'], datos['anio_egreso'], id_institucion,
        datos['otros_estudios'], datos['anio_egreso_otros'], trabaja,
        actividad, horario_habitual, obra_social
    ))

    # Recuperar id_usuario usando el DNI
    query_select_id = "SELECT id_usuario FROM pre_inscripciones WHERE dni = %s"
    id_usuario = ejecutar_sql(query_select_id, (datos['dni'],))[0][0]
    print (id_usuario)
    # Insertar en inscripciones_carreras con el id_usuario obtenido
    query_inscripcion = """
        INSERT INTO inscripciones_carreras (
            id_carrera, id_usuario, fecha_inscripcion, turno, estado_alumno, activo
        ) VALUES (%s, %s, NOW(), %s, 'pre_inscripto', 1)
    """
    ejecutar_sql(query_inscripcion, (id_carrera, id_usuario, id_turno))
    # Redirigir al home una vez completada la inscripción
    return redirect(url_for('home'))

#siguiendo con el formulario, aqui primero cargara todos los datos, generara algunas inteligencias para mostrar nombres en vez de
# ids y los mostrara en pantalla, si todo esta bien pasamos a guardar_pre_inscripcion
@app.route('/pre_inscripcion_3', methods=['POST'])
@perfil_requerido(['1', '2'])
def pre_inscripcion_3():
    if 'nombre' not in session:
        return redirect(url_for('login'))

    # Obtener los datos personales desde la sesión
    datos_personales = session.get('datos_personales', {})

    # Recibir los datos de estudios y laborales del formulario de pre_inscripcion_2
    datos_estudios_y_laborales = request.form.to_dict()

    # Combinar todos los datos
    datos_completos = {**datos_personales, **datos_estudios_y_laborales}

    # Guardar en la sesión
    session['datos_completos'] = datos_completos

    # Consultas SQL para obtener los nombres en lugar de IDs
    query_pais = "SELECT nombre FROM paises WHERE id_pais = %s"
    query_provincia = "SELECT nombre FROM provincias WHERE id_provincia = %s"
    query_localidad = "SELECT nombre FROM localidades WHERE id_localidad = %s"
    query_carrera = "SELECT nombre FROM lista_carreras WHERE id_carrera = %s"
    query_turno = "SELECT descripcion FROM turno_carrera WHERE id_turno = %s"
    query_instituto = "SELECT nombre_instituto FROM institutos WHERE id_instituto = %s"
    query_sexo = "SELECT descripcion FROM sexos WHERE id_sexo = %s"
    query_estado_civil = "SELECT nombre FROM estado_civil WHERE id_estado_civil = %s"

    # Mantener los IDs originales
    id_pais_original = datos_completos.get('id_pais')
    id_provincia_original = datos_completos.get('id_provincia')
    id_localidad_original = datos_completos.get('id_localidad')
    id_carrera_original = datos_completos.get('carrera')
    id_turno_original = datos_completos.get('turno')
    id_instituto_original = datos_completos.get('id_institucion')
    id_sexo_original = datos_completos.get('id_sexo')
    id_estado_civil_original = datos_completos.get('id_estado_civil')

    # Obtener los nombres basados en los IDs
    pais_nombre = ejecutar_sql(query_pais, (id_pais_original,))[0][0] if id_pais_original else None
    provincia_nombre = ejecutar_sql(query_provincia, (id_provincia_original,))[0][0] if id_provincia_original else None
    localidad_nombre = ejecutar_sql(query_localidad, (id_localidad_original,))[0][0] if id_localidad_original else None
    carrera_nombre = ejecutar_sql(query_carrera, (id_carrera_original,))[0][0] if id_carrera_original else None
    turno_descripcion = ejecutar_sql(query_turno, (id_turno_original,))[0][0] if id_turno_original else None
    instituto_nombre = ejecutar_sql(query_instituto, (id_instituto_original,))[0][0] if id_instituto_original else None
    sexo_nombre = ejecutar_sql(query_sexo, (id_sexo_original,))[0][0] if id_sexo_original else None
    estado_civil_nombre = ejecutar_sql(query_estado_civil, (id_estado_civil_original,))[0][0] if id_estado_civil_original else None

    # Guardar los valores originales junto con los nombres
    datos_completos['id_pais_original'] = id_pais_original
    datos_completos['id_provincia_original'] = id_provincia_original
    datos_completos['id_localidad_original'] = id_localidad_original
    datos_completos['id_carrera_original'] = id_carrera_original
    datos_completos['id_turno_original'] = id_turno_original
    datos_completos['id_instituto_original'] = id_instituto_original
    datos_completos['id_sexo_original'] = id_sexo_original
    datos_completos['id_estado_civil_original'] = id_sexo_original

    # Reemplazar los IDs por sus nombres para mostrar en la vista
    datos_completos['id_pais'] = pais_nombre
    datos_completos['id_provincia'] = provincia_nombre
    datos_completos['id_localidad'] = localidad_nombre
    datos_completos['carrera'] = carrera_nombre
    datos_completos['turno'] = turno_descripcion
    datos_completos['id_institucion'] = instituto_nombre
    datos_completos['id_sexo'] = sexo_nombre
    datos_completos['id_estado_civil'] = estado_civil_nombre

    return render_template('pre_inscripcion_3.html', **datos_completos)

#estas rutas hacen lo mismo que pre_inscripcion pero estas funcionan para el que hace el formulario de afuera, no vera la navbar
@app.route('/inscribite', methods=['GET', 'POST'])
def inscribite():

    # Obtener países, provincias, localidades, carreras y turnos
    query_paises = "SELECT id_pais, nombre FROM paises"
    paises = ejecutar_sql(query_paises)

    query_provincias = "SELECT id_provincia, nombre, id_pais FROM provincias"
    provincias = ejecutar_sql(query_provincias)

    query_localidades = "SELECT id_localidad, nombre, id_provincia FROM localidades"
    localidades = ejecutar_sql(query_localidades)

    # Incluir el ID de la institución en cada carrera
    query_carreras = """
        SELECT c.id_carrera, c.nombre, c.id_instituto
        FROM lista_carreras c
    """
    lista_carreras = ejecutar_sql(query_carreras)
    carreras_dict = [{"id_carrera": carrera[0], "nombre": carrera[1], "id_instituto": carrera[2]} for carrera in lista_carreras]

    query_turnos = """
        SELECT tc.id_carrera, tc.descripcion, tc.id_turno
        FROM turno_carrera tc
        WHERE tc.estado = 1
    """
    turnos_carreras = ejecutar_sql(query_turnos)
    turnos_carreras_dict = [{"id_carrera": turno[0], "descripcion": turno[1], "id_turno": turno[2]} for turno in turnos_carreras]

    # Consulta para obtener sexos
    query_sexo = "SELECT id_sexo, descripcion FROM sexos"
    sexos = ejecutar_sql(query_sexo)

    # Consulta para obtener institutos (mejorar comentario)
    query_institutos = "SELECT id_instituto, nombre_instituto FROM institutos"
    institutos = ejecutar_sql(query_institutos)  

    query_estados = "SELECT id_estado_civil, nombre FROM estado_civil"
    estado_civil = ejecutar_sql(query_estados)    

    if request.method == 'POST':
        # Recibir los datos desde el formulario
        datos_personales = request.form.to_dict()
        
        # Verificar si el DNI ya existe en la base de datos de usuarios
        dni = datos_personales.get('dni')
        query_verificar_dni = "SELECT COUNT(*) FROM usuarios WHERE dni = %s"
        existe_dni = ejecutar_sql(query_verificar_dni, (dni,))[0][0]

        if existe_dni > 0:
            return render_template(
                'inscribite.html',
                turnos_carreras=turnos_carreras_dict,
                lista_carreras=carreras_dict,
                paises=paises,
                provincias=provincias,
                localidades=localidades,
                error_dni=True,
                sexos=sexos,
                institutos=institutos,
                estado_civil=estado_civil,
                datos_personales=datos_personales  # Para mantener los datos ingresados
            )

        # Guardar los datos en la sesión y continuar a la siguiente página
        session['datos_personales'] = datos_personales
        return redirect(url_for('inscribite_2'))

    # Renderizar la página sin mensaje de error al cargar por primera vez (GET)
    return render_template(
        'inscribite.html',
        turnos_carreras=turnos_carreras_dict,
        lista_carreras=carreras_dict,
        paises=paises,
        provincias=provincias,
        localidades=localidades,
        error_dni=False,
        sexos=sexos,
        institutos=institutos,
        estado_civil=estado_civil
    )

#estas rutas hacen lo mismo que pre_inscripcion pero estas funcionan para el que hace el formulario de afuera, no vera la navbar
@app.route('/inscribite_2', methods=['GET', 'POST'])
def inscribite_2():

    if request.method == 'POST':
        # Recibir los datos del formulario anterior
        datos_personales = request.form.to_dict()

        # Guardar en la sesión para usarlos más adelante
        session['datos_personales'] = datos_personales

    # Obtener el país seleccionado previamente (Argentina o no)
    id_pais_estudio = int(session['datos_personales'].get('id_pais', 0))  # Valor por defecto 0 si no está en sesión

    # Consulta para obtener provincias
    query_provincias = "SELECT id_provincia, id_pais, nombre FROM provincias"
    provincias = ejecutar_sql(query_provincias)


    return render_template(
        'inscribite_2.html',
        id_pais_estudio=id_pais_estudio,
        provincias=provincias,
    )


#estas rutas hacen lo mismo que pre_inscripcion pero estas funcionan para el que hace el formulario de afuera, no vera la navbar
@app.route('/inscribite_3', methods=['POST'])
def inscribite_3():

    # Obtener los datos personales desde la sesión
    datos_personales = session.get('datos_personales', {})

    # Recibir los datos de estudios y laborales del formulario de pre_inscripcion_2
    datos_estudios_y_laborales = request.form.to_dict()

    # Combinar todos los datos
    datos_completos = {**datos_personales, **datos_estudios_y_laborales}

    # Guardar en la sesión
    session['datos_completos'] = datos_completos

    # Consultas SQL para obtener los nombres en lugar de IDs
    query_pais = "SELECT nombre FROM paises WHERE id_pais = %s"
    query_provincia = "SELECT nombre FROM provincias WHERE id_provincia = %s"
    query_localidad = "SELECT nombre FROM localidades WHERE id_localidad = %s"
    query_carrera = "SELECT nombre FROM lista_carreras WHERE id_carrera = %s"
    query_turno = "SELECT descripcion FROM turno_carrera WHERE id_turno = %s"
    query_instituto = "SELECT nombre_instituto FROM institutos WHERE id_instituto = %s"
    query_sexo = "SELECT descripcion FROM sexos WHERE id_sexo = %s"
    query_estado_civil = "SELECT nombre FROM estado_civil WHERE id_estado_civil = %s"

    # Mantener los IDs originales
    id_pais_original = datos_completos.get('id_pais')
    id_provincia_original = datos_completos.get('id_provincia')
    id_localidad_original = datos_completos.get('id_localidad')
    id_carrera_original = datos_completos.get('carrera')
    id_turno_original = datos_completos.get('turno')
    id_instituto_original = datos_completos.get('id_institucion')
    id_sexo_original = datos_completos.get('id_sexo')
    id_estado_civil_original = datos_completos.get('id_estado_civil')

    # Obtener los nombres basados en los IDs
    pais_nombre = ejecutar_sql(query_pais, (id_pais_original,))[0][0] if id_pais_original else None
    provincia_nombre = ejecutar_sql(query_provincia, (id_provincia_original,))[0][0] if id_provincia_original else None
    localidad_nombre = ejecutar_sql(query_localidad, (id_localidad_original,))[0][0] if id_localidad_original else None
    carrera_nombre = ejecutar_sql(query_carrera, (id_carrera_original,))[0][0] if id_carrera_original else None
    turno_descripcion = ejecutar_sql(query_turno, (id_turno_original,))[0][0] if id_turno_original else None
    instituto_nombre = ejecutar_sql(query_instituto, (id_instituto_original,))[0][0] if id_instituto_original else None
    sexo_nombre = ejecutar_sql(query_sexo, (id_sexo_original,))[0][0] if id_sexo_original else None
    estado_civil_nombre = ejecutar_sql(query_estado_civil, (id_estado_civil_original,))[0][0] if id_estado_civil_original else None

    # Guardar los valores originales junto con los nombres
    datos_completos['id_pais_original'] = id_pais_original
    datos_completos['id_provincia_original'] = id_provincia_original
    datos_completos['id_localidad_original'] = id_localidad_original
    datos_completos['id_carrera_original'] = id_carrera_original
    datos_completos['id_turno_original'] = id_turno_original
    datos_completos['id_instituto_original'] = id_instituto_original
    datos_completos['id_sexo_original'] = id_sexo_original
    datos_completos['id_estado_civil_original'] = id_sexo_original

    # Reemplazar los IDs por sus nombres para mostrar en la vista
    datos_completos['id_pais'] = pais_nombre
    datos_completos['id_provincia'] = provincia_nombre
    datos_completos['id_localidad'] = localidad_nombre
    datos_completos['carrera'] = carrera_nombre
    datos_completos['turno'] = turno_descripcion
    datos_completos['id_institucion'] = instituto_nombre
    datos_completos['id_sexo'] = sexo_nombre
    datos_completos['id_estado_civil'] = estado_civil_nombre

    return render_template('inscribite_3.html', **datos_completos)










###PROFESORES######PROFESORES######PROFESORES######PROFESORES######PROFESORES######PROFESORES######PROFESORES######PROFESORES######PROFESORES######PROFESORES######PROFESORES######PROFESORES###




#################PROFESORES    
@app.route('/profesores/profesores', methods=['GET'])
@perfil_requerido(['1', '2'])
def profesores():
    if 'id_usuario' not in session:
        flash('Error: Sesión no válida.', 'error')
        return redirect(url_for('login'))

    search = request.args.get('search', '')
    estado = request.args.get('estado', 'todos')
    page = int(request.args.get('page', 1))
    per_page = 10

    try:
        query = """
            SELECT p.dni_profesor, p.nombre, p.apellido, p.sexo, p.activo,
                   CASE 
                       WHEN p.activo = 0 THEN '-' 
                       ELSE COALESCE(GROUP_CONCAT(CONCAT(l.licencia, ' (', l.desde, ' - ', COALESCE(l.hasta, 'Indefinido'), ')') ORDER BY l.desde SEPARATOR ', '), 'Sin licencias')
                   END as licencias
            FROM profesores p
            LEFT JOIN licencias l ON p.dni_profesor = l.dni_profesor
            WHERE 1=1
        """
        params = []
        if search:
            query += " AND (p.dni_profesor LIKE %s OR p.nombre LIKE %s OR p.apellido LIKE %s)"
            params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
        if estado == 'activo':
            query += " AND p.activo = 1"
        elif estado == 'cesado':
            query += " AND p.activo = 0"
        query += " GROUP BY p.dni_profesor, p.nombre, p.apellido, p.sexo, p.activo"
        query += " ORDER BY p.nombre, p.apellido"
        query += " LIMIT %s OFFSET %s"
        params.extend([per_page, (page - 1) * per_page])

        profesores = ejecutar_sql(query, tuple(params))
        if profesores is None:
            raise Exception("Query returned None for profesores")

        count_query = "SELECT COUNT(*) FROM profesores WHERE 1=1"
        count_params = []
        if search:
            count_query += " AND (dni_profesor LIKE %s OR nombre LIKE %s OR apellido LIKE %s)"
            count_params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
        if estado == 'activo':
            count_query += " AND activo = 1"
        elif estado == 'cesado':
            count_query += " AND activo = 0"
        total = ejecutar_sql(count_query, tuple(count_params))[0][0]
        total_paginas = (total + per_page - 1) // per_page

        profesores = [(p[0], p[1], p[2], p[3], p[4], p[5]) for p in profesores]
    except Exception as e:
        print(f"Error fetching profesores: {str(e)}")
        flash('Error al cargar profesores', 'danger')
        profesores = []
        total_paginas = 0

    return render_template('profesores/profesores.html', profesores=profesores,
                          total_paginas=total_paginas, pagina_actual=page, search=search, estado=estado)

#################PROFESORES DETALLE
@app.route('/profesores/detalle/<int:dni_profesor>', methods=['GET'])
@perfil_requerido(['1', '2'])
def detalle_profesor(dni_profesor):
    if 'id_usuario' not in session:
        flash('Error: Sesión no válida.', 'error')
        return redirect(url_for('login'))

    try:
        # === FETCH PROFESOR ===
        query_profesor = """
            SELECT id_profesor, dni_profesor, nombre, apellido, email, fecha_nacimiento,
                   lugar_nacimiento, pais, foja, n_registro, certificado_aptitud_fisica,
                   telefono, celular, piso, dpto, codigo_postal, partido, sexo, activo,
                   localidad, domicilio
            FROM profesores
            WHERE dni_profesor = %s
        """
        result = ejecutar_sql(query_profesor, (dni_profesor,))
        if not result:
            flash('Profesor no encontrado.', 'error')
            return redirect(url_for('profesores'))

        profesor = {
            'id_profesor': result[0][0],
            'dni_profesor': result[0][1],
            'nombre': result[0][2],
            'apellido': result[0][3],
            'email': result[0][4],
            'fecha_nacimiento': result[0][5],
            'lugar_nacimiento': result[0][6],
            'pais': result[0][7],
            'foja': result[0][8],
            'n_registro': result[0][9],
            'certificado_aptitud_fisica': result[0][10],
            'telefono': result[0][11],
            'celular': result[0][12],
            'piso': result[0][13],
            'dpto': result[0][14],
            'codigo_postal': result[0][15],
            'partido': result[0][16],
            'sexo': result[0][17],
            'activo': result[0][18],
            'localidad': result[0][19],
            'domicilio': result[0][20]
        }

        # === FETCH TÍTULOS ===
        query_titulos = """
            SELECT id_titulo, titulo, expedido_por, duracion, finalizo, fecha_egreso, porcentaje_carrera
            FROM titulos_profesores
            WHERE dni_profesor = %s
            ORDER BY id_titulo DESC
        """
        results_titulos = ejecutar_sql(query_titulos, (dni_profesor,))
        titulos = []
        for row in results_titulos or []:
            titulo = {
                'id_titulo': row[0],
                'titulo': row[1],
                'expedido_por': row[2],
                'duracion': row[3],
                'finalizo': row[4],
                'fecha_egreso': row[5],
                'porcentaje_carrera': row[6]
            }
            titulos.append(titulo)

    except Exception as e:
        print(f"Error fetching profesor details: {str(e)}")
        flash('Error al cargar detalles del profesor', 'danger')
        return redirect(url_for('profesores'))

    return render_template('profesores/detalle_profesor.html', profesor=profesor, titulos=titulos)

#################ALTA DE PROFESORES
@app.route('/alta_profesores', methods=['GET', 'POST'])
@perfil_requerido(['1', '2'])
def alta_profesores():
    if 'id_usuario' not in session:
        flash('Error: Sesión no válida.', 'error')
        return redirect(url_for('login'))

    try:
        sexos = ejecutar_sql("SELECT descripcion FROM sexos ORDER BY descripcion") or []
        sexos = [{'descripcion': s[0]} for s in sexos]

        paises = ejecutar_sql("SELECT id_pais, nombre FROM paises ORDER BY nombre") or []
        paises = [{'id_pais': p[0], 'nombre': p[1]} for p in paises]
    except Exception as e:
        print(f"Error fetching sexos: {str(e)}")
        flash('Error al cargar datos', 'danger')
        return render_template('profesores/alta_de_profesores.html', sexos=[], paises=[])

    if request.method == 'POST':
        try:
            dni_profesor = request.form.get('dni_profesor')
            nombre = request.form.get('nombre')
            apellido = request.form.get('apellido')
            sexo = request.form.get('sexo')
            email = request.form.get('email') or None
            fecha_nacimiento = request.form.get('fecha_nacimiento') or None
            lugar_nacimiento = request.form.get('lugar_nacimiento') or None
            domicilio = request.form.get('domicilio') or None
            pais = request.form.get('pais') or None
            foja = request.form.get('foja') or None
            n_registro = request.form.get('n_registro') or None
            certificado_aptitud_fisica = 1 if request.form.get('certificado_aptitud_fisica') else 0
            telefono = ''.join(filter(str.isdigit, request.form.get('telefono') or '')) or None
            celular = request.form.get('celular') or None
            localidad = request.form.get('localidad') or None
            partido = request.form.get('partido') or None
            piso = request.form.get('piso') or None
            dpto = request.form.get('dpto') or None
            codigo_postal = request.form.get('codigo_postal') or None
            titulos = request.form.getlist('titulo[]')
            expedidos_por = request.form.getlist('expedido_por[]')
            duraciones = request.form.getlist('duracion[]')
            finalizos = request.form.getlist('finalizo[]')
            fechas_egreso = request.form.getlist('fecha_egreso[]')
            porcentajes_carrera = request.form.getlist('porcentaje_carrera[]')

            # Validate required fields
            if not all([dni_profesor, nombre, apellido, sexo]):
                flash('Los campos obligatorios deben completarse.', 'error')
                return render_template('profesores/alta_de_profesores.html', sexos=sexos, paises=paises)

            # Validate DNI
            try:
                dni_profesor = int(dni_profesor)
                if not (1000000 <= dni_profesor <= 99999999):
                    flash('DNI debe tener entre 7 y 8 dígitos.', 'error')
                    return render_template('profesores/alta_de_profesores.html', sexos=sexos, paises=paises)
            except ValueError:
                flash('DNI debe ser un número válido.', 'error')
                return render_template('profesores/alta_de_profesores.html', sexos=sexos, paises=paises)

            # Check DNI uniqueness
            query = "SELECT COUNT(*) FROM profesores WHERE dni_profesor = %s"
            result = ejecutar_sql(query, (dni_profesor,))
            if result is None or result[0][0] > 0:
                flash('DNI ya registrado.', 'error')
                return render_template('profesores/alta_de_profesores.html', sexos=sexos, paises=paises)

            # Check foja uniqueness
            if foja:
                query = "SELECT COUNT(*) FROM profesores WHERE foja = %s"
                result = ejecutar_sql(query, (foja,))
                if result is None or result[0][0] > 0:
                    flash('Foja ya registrada.', 'error')
                    return render_template('profesores/alta_de_profesores.html', sexos=sexos, paises=paises)

            # Check n_registro uniqueness
            if n_registro:
                query = "SELECT COUNT(*) FROM profesores WHERE n_registro = %s"
                result = ejecutar_sql(query, (n_registro,))
                if result is None or result[0][0] > 0:
                    flash('Número de registro ya registrado.', 'error')
                    return render_template('profesores/alta_de_profesores.html', sexos=sexos, paises=paises)

            # Validate fecha_nacimiento
            if fecha_nacimiento:
                try:
                    datetime.strptime(fecha_nacimiento, '%Y-%m-%d')
                except ValueError:
                    flash('Fecha de nacimiento inválida.', 'error')
                    return render_template('profesores/alta_de_profesores.html', sexos=sexos, paises=paises)

            # Insert professor
            query = """
                INSERT INTO profesores (
                    dni_profesor, nombre, apellido, sexo, email, fecha_nacimiento, lugar_nacimiento, domicilio,
                    pais, foja, n_registro, certificado_aptitud_fisica, telefono, celular,
                    localidad, partido, piso, dpto, codigo_postal, activo
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            params = (
                dni_profesor, nombre, apellido, sexo, email, fecha_nacimiento, lugar_nacimiento, domicilio,
                pais, foja, n_registro, certificado_aptitud_fisica, telefono, celular,
                localidad, partido, piso, dpto, codigo_postal, 0
            )
            ejecutar_sql(query, params)

            # Insert titulos
            id_profesor = ejecutar_sql("SELECT LAST_INSERT_ID()")[0][0]
            for i in range(len(titulos)):
                if titulos[i]:
                    finalizo = 1 if finalizos[i] else 0
                    duracion = int(duraciones[i]) if duraciones[i] else None
                    porcentaje = int(porcentajes_carrera[i]) if porcentajes_carrera[i] else None
                    fecha_egreso = fechas_egreso[i] or None
                    if fecha_egreso:
                        try:
                            datetime.strptime(fecha_egreso, '%Y-%m-%d')
                        except ValueError:
                            flash(f'Fecha de egreso inválida para el título {titulos[i]}.', 'error')
                            return render_template('profesores/alta_de_profesores.html', sexos=sexos, paises=paises)
                    query = """
                        INSERT INTO titulos_profesores (
                            dni_profesor, titulo, expedido_por, duracion, finalizo, fecha_egreso,
                            porcentaje_carrera
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """
                    ejecutar_sql(query, (
                        dni_profesor, titulos[i], expedidos_por[i] or None, duracion,
                        finalizo, fecha_egreso, porcentaje
                    ))

            flash('Profesor registrado con éxito.', 'success')
            return redirect(url_for('profesores'))
        except Exception as e:
            print(f"Error registering professor: {str(e)}")
            flash(f'Error al registrar profesor: {str(e)}', 'error')
            return render_template('profesores/alta_de_profesores.html', sexos=sexos, paises=paises)

    return render_template('profesores/alta_de_profesores.html', sexos=sexos, paises=paises)



#################CESAR PROFESOR
@app.route('/cesar_profesor', methods=['GET', 'POST'])
@perfil_requerido(['1', '2'])
def cesar_profesor():
    if 'id_usuario' not in session:
        flash('Error: Sesión no válida.', 'error')
        return redirect(url_for('login'))

    # Fetch profesores, carreras, and materias
    try:
        profesores = ejecutar_sql("SELECT dni_profesor, nombre, apellido FROM profesores WHERE activo = 1 ORDER BY nombre, apellido")
        if profesores is None:
            raise Exception("Query returned None for profesores")
        profesores = [(p[0], p[1], p[2]) for p in profesores]

        carreras = ejecutar_sql("SELECT id_carrera, nombre FROM lista_carreras WHERE activo = 1 ORDER BY nombre")
        if carreras is None:
            raise Exception("Query returned None for carreras")
        carreras = [(c[0], '', '', c[1]) for c in carreras]  # Match carrera[3] in template

        materias = ejecutar_sql("SELECT id_materia, nombre, id_carrera FROM materias ORDER BY nombre")
        if materias is None:
            raise Exception("Query returned None for materias")
        materias = [(m[0], m[1], m[2]) for m in materias]

        # Fetch assigned per professor per career (active toma_posesion)
        assigned_query = "SELECT dni_profesor, id_carrera, id_materia FROM toma_posesion WHERE activo = 1"
        assigned_results = ejecutar_sql(assigned_query)
        if assigned_results is None:
            raise Exception("Query returned None for assigned")
        assigned = {}
        for row in assigned_results:
            prof = row[0]
            career = row[1]
            matter = row[2]
            if prof not in assigned:
                assigned[prof] = {}
            if career not in assigned[prof]:
                assigned[prof][career] = []
            assigned[prof][career].append(matter)
    except Exception as e:
        print(f"Error fetching data: {str(e)}")
        flash('Error al cargar datos', 'danger')
        return render_template('profesores/cesar_profesor.html', profesores=[], carreras=[], materias=[], assigned={})

    if request.method == 'POST':
        try:
            dni_profesor = request.form.get('dni_profesor')
            fecha = request.form.get('fecha')
            id_carrera = request.form.get('id_carrera')
            id_materia = request.form.get('id_materia')
            anio = request.form.get('anio') or None
            hs_modulos = request.form.get('hs_modulos') or None
            motivo = request.form.get('motivo')
            observaciones = request.form.get('observaciones') or None

            # Validate required fields
            if not all([dni_profesor, fecha, id_carrera, id_materia, motivo, hs_modulos]):
                flash('Los campos obligatorios deben completarse.', 'error')
                return render_template('profesores/cesar_profesor.html', profesores=profesores,
                                      carreras=carreras, materias=materias, assigned=assigned)

            # Validate fecha
            try:
                datetime.strptime(fecha, '%Y-%m-%d')
            except ValueError:
                flash('Fecha inválida.', 'error')
                return render_template('profesores/cesar_profesor.html', profesores=profesores,
                                      carreras=carreras, materias=materias, assigned=assigned)

            # Validate motivo
            if motivo not in ['Jubilación', 'Renuncia', 'Fallecimiento', 'Otros']:
                flash('Motivo inválido.', 'error')
                return render_template('profesores/cesar_profesor.html', profesores=profesores,
                                      carreras=carreras, materias=materias, assigned=assigned)

            # Validate anio
            if anio and anio not in ['1°', '2°', '3°', '4°']:
                flash('Año inválido.', 'error')
                return render_template('profesores/cesar_profesor.html', profesores=profesores,
                                      carreras=carreras, materias=materias, assigned=assigned)

            # Validate hs_modulos
            try:
                hs_modulos = int(hs_modulos)
                if hs_modulos < 0:
                    flash('Módulos deben ser no negativos.', 'error')
                    return render_template('profesores/cesar_profesor.html', profesores=profesores,
                                          carreras=carreras, materias=materias, assigned=assigned)
            except ValueError:
                flash('Módulos deben ser un número válido.', 'error')
                return render_template('profesores/cesar_profesor.html', profesores=profesores,
                                      carreras=carreras, materias=materias, assigned=assigned)

            # Check if toma_posesion exists and is active
            query = "SELECT COUNT(*) FROM toma_posesion WHERE dni_profesor = %s AND id_carrera = %s AND id_materia = %s AND activo = 1"
            result = ejecutar_sql(query, (dni_profesor, id_carrera, id_materia))
            if result is None or result[0][0] == 0:
                flash('No existe una toma de posesión activa para esta materia y profesor.', 'error')
                return render_template('profesores/cesar_profesor.html', profesores=profesores,
                                      carreras=carreras, materias=materias, assigned=assigned)

            # Insert into ceses
            query = """
                INSERT INTO ceses (dni_profesor, fecha, id_carrera, id_materia, anio, hs_modulos, motivo, observaciones)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            ejecutar_sql(query, (dni_profesor, fecha, id_carrera, id_materia, anio, hs_modulos, motivo, observaciones))

            # Deactivate the toma_posesion
            update_query = """
                UPDATE toma_posesion
                SET activo = 0
                WHERE dni_profesor = %s AND id_carrera = %s AND id_materia = %s AND activo = 1
            """
            ejecutar_sql(update_query, (dni_profesor, id_carrera, id_materia))

            # Check if professor has other active toma_posesion records
            query = "SELECT COUNT(*) FROM toma_posesion WHERE dni_profesor = %s AND activo = 1"
            result = ejecutar_sql(query, (dni_profesor,))
            if result is None or result[0][0] == 0:
                # No active toma_posesion records, set profesor activo = 0
                query = "UPDATE profesores SET activo = 0 WHERE dni_profesor = %s"
                ejecutar_sql(query, (dni_profesor,))

            flash('Profesor cesado con éxito.', 'success')
            return redirect(url_for('profesores'))
        except Exception as e:
            print(f"Error cesing professor: {str(e)}")
            flash(f'Error al cesar profesor: {str(e)}', 'error')
            return render_template('profesores/cesar_profesor.html', profesores=profesores,
                                  carreras=carreras, materias=materias, assigned=assigned)

    return render_template('profesores/cesar_profesor.html', profesores=profesores,
                          carreras=carreras, materias=materias, assigned=assigned)

#################AGREGAR INASISTENCIA
@app.route('/agregar_inasistencia', methods=['GET', 'POST'])
@perfil_requerido(['1', '2'])
def agregar_inasistencia():
    if 'id_usuario' not in session:
        flash('Error: Sesión no válida.', 'error')
        return redirect(url_for('login'))

    # Fetch profesores, carreras, and materias
    try:
        profesores = ejecutar_sql("SELECT dni_profesor, nombre, apellido FROM profesores ORDER BY nombre, apellido")
        if profesores is None:
            raise Exception("Query returned None for profesores")
        profesores = [(p[0], p[1], p[2]) for p in profesores]

        carreras = ejecutar_sql("SELECT id_carrera, nombre FROM lista_carreras ORDER BY nombre")
        if carreras is None:
            raise Exception("Query returned None for carreras")
        carreras = [(c[0], '', '', c[1]) for c in carreras]  # Match carrera[3] in template

        materias = ejecutar_sql("SELECT id_materia, nombre, id_carrera FROM materias ORDER BY nombre")
        if materias is None:
            raise Exception("Query returned None for materias")
        materias = [(m[0], m[1], m[2]) for m in materias]
    except Exception as e:
        print(f"Error fetching data: {str(e)}")
        flash('Error al cargar datos', 'danger')
        return render_template('profesores/agregar_inasistencia.html', profesores=[], carreras=[], materias=[])

    if request.method == 'POST':
        try:
            dni_profesor = request.form.get('dni_profesor')
            id_carrera = request.form.get('id_carrera')
            id_materia = request.form.get('id_materia')
            fecha = request.form.get('fecha')
            motivo = request.form.get('motivo') or None
            presente = request.form.get('presente')
            observaciones = request.form.get('observaciones') or None

            # Validate required fields
            if not all([dni_profesor, id_carrera, id_materia, fecha, presente]):
                flash('Los campos obligatorios deben completarse.', 'error')
                return render_template('profesores/agregar_inasistencia.html', profesores=profesores,
                                      carreras=carreras, materias=materias)

            # Validate fecha
            try:
                datetime.strptime(fecha, '%Y-%m-%d')
            except ValueError:
                flash('Fecha inválida.', 'error')
                return render_template('profesores/agregar_inasistencia.html', profesores=profesores,
                                      carreras=carreras, materias=materias)

            # Validate presente
            if presente not in ['Presente', 'Ausente']:
                flash('El valor de presente debe ser "Presente" o "Ausente".', 'error')
                return render_template('profesores/agregar_inasistencia.html', profesores=profesores,
                                      carreras=carreras, materias=materias)

            # Insert into inasistencias
            query = """
                INSERT INTO inasistencias (dni_profesor, id_carrera, id_materia, fecha, motivo, presente, observaciones)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            ejecutar_sql(query, (dni_profesor, id_carrera, id_materia, fecha, motivo, presente, observaciones))

            flash('Inasistencia agregada con éxito.', 'success')
            return redirect(url_for('profesores'))
        except Exception as e:
            print(f"Error adding inasistencia: {str(e)}")
            flash(f'Error al agregar inasistencia: {str(e)}', 'error')
            return render_template('profesores/agregar_inasistencia.html', profesores=profesores,
                                  carreras=carreras, materias=materias)

    return render_template('profesores/agregar_inasistencia.html', profesores=profesores,
                          carreras=carreras, materias=materias)

#################AGREGAR LICENCIA
@app.route('/profesores/agregar_licencia', methods=['GET', 'POST'])
@perfil_requerido(['1', '2'])
def agregar_licencia():
    if 'id_usuario' not in session:
        flash('Error: Sesión no válida.', 'error')
        return redirect(url_for('login'))

    if request.method == 'GET':
        # Fetch data for dropdowns
        profesores_query = """
            SELECT dni_profesor, nombre, apellido
            FROM profesores
            WHERE activo = 1
            ORDER BY apellido, nombre
        """
        carreras_query = """
            SELECT id_carrera, id_instituto, id_turno, nombre
            FROM lista_carreras
            WHERE activo = 1
            ORDER BY nombre
        """
        materias_query = """
            SELECT id_materia, nombre, id_carrera
            FROM materias
            ORDER BY nombre
        """
        profesores = ejecutar_sql(profesores_query) or []
        carreras = ejecutar_sql(carreras_query) or []
        materias = ejecutar_sql(materias_query) or []

        return render_template(
            'profesores/agregar_licencia.html',
            profesores=profesores,
            carreras=carreras,
            materias=materias
        )

    # POST: Save licencia
    try:
        dni_profesor = request.form.get('dni_profesor')
        id_carrera = request.form.get('id_carrera')
        id_materia = request.form.get('id_materia')
        licencia = request.form.get('licencia')
        tiempo_estimado = request.form.get('tiempo_estimado')
        desde = request.form.get('desde')
        hasta = request.form.get('hasta') or None
        observaciones = request.form.get('observaciones') or None

        # Validate inputs
        if not all([dni_profesor, id_carrera, id_materia, licencia, tiempo_estimado, desde]):
            flash('Todos los campos obligatorios deben completarse.', 'error')
            return redirect(url_for('agregar_licencia'))

        # Validate hasta is provided unless tiempo_estimado is Difícil cobertura
        if tiempo_estimado != 'Difícil cobertura' and not hasta:
            flash('La fecha "hasta" es obligatoria a menos que se seleccione "Difícil cobertura".', 'error')
            return redirect(url_for('agregar_licencia'))

        # Validate desde <= hasta if hasta is provided
        if hasta and desde > hasta:
            flash('La fecha "desde" debe ser menor o igual a la fecha "hasta".', 'error')
            return redirect(url_for('agregar_licencia'))

        query = """
            INSERT INTO licencias (dni_profesor, id_carrera, id_materia, licencia, tiempo_estimado, desde, hasta, observaciones)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        ejecutar_sql(query, (
            dni_profesor, id_carrera, id_materia, licencia, tiempo_estimado, desde, hasta, observaciones
        ))

        flash('Licencia registrada con éxito.', 'success')
    except Exception as e:
        flash(f'Error al registrar licencia: {str(e)}', 'error')
    return redirect(url_for('profesores'))

#################AGREGAR TOMA DE POSESION
@app.route('/agregar_toma_posesion', methods=['GET', 'POST'])
@perfil_requerido(['1', '2'])
def agregar_toma_posesion():
    if 'id_usuario' not in session:
        flash('Error: Sesión no válida.', 'error')
        return redirect(url_for('login'))

    # Fetch profesores, carreras, and materias
    try:
        # Fetch all professors, including activo = 0, with activo status
        profesores = ejecutar_sql("SELECT dni_profesor, nombre, apellido, activo FROM profesores ORDER BY nombre, apellido")
        if profesores is None:
            raise Exception("Query returned None for profesores")
        profesores = [(p[0], p[1], p[2], p[3]) for p in profesores]

        carreras = ejecutar_sql("SELECT id_carrera, nombre FROM lista_carreras WHERE activo = 1 ORDER BY nombre")
        if carreras is None:
            raise Exception("Query returned None for carreras")
        carreras = [(c[0], '', '', c[1]) for c in carreras]  # Match carrera[3] in template

        materias = ejecutar_sql("SELECT id_materia, nombre, id_carrera FROM materias ORDER BY nombre")
        if materias is None:
            raise Exception("Query returned None for materias")
        materias = [(m[0], m[1], m[2]) for m in materias]

        # Fetch assigned id_materia per id_carrera (active toma_posesion)
        assigned_query = "SELECT id_carrera, id_materia FROM toma_posesion WHERE activo = 1"
        assigned_results = ejecutar_sql(assigned_query)
        if assigned_results is None:
            raise Exception("Query returned None for assigned")
        assigned = {}
        for row in assigned_results:
            career = row[0]
            matter = row[1]
            if career not in assigned:
                assigned[career] = []
            assigned[career].append(matter)
    except Exception as e:
        print(f"Error fetching data: {str(e)}")
        flash('Error al cargar datos', 'danger')
        return render_template('profesores/agregar_toma_posesion.html', profesores=[], carreras=[], materias=[], assigned={})

    if request.method == 'POST':
        try:
            dni_profesor = request.form.get('dni_profesor')
            fecha = request.form.get('fecha')
            id_carrera = request.form.get('id_carrera')
            id_materia = request.form.get('id_materia')
            modulos = request.form.get('modulos')
            observaciones = request.form.get('observaciones') or None
            situacion_revista = request.form['situacion_revista']
            if situacion_revista == '':
                situacion_revista = None

            # Validate required fields
            if not all([dni_profesor, fecha, id_carrera, id_materia, modulos]):
                flash('Los campos obligatorios deben completarse.', 'error')
                return render_template('profesores/agregar_toma_posesion.html', profesores=profesores,
                                      carreras=carreras, materias=materias, assigned=assigned)

            # Validate fecha
            try:
                datetime.strptime(fecha, '%Y-%m-%d')
            except ValueError:
                flash('Fecha inválida.', 'error')
                return render_template('profesores/agregar_toma_posesion.html', profesores=profesores,
                                      carreras=carreras, materias=materias, assigned=assigned)

            # Validate modulos
            try:
                modulos = int(modulos)
                if modulos < 0:
                    flash('Los módulos deben ser un número no negativo.', 'error')
                    return render_template('profesores/agregar_toma_posesion.html', profesores=profesores,
                                          carreras=carreras, materias=materias, assigned=assigned)
            except ValueError:
                flash('Los módulos deben ser un número válido.', 'error')
                return render_template('profesores/agregar_toma_posesion.html', profesores=profesores,
                                      carreras=carreras, materias=materias, assigned=assigned)

            # Check if materia is already assigned
            query = "SELECT COUNT(*) FROM toma_posesion WHERE id_carrera = %s AND id_materia = %s AND activo = 1"
            result = ejecutar_sql(query, (id_carrera, id_materia))
            if result is None or result[0][0] > 0:
                flash('La materia ya está asignada en esta carrera.', 'error')
                return render_template('profesores/agregar_toma_posesion.html', profesores=profesores,
                                      carreras=carreras, materias=materias, assigned=assigned)

            # Insert into toma_posesion
            query = """
                INSERT INTO toma_posesion (dni_profesor, fecha, id_carrera, id_materia, modulos, observaciones, activo)
                VALUES (%s, %s, %s, %s, %s, %s, 1)
            """
            ejecutar_sql(query, (dni_profesor, fecha, id_carrera, id_materia, modulos, observaciones))

            # Ensure professor is active
            query = "UPDATE profesores SET activo = 1 WHERE dni_profesor = %s"
            ejecutar_sql(query, (dni_profesor,))

            flash('Toma de posesión agregada con éxito.', 'success')
            return redirect(url_for('profesores'))
        except Exception as e:
            print(f"Error adding toma_posesion: {str(e)}")
            flash(f'Error al agregar toma de posesión: {str(e)}', 'error')
            return render_template('profesores/agregar_toma_posesion.html', profesores=profesores,
                                  carreras=carreras, materias=materias, assigned=assigned)

    return render_template('profesores/agregar_toma_posesion.html', profesores=profesores,
                          carreras=carreras, materias=materias, assigned=assigned)

#################EDITAR PROFESOR
@app.route('/profesores/editar_profesor/<int:dni_profesor>', methods=['GET', 'POST'])
@perfil_requerido(['1', '2'])
def editar_profesor(dni_profesor):
    if 'id_usuario' not in session:
        flash('Error: Sesión no válida.', 'error')
        return redirect(url_for('login'))

    if request.method == 'GET':
        # Fetch profesor data
        profesor_query = """
            SELECT 
                id_profesor, dni_profesor, nombre, apellido, email, fecha_nacimiento, 
                lugar_nacimiento, pais, foja, n_registro, certificado_aptitud_fisica, 
                telefono, celular, piso, dpto, codigo_postal, partido, sexo, activo, 
                domicilio, localidad
            FROM profesores
            WHERE dni_profesor = %s
        """
        results = ejecutar_sql(profesor_query, (dni_profesor,))
        if not results:
            flash('Profesor no encontrado.', 'error')
            return redirect(url_for('profesores'))

        # Convert to dictionary
        result = results[0]
        profesor = {
            'id_profesor': result[0],
            'dni_profesor': result[1],
            'nombre': result[2],
            'apellido': result[3],
            'email': result[4],
            'fecha_nacimiento': result[5],
            'lugar_nacimiento': result[6],
            'pais': result[7],
            'foja': result[8],
            'n_registro': result[9],
            'certificado_aptitud_fisica': result[10],
            'telefono': result[11],
            'celular': result[12],
            'piso': result[13],
            'dpto': result[14],
            'codigo_postal': result[15],
            'partido': result[16],
            'sexo': result[17],
            'activo': result[18],
            'domicilio': result[19],
            'localidad': result[20]
        }

        # Fetch distinct sexo values
        sexo_query = """
            SELECT DISTINCT sexo
            FROM profesores
            WHERE sexo IS NOT NULL
            ORDER BY sexo
        """
        sexos = [row[0] for row in ejecutar_sql(sexo_query) or []]

        # Fetch titulos_profesores data
        titulos_query = """
            SELECT id_titulo, dni_profesor, titulo, expedido_por, duracion, 
                   finalizo, fecha_egreso, porcentaje_carrera
            FROM titulos_profesores
            WHERE dni_profesor = %s
        """
        results = ejecutar_sql(titulos_query, (dni_profesor,)) or []
        titulos = [
            {
                'id_titulo': row[0],
                'dni_profesor': row[1],
                'titulo': row[2],
                'expedido_por': row[3],
                'duracion': row[4],
                'finalizo': row[5],
                'fecha_egreso': row[6],
                'porcentaje_carrera': row[7]
            } for row in results
        ]

        return render_template(
            'profesores/editar_profesor.html',
            profesor=profesor,
            sexos=sexos,
            titulos=titulos
        )

    # POST: Update profesor
    try:
        nombre = request.form.get('nombre')
        apellido = request.form.get('apellido')
        sexo = request.form.get('sexo')
        fecha_nacimiento = request.form.get('fecha_nacimiento') or None
        lugar_nacimiento = request.form.get('lugar_nacimiento') or None
        pais = request.form.get('pais') or None
        domicilio = request.form.get('domicilio') or None
        piso = request.form.get('piso') or None
        dpto = request.form.get('dpto') or None
        localidad = request.form.get('localidad') or None
        partido = request.form.get('partido') or None
        codigo_postal = request.form.get('codigo_postal') or None
        telefono = request.form.get('telefono') or None
        celular = request.form.get('celular') or None
        email = request.form.get('email') or None
        foja = request.form.get('foja') or None
        n_registro = request.form.get('n_registro') or None

        # Validate required fields
        if not all([nombre, sexo]):
            flash('Los campos obligatorios (Nombre, Sexo) deben completarse.', 'error')
            return redirect(url_for('editar_profesor', dni_profesor=dni_profesor))

        query = """
            UPDATE profesores
            SET nombre = %s, apellido = %s, sexo = %s, fecha_nacimiento = %s, 
                lugar_nacimiento = %s, pais = %s, domicilio = %s, piso = %s, 
                dpto = %s, localidad = %s, partido = %s, codigo_postal = %s, 
                telefono = %s, celular = %s, email = %s, foja = %s, n_registro = %s
            WHERE dni_profesor = %s
        """
        ejecutar_sql(query, (
            nombre, apellido, sexo, fecha_nacimiento, lugar_nacimiento, pais,
            domicilio, piso, dpto, localidad, partido, codigo_postal, telefono,
            celular, email, foja, n_registro, dni_profesor
        ))

        flash('Profesor actualizado con éxito.', 'success')
        return redirect(url_for('profesores'))
    except Exception as e:
        flash(f'Error al actualizar profesor: {str(e)}', 'error')
        return redirect(url_for('editar_profesor', dni_profesor=dni_profesor))

#################AGREGAR SUPLENCIA
@app.route('/profesores/agregar_suplencia', methods=['GET', 'POST'])
@perfil_requerido(['1', '2'])
def agregar_suplencia():
    # === DATOS COMUNES ===
    profesores = ejecutar_sql("SELECT dni_profesor, nombre, apellido FROM profesores ORDER BY apellido, nombre")
    carreras = ejecutar_sql("SELECT id_carrera, nombre FROM lista_carreras ORDER BY nombre")
    materias = ejecutar_sql("SELECT id_materia, nombre, id_carrera FROM materias ORDER BY nombre")

    if request.method == 'GET':
        return render_template(
            'profesores/agregar_suplencia.html',
            profesores=profesores,
            carreras=carreras,
            materias=materias
        )

    elif request.method == 'POST':
        # === OBTENER DATOS DEL FORMULARIO ===
        dni_profesor = request.form.get('dni_profesor')
        dni_suplente = request.form.get('dni_suplente') or None
        fecha = request.form.get('fecha')
        id_carrera = request.form.get('id_carrera')
        id_materia = request.form.get('id_materia')
        modulos = request.form.get('modulos')
        fecha_desde = request.form.get('fecha_desde')
        fecha_hasta = request.form.get('fecha_hasta')
        observaciones = request.form.get('observaciones', '').strip()

        # === VALIDACIONES ===
        errores = []

        # 1. Campos obligatorios
        if not all([dni_profesor, fecha, id_carrera, id_materia, modulos, fecha_desde, fecha_hasta]):
            errores.append('Todos los campos obligatorios deben estar completos.')

        # 2. Módulos > 0
        try:
            modulos = int(modulos)
            if modulos <= 0:
                errores.append('La cantidad de módulos debe ser mayor a 0.')
        except:
            errores.append('Módulos debe ser un número válido.')

        # 3. Fechas: desde <= hasta
        if fecha_desde and fecha_hasta:
            if fecha_desde > fecha_hasta:
                errores.append('La fecha "Desde" no puede ser posterior a "Hasta".')

        # 4. Suplente ≠ Titular
        if dni_suplente and dni_suplente == dni_profesor:
            errores.append('El suplente no puede ser el mismo que el profesor titular.')

        # === SI HAY ERRORES: VOLVER AL FORMULARIO ===
        if errores:
            for error in errores:
                flash(error, 'danger')
            return render_template(
                'profesores/agregar_suplencia.html',
                profesores=profesores,
                carreras=carreras,
                materias=materias,
                form_data={
                    'dni_profesor': dni_profesor,
                    'dni_suplente': dni_suplente,
                    'fecha': fecha,
                    'id_carrera': id_carrera,
                    'id_materia': id_materia,
                    'modulos': modulos if 'modulos' in locals() else '',
                    'fecha_desde': fecha_desde,
                    'fecha_hasta': fecha_hasta,
                    'observaciones': observaciones
                }
            )

        # === INSERTAR EN BASE DE DATOS ===
        try:
            query = """
                INSERT INTO suplencias (
                    dni_profesor, dni_suplente, fecha, id_carrera, id_materia,
                    modulos, fecha_desde, fecha_hasta, observaciones
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            ejecutar_sql(query, (
                dni_profesor, dni_suplente, fecha, id_carrera, id_materia,
                modulos, fecha_desde, fecha_hasta, observaciones
            ))
            flash('Suplencia agregada correctamente.', 'success')
        except Exception as e:
            print(f"Error al agregar suplencia: {e}")
            flash('Error al guardar la suplencia.', 'danger')

        return redirect(url_for('listado_suplencias'))

#################LISTADO DE SUPLENCIAS
@app.route('/profesores/listado_suplencias')
@perfil_requerido(['1', '2'])
def listado_suplencias():
    query = """
        SELECT 
            s.id_suplencia,
            s.dni_profesor, p.nombre, p.apellido,
            s.fecha,
            c.nombre AS carrera_nombre,
            m.nombre AS materia_nombre,
            s.modulos,
            s.fecha_desde, s.fecha_hasta,
            s.observaciones,
            s.dni_suplente,
            COALESCE(ps.nombre, '') AS suplente_nombre,
            COALESCE(ps.apellido, '') AS suplente_apellido
        FROM suplencias s
        JOIN profesores p ON s.dni_profesor = p.dni_profesor
        JOIN lista_carreras c ON s.id_carrera = c.id_carrera
        JOIN materias m ON s.id_materia = m.id_materia
        LEFT JOIN profesores ps ON s.dni_suplente = ps.dni_profesor
        ORDER BY s.fecha DESC
    """
    resultados = ejecutar_sql(query)

    # Convertir a lista de diccionarios
    suplencias = []
    for row in resultados:
        suplencia = {
            'id_suplencia': row[0],
            'dni_profesor': row[1],
            'nombre': row[2],
            'apellido': row[3],
            'fecha': row[4],
            'carrera_nombre': row[5],
            'materia_nombre': row[6],
            'modulos': row[7],
            'fecha_desde': row[8],
            'fecha_hasta': row[9],
            'observaciones': row[10],
            'dni_suplente': row[11],
            'suplente_nombre': row[12],
            'suplente_apellido': row[13]
        }
        suplencias.append(suplencia)

    return render_template('profesores/listado_suplencias.html', suplencias=suplencias)

#################EDITAR SUPLENCIA
@app.route('/profesores/editar_suplencia/<int:id_suplencia>', methods=['GET', 'POST'])
@perfil_requerido(['1', '2'])
def editar_suplencia(id_suplencia):
    # === OBTENER DATOS COMUNES ===
    profesores = ejecutar_sql("SELECT dni_profesor, nombre, apellido FROM profesores ORDER BY apellido, nombre")
    carreras = ejecutar_sql("SELECT id_carrera, nombre FROM lista_carreras ORDER BY nombre")
    materias = ejecutar_sql("SELECT id_materia, nombre, id_carrera FROM materias ORDER BY nombre")

    if request.method == 'GET':
        # === CARGAR SUPLENCIA EXISTENTE ===
        query = """
            SELECT 
                s.id_suplencia,
                s.dni_profesor,
                s.dni_suplente,
                s.fecha,
                s.id_carrera,
                s.id_materia,
                s.modulos,
                s.fecha_desde,
                s.fecha_hasta,
                s.observaciones
            FROM suplencias s
            WHERE s.id_suplencia = %s
        """
        resultado = ejecutar_sql(query, (id_suplencia,))
        
        if not resultado:
            flash('Suplencia no encontrada.', 'danger')
            return redirect(url_for('listado_suplencias'))
        
        suplencia = {
            'id_suplencia': resultado[0][0],
            'dni_profesor': resultado[0][1],
            'dni_suplente': resultado[0][2],
            'fecha': resultado[0][3].strftime('%Y-%m-%d') if resultado[0][3] else '',
            'id_carrera': resultado[0][4],
            'id_materia': resultado[0][5],
            'modulos': resultado[0][6],
            'fecha_desde': resultado[0][7].strftime('%Y-%m-%d') if resultado[0][7] else '',
            'fecha_hasta': resultado[0][8].strftime('%Y-%m-%d') if resultado[0][8] else '',
            'observaciones': resultado[0][9] or ''
        }

        return render_template(
            'profesores/editar_suplencia.html',
            suplencia=suplencia,
            profesores=profesores,
            carreras=carreras,
            materias=materias
        )

    elif request.method == 'POST':
        # === OBTENER DATOS DEL FORMULARIO ===
        dni_profesor = request.form.get('dni_profesor')
        dni_suplente = request.form.get('dni_suplente') or None
        fecha = request.form.get('fecha')
        id_carrera = request.form.get('id_carrera')
        id_materia = request.form.get('id_materia')
        modulos = request.form.get('modulos')
        fecha_desde = request.form.get('fecha_desde')
        fecha_hasta = request.form.get('fecha_hasta')
        observaciones = request.form.get('observaciones', '').strip()

        # === VALIDACIONES ===
        errores = []

        # 1. Campos obligatorios
        if not all([dni_profesor, fecha, id_carrera, id_materia, modulos, fecha_desde, fecha_hasta]):
            errores.append('Todos los campos obligatorios deben estar completos.')

        # 2. Módulos > 0
        try:
            modulos = int(modulos)
            if modulos <= 0:
                errores.append('La cantidad de módulos debe ser mayor a 0.')
        except:
            errores.append('Módulos debe ser un número válido.')

        # 3. Fechas: desde <= hasta
        if fecha_desde and fecha_hasta:
            if fecha_desde > fecha_hasta:
                errores.append('La fecha "Desde" no puede ser posterior a "Hasta".')

        # 4. Suplente ≠ Titular
        if dni_suplente and dni_suplente == dni_profesor:
            errores.append('El suplente no puede ser el mismo que el profesor titular.')

        # === SI HAY ERRORES: REENVIAR AL FORMULARIO ===
        if errores:
            for error in errores:
                flash(error, 'danger')
            suplencia = {
                'id_suplencia': id_suplencia,
                'dni_profesor': dni_profesor,
                'dni_suplente': dni_suplente,
                'fecha': fecha,
                'id_carrera': id_carrera,
                'id_materia': id_materia,
                'modulos': modulos,
                'fecha_desde': fecha_desde,
                'fecha_hasta': fecha_hasta,
                'observaciones': observaciones
            }
            return render_template(
                'profesores/editar_suplencia.html',
                suplencia=suplencia,
                profesores=profesores,
                carreras=carreras,
                materias=materias
            )

        # === ACTUALIZAR EN BASE DE DATOS ===
        try:
            query = """
                UPDATE suplencias SET
                    dni_profesor = %s,
                    dni_suplente = %s,
                    fecha = %s,
                    id_carrera = %s,
                    id_materia = %s,
                    modulos = %s,
                    fecha_desde = %s,
                    fecha_hasta = %s,
                    observaciones = %s
                WHERE id_suplencia = %s
            """
            ejecutar_sql(query, (
                dni_profesor, dni_suplente, fecha, id_carrera, id_materia,
                modulos, fecha_desde, fecha_hasta, observaciones, id_suplencia
            ))
            flash('Suplencia actualizada correctamente.', 'success')
        except Exception as e:
            print(f"Error al actualizar suplencia {id_suplencia}: {e}")
            flash('Error al guardar los cambios.', 'danger')

        return redirect(url_for('listado_suplencias'))

#################LISTAR INASISTENCIAS
@app.route('/listar_inasistencias', methods=['GET'])
@perfil_requerido(['1', '2'])
def listar_inasistencias():
    if 'id_usuario' not in session:
        flash('Error: Sesión no válida.', 'error')
        return redirect(url_for('login'))

    try:
        query = """
            SELECT i.id_inasistencia, i.dni_profesor, p.nombre, p.apellido, i.fecha, i.motivo, 
                   c.nombre AS nombre_carrera, m.nombre AS nombre_materia, i.presente, i.observaciones
            FROM inasistencias i
            JOIN profesores p ON i.dni_profesor = p.dni_profesor
            JOIN lista_carreras c ON i.id_carrera = c.id_carrera
            JOIN materias m ON i.id_materia = m.id_materia
            ORDER BY i.fecha DESC
        """
        inasistencias = ejecutar_sql(query)
        if inasistencias is None:
            raise Exception("Query returned None for inasistencias")
        inasistencias = [{
            'id_inasistencia': row[0], 'dni_profesor': row[1], 'nombre': row[2], 'apellido': row[3],
            'fecha': row[4], 'motivo': row[5], 'nombre_carrera': row[6], 'nombre_materia': row[7],
            'presente': row[8], 'observaciones': row[9]
        } for row in inasistencias]
    except Exception as e:
        print(f"Error fetching inasistencias: {str(e)}")
        flash('Error al cargar las inasistencias', 'danger')
        inasistencias = []

    return render_template('profesores/listar_inasistencias.html', inasistencias=inasistencias)

#################EDITAR INASISTENCIAS
@app.route('/editar_inasistencia/<int:id_inasistencia>', methods=['GET', 'POST'])
@perfil_requerido(['1', '2'])
def editar_inasistencia(id_inasistencia):
    if 'id_usuario' not in session:
        flash('Error: Sesión no válida.', 'error')
        return redirect(url_for('login'))

    # Fetch inasistencia data
    try:
        query = """
            SELECT i.id_inasistencia, i.dni_profesor, i.fecha, i.motivo, i.id_carrera, 
                   i.id_materia, i.presente, i.observaciones
            FROM inasistencias i
            WHERE i.id_inasistencia = %s
        """
        result = ejecutar_sql(query, (id_inasistencia,))
        if result is None:
            raise Exception("Query returned None for inasistencia")
        if not result:
            flash('Inasistencia no encontrada.', 'error')
            return redirect(url_for('listar_inasistencias'))
        inasistencia = {
            'id_inasistencia': result[0][0], 'dni_profesor': result[0][1], 'fecha': result[0][2],
            'motivo': result[0][3], 'id_carrera': result[0][4], 'id_materia': result[0][5],
            'presente': result[0][6], 'observaciones': result[0][7]
        }
    except Exception as e:
        print(f"Error fetching inasistencia: {str(e)}")
        flash('Error al cargar la inasistencia', 'danger')
        return redirect(url_for('listar_inasistencias'))

    # Fetch profesores, carreras, and materias
    try:
        profesores = ejecutar_sql("SELECT dni_profesor, nombre, apellido FROM profesores ORDER BY nombre, apellido")
        if profesores is None:
            raise Exception("Query returned None for profesores")
        profesores = [{'dni_profesor': p[0], 'nombre': p[1], 'apellido': p[2]} for p in profesores]

        carreras = ejecutar_sql("SELECT id_carrera, nombre FROM lista_carreras ORDER BY nombre")
        if carreras is None:
            raise Exception("Query returned None for carreras")
        carreras = [{'id_carrera': c[0], 'nombre_carrera': c[1]} for c in carreras]

        materias = ejecutar_sql("SELECT id_materia, nombre, id_carrera FROM materias ORDER BY nombre")
        if materias is None:
            raise Exception("Query returned None for materias")
        materias = [{'id_materia': m[0], 'nombre': m[1], 'id_carrera': m[2]} for m in materias]
    except Exception as e:
        print(f"Error fetching data: {str(e)}")
        flash('Error al cargar datos', 'danger')
        return render_template('profesores/editar_inasistencia.html', inasistencia=inasistencia,
                              profesores=[], carreras=[], materias=[])

    if request.method == 'POST':
        try:
            dni_profesor = request.form.get('dni_profesor')
            id_carrera = request.form.get('id_carrera')
            id_materia = request.form.get('id_materia')
            fecha = request.form.get('fecha')
            motivo = request.form.get('motivo') or None
            presente = request.form.get('presente')
            observaciones = request.form.get('observaciones') or None

            # Validate required fields
            if not all([dni_profesor, id_carrera, id_materia, fecha, presente]):
                flash('Los campos obligatorios deben completarse.', 'error')
                return render_template('profesores/editar_inasistencia.html', inasistencia=inasistencia,
                                      profesores=profesores, carreras=carreras, materias=materias)

            # Validate fecha
            try:
                datetime.strptime(fecha, '%Y-%m-%d')
            except ValueError:
                flash('Fecha inválida.', 'error')
                return render_template('profesores/editar_inasistencia.html', inasistencia=inasistencia,
                                      profesores=profesores, carreras=carreras, materias=materias)

            # Validate presente
            if presente not in ['Presente', 'Ausente']:
                flash('El valor de presente debe ser "Presente" o "Ausente".', 'error')
                return render_template('profesores/editar_inasistencia.html', inasistencia=inasistencia,
                                      profesores=profesores, carreras=carreras, materias=materias)

            # Update inasistencia
            query = """
                UPDATE inasistencias
                SET dni_profesor = %s, id_carrera = %s, id_materia = %s, fecha = %s,
                    motivo = %s, presente = %s, observaciones = %s
                WHERE id_inasistencia = %s
            """
            ejecutar_sql(query, (dni_profesor, id_carrera, id_materia, fecha, motivo,
                               presente, observaciones, id_inasistencia))

            flash('Inasistencia actualizada con éxito.', 'success')
            return redirect(url_for('listar_inasistencias'))
        except Exception as e:
            print(f"Error updating inasistencia: {str(e)}")
            flash(f'Error al actualizar inasistencia: {str(e)}', 'error')
            return render_template('profesores/editar_inasistencia.html', inasistencia=inasistencia,
                                  profesores=profesores, carreras=carreras, materias=materias)

    return render_template('profesores/editar_inasistencia.html', inasistencia=inasistencia,
                          profesores=profesores, carreras=carreras, materias=materias)

#################LISTAR TOMA DE POSESION
@app.route('/listar_toma_posesion', methods=['GET'])
@perfil_requerido(['1', '2'])
def listar_toma_posesion():
    if 'id_usuario' not in session:
        flash('Error: Sesión no válida.', 'error')
        return redirect(url_for('login'))

    # === FILTRO POR ESTADO ===
    filtro = request.args.get('filtro', 'todos')  # todos, activos, inactivos

    try:
        # Base query (sin filtro de activo aún)
        query = """
            SELECT t.id_toma, t.dni_profesor, p.nombre, p.apellido, t.fecha, 
                   c.nombre AS nombre_carrera, m.nombre AS nombre_materia, 
                   t.modulos, t.observaciones, t.situacion_revista,
                   t.activo, p.activo AS profesor_activo, c.activo AS carrera_activa
            FROM toma_posesion t
            JOIN profesores p ON t.dni_profesor = p.dni_profesor
            JOIN lista_carreras c ON t.id_carrera = c.id_carrera
            JOIN materias m ON t.id_materia = m.id_materia
        """

        # === APLICAR FILTRO ===
        if filtro == 'activos':
            query += " WHERE t.activo = 1"
        elif filtro == 'inactivos':
            query += " WHERE t.activo = 0"

        query += " ORDER BY t.fecha DESC"

        tomas = ejecutar_sql(query)
        if tomas is None:
            raise Exception("Query returned None")

        tomas = [{
            'id_toma': row[0], 'dni_profesor': row[1], 'nombre': row[2], 'apellido': row[3],
            'fecha': row[4], 'nombre_carrera': row[5], 'nombre_materia': row[6],
            'modulos': row[7], 'observaciones': row[8], 'situacion_revista': row[9],
            'activo': row[10], 'profesor_activo': row[11], 'carrera_activa': row[12]
        } for row in tomas]

    except Exception as e:
        print(f"Error fetching tomas: {str(e)}")
        flash('Error al cargar las tomas de posesión', 'danger')
        tomas = []

    return render_template('profesores/listar_toma_posesion.html', tomas=tomas, filtro=filtro)

#################EDITAR TOMA DE POSESION
@app.route('/editar_toma_posesion/<int:id_toma>', methods=['GET', 'POST'])
@perfil_requerido(['1', '2'])
def editar_toma_posesion(id_toma):
    if 'id_usuario' not in session:
        flash('Error: Sesión no válida.', 'error')
        return redirect(url_for('login'))

    # === CARGAR TOMA DE POSESIÓN CON situacion_revista ===
    try:
        query = """
            SELECT id_toma, dni_profesor, fecha, id_carrera, id_materia, 
                   modulos, observaciones, situacion_revista
            FROM toma_posesion
            WHERE id_toma = %s
        """
        result = ejecutar_sql(query, (id_toma,))
        if result is None:
            raise Exception("Query returned None for toma_posesion")
        if not result:
            flash('Toma de posesión no encontrada.', 'error')
            return redirect(url_for('listar_toma_posesion'))
        toma_posesion = {
            'id_toma': result[0][0], 'dni_profesor': result[0][1], 'fecha': result[0][2],
            'id_carrera': result[0][3], 'id_materia': result[0][4], 'modulos': result[0][5],
            'observaciones': result[0][6], 'situacion_revista': result[0][7]
        }
    except Exception as e:
        print(f"Error fetching toma_posesion: {str(e)}")
        flash('Error al cargar la toma de posesión', 'danger')
        return redirect(url_for('listar_toma_posesion'))

    # === CARGAR LISTAS (profesores, carreras, materias) ===
    try:
        profesores = ejecutar_sql("SELECT dni_profesor, nombre, apellido FROM profesores ORDER BY nombre, apellido") or []
        profesores = [(p[0], p[1], p[2]) for p in profesores]

        carreras = ejecutar_sql("SELECT id_carrera, nombre FROM lista_carreras ORDER BY nombre") or []
        carreras = [(c[0], '', '', c[1]) for c in carreras]  # carrera[3] = nombre

        materias = ejecutar_sql("SELECT id_materia, nombre, id_carrera FROM materias ORDER BY nombre") or []
        materias = [(m[0], m[1], m[2]) for m in materias]
    except Exception as e:
        print(f"Error fetching data: {str(e)}")
        flash('Error al cargar datos', 'danger')
        return render_template('profesores/editar_toma_posesion.html', 
                              profesores=[], carreras=[], materias=[], toma_posesion=toma_posesion)

    # === POST: ACTUALIZAR ===
    if request.method == 'POST':
        try:
            dni_profesor = request.form.get('dni_profesor')
            fecha = request.form.get('fecha')
            id_carrera = request.form.get('id_carrera')
            id_materia = request.form.get('id_materia')
            modulos = request.form.get('modulos')
            observaciones = request.form.get('observaciones') or None
            situacion_revista = request.form.get('situacion_revista')
            if situacion_revista == '':
                situacion_revista = None

            # === VALIDACIONES ===
            if not all([dni_profesor, fecha, id_carrera, id_materia, modulos, situacion_revista]):
                flash('Todos los campos son obligatorios.', 'error')
                return render_template('profesores/editar_toma_posesion.html', 
                                      profesores=profesores, carreras=carreras, 
                                      materias=materias, toma_posesion=toma_posesion)

            try:
                datetime.strptime(fecha, '%Y-%m-%d')
            except ValueError:
                flash('Fecha inválida.', 'error')
                return render_template('profesores/editar_toma_posesion.html', 
                                      profesores=profesores, carreras=carreras, 
                                      materias=materias, toma_posesion=toma_posesion)

            try:
                modulos = int(modulos)
                if modulos < 0:
                    raise ValueError
            except ValueError:
                flash('Los módulos deben ser un número no negativo.', 'error')
                return render_template('profesores/editar_toma_posesion.html', 
                                      profesores=profesores, carreras=carreras, 
                                      materias=materias, toma_posesion=toma_posesion)

            # === ACTUALIZAR EN DB ===
            query = """
                UPDATE toma_posesion
                SET dni_profesor = %s, fecha = %s, id_carrera = %s, id_materia = %s,
                    modulos = %s, observaciones = %s, situacion_revista = %s
                WHERE id_toma = %s
            """
            ejecutar_sql(query, (dni_profesor, fecha, id_carrera, id_materia, 
                               modulos, observaciones, situacion_revista, id_toma))
            flash('Toma de posesión actualizada con éxito.', 'success')
            return redirect(url_for('listar_toma_posesion'))

        except Exception as e:
            print(f"Error updating toma_posesion: {str(e)}")
            flash(f'Error al actualizar: {str(e)}', 'error')
            return render_template('profesores/editar_toma_posesion.html', 
                                  profesores=profesores, carreras=carreras, 
                                  materias=materias, toma_posesion=toma_posesion)

    # === GET: MOSTRAR FORMULARIO ===
    return render_template('profesores/editar_toma_posesion.html', 
                          profesores=profesores, carreras=carreras, 
                          materias=materias, toma_posesion=toma_posesion)

#################LISTAR LICENCIAS
@app.route('/listar_licencias', methods=['GET'])
@perfil_requerido(['1', '2'])
def listar_licencias():
    if 'id_usuario' not in session:
        flash('Error: Sesión no válida.', 'error')
        return redirect(url_for('login'))

    try:
        query = """
            SELECT l.id_licencia, l.dni_profesor, p.nombre, p.apellido, l.desde, l.hasta,
                   l.licencia, l.tiempo_estimado, c.nombre AS nombre_carrera, m.nombre AS nombre_materia,
                   l.observaciones
            FROM licencias l
            JOIN profesores p ON l.dni_profesor = p.dni_profesor
            JOIN lista_carreras c ON l.id_carrera = c.id_carrera
            JOIN materias m ON l.id_materia = m.id_materia
            ORDER BY l.desde DESC
        """
        licencias = ejecutar_sql(query)
        if licencias is None:
            raise Exception("Query returned None for licencias")
        licencias = [{
            'id_licencia': row[0], 'dni_profesor': row[1], 'nombre': row[2], 'apellido': row[3],
            'desde': row[4], 'hasta': row[5], 'licencia': row[6], 'tiempo_estimado': row[7],
            'nombre_carrera': row[8], 'nombre_materia': row[9], 'observaciones': row[10]
        } for row in licencias]
    except Exception as e:
        print(f"Error fetching licencias: {str(e)}")
        flash('Error al cargar las licencias', 'danger')
        licencias = []

    return render_template('profesores/listar_licencias.html', licencias=licencias)

#################EDITAR LICENCIA
@app.route('/editar_licencia/<int:id_licencia>', methods=['GET', 'POST'])
@perfil_requerido(['1', '2'])
def editar_licencia(id_licencia):
    if 'id_usuario' not in session:
        flash('Error: Sesión no válida.', 'error')
        return redirect(url_for('login'))

    # Fetch licencia data
    try:
        query = """
            SELECT id_licencia, dni_profesor, desde, hasta, id_carrera, id_materia,
                   licencia, tiempo_estimado, observaciones
            FROM licencias
            WHERE id_licencia = %s
        """
        result = ejecutar_sql(query, (id_licencia,))
        if result is None:
            raise Exception("Query returned None for licencia")
        if not result:
            flash('Licencia no encontrada.', 'error')
            return redirect(url_for('listar_licencias'))
        licencia = {
            'id_licencia': result[0][0], 'dni_profesor': result[0][1], 'desde': result[0][2],
            'hasta': result[0][3], 'id_carrera': result[0][4], 'id_materia': result[0][5],
            'licencia': result[0][6], 'tiempo_estimado': result[0][7], 'observaciones': result[0][8]
        }
    except Exception as e:
        print(f"Error fetching licencia: {str(e)}")
        flash('Error al cargar la licencia', 'danger')
        return redirect(url_for('listar_licencias'))

    # Fetch profesores, carreras, and materias
    try:
        profesores = ejecutar_sql("SELECT dni_profesor, nombre, apellido FROM profesores ORDER BY nombre, apellido")
        if profesores is None:
            raise Exception("Query returned None for profesores")
        profesores = [(p[0], p[1], p[2]) for p in profesores]

        carreras = ejecutar_sql("SELECT id_carrera, nombre FROM lista_carreras ORDER BY nombre")
        if carreras is None:
            raise Exception("Query returned None for carreras")
        carreras = [(c[0], '', '', c[1]) for c in carreras]  # Match carrera[3] in template

        materias = ejecutar_sql("SELECT id_materia, nombre, id_carrera FROM materias ORDER BY nombre")
        if materias is None:
            raise Exception("Query returned None for materias")
        materias = [(m[0], m[1], m[2]) for m in materias]
    except Exception as e:
        print(f"Error fetching data: {str(e)}")
        flash('Error al cargar datos', 'danger')
        return render_template('profesores/editar_licencia.html', profesores=[], carreras=[],
                              materias=[], licencia=licencia)

    if request.method == 'POST':
        try:
            dni_profesor = request.form.get('dni_profesor')
            desde = request.form.get('desde')
            hasta = request.form.get('hasta') or None
            id_carrera = request.form.get('id_carrera')
            id_materia = request.form.get('id_materia')
            licencia = request.form.get('licencia')
            tiempo_estimado = request.form.get('tiempo_estimado')
            observaciones = request.form.get('observaciones') or None

            # Validate required fields
            if not all([dni_profesor, desde, id_carrera, id_materia, licencia, tiempo_estimado]):
                flash('Los campos obligatorios deben completarse.', 'error')
                return render_template('profesores/editar_licencia.html', profesores=profesores,
                                      carreras=carreras, materias=materias, licencia=licencia)

            # Validate fecha
            try:
                datetime.strptime(desde, '%Y-%m-%d')
                if hasta:
                    datetime.strptime(hasta, '%Y-%m-%d')
                    if datetime.strptime(hasta, '%Y-%m-%d') < datetime.strptime(desde, '%Y-%m-%d'):
                        flash('La fecha "hasta" no puede ser anterior a "desde".', 'error')
                        return render_template('profesores/editar_licencia.html', profesores=profesores,
                                              carreras=carreras, materias=materias, licencia=licencia)
            except ValueError:
                flash('Fechas inválidas.', 'error')
                return render_template('profesores/editar_licencia.html', profesores=profesores,
                                      carreras=carreras, materias=materias, licencia=licencia)

            # Validate licencia and tiempo_estimado
            if licencia not in ['Licencia administrativa', 'Licencia médica', 'Ausente']:
                flash('Tipo de licencia inválido.', 'error')
                return render_template('profesores/editar_licencia.html', profesores=profesores,
                                      carreras=carreras, materias=materias, licencia=licencia)
            if tiempo_estimado not in ['Menos de 30 días', 'Menor a 4 meses', 'Mayor a 4 meses', 'Difícil cobertura']:
                flash('Tiempo estimado inválido.', 'error')
                return render_template('profesores/editar_licencia.html', profesores=profesores,
                                      carreras=carreras, materias=materias, licencia=licencia)

            # Update licencia
            query = """
                UPDATE licencias
                SET dni_profesor = %s, desde = %s, hasta = %s, id_carrera = %s, id_materia = %s,
                    licencia = %s, tiempo_estimado = %s, observaciones = %s
                WHERE id_licencia = %s
            """
            ejecutar_sql(query, (dni_profesor, desde, hasta, id_carrera, id_materia, licencia,
                               tiempo_estimado, observaciones, id_licencia))
            flash('Licencia actualizada con éxito.', 'success')
            return redirect(url_for('listar_licencias'))
        except Exception as e:
            print(f"Error updating licencia: {str(e)}")
            flash(f'Error al actualizar licencia: {str(e)}', 'error')
            return render_template('profesores/editar_licencia.html', profesores=profesores,
                                  carreras=carreras, materias=materias, licencia=licencia)

    return render_template('profesores/editar_licencia.html', profesores=profesores,
                          carreras=carreras, materias=materias, licencia=licencia)

#################LISTAR CESES
@app.route('/listar_ceses', methods=['GET'])
@perfil_requerido(['1', '2'])
def listar_ceses():
    if 'id_usuario' not in session:
        flash('Error: Sesión no válida.', 'error')
        return redirect(url_for('login'))

    try:
        query = """
            SELECT c.id_cese, c.dni_profesor, p.nombre, p.apellido, lc.nombre, m.nombre,
                   c.fecha, c.hs_modulos, c.motivo, c.observaciones, c.anio
            FROM ceses c
            JOIN profesores p ON c.dni_profesor = p.dni_profesor
            JOIN lista_carreras lc ON c.id_carrera = lc.id_carrera
            JOIN materias m ON c.id_materia = m.id_materia
            ORDER BY c.fecha DESC
        """
        ceses = ejecutar_sql(query)
        if ceses is None:
            raise Exception("Query returned None for ceses")
        ceses = [(c[0], c[1], c[2], c[3], c[4], c[5], c[6], c[7], c[8], c[9], c[10]) for c in ceses]
    except Exception as e:
        print(f"Error fetching ceses: {str(e)}")
        flash('Error al cargar ceses', 'danger')
        ceses = []

    return render_template('profesores/listar_ceses.html', ceses=ceses)

#################EDITAR CESE
@app.route('/editar_cese/<int:id_cese>', methods=['GET', 'POST'])
@perfil_requerido(['1', '2'])
def editar_cese(id_cese):
    if 'id_usuario' not in session:
        flash('Error: Sesión no válida.', 'error')
        return redirect(url_for('login'))

    # Fetch cese details
    try:
        query = """
            SELECT c.id_cese, c.dni_profesor, p.nombre, p.apellido, lc.nombre, m.nombre,
                   c.fecha, c.hs_modulos, c.motivo, c.observaciones, c.anio
            FROM ceses c
            JOIN profesores p ON c.dni_profesor = p.dni_profesor
            JOIN lista_carreras lc ON c.id_carrera = lc.id_carrera
            JOIN materias m ON c.id_materia = m.id_materia
            WHERE c.id_cese = %s
        """
        cese = ejecutar_sql(query, (id_cese,))
        if cese is None or not cese:
            flash('Cese no encontrado.', 'error')
            return redirect(url_for('listar_ceses'))
        cese = cese[0]
    except Exception as e:
        print(f"Error fetching cese: {str(e)}")
        flash('Error al cargar cese', 'danger')
        return redirect(url_for('listar_ceses'))

    if request.method == 'POST':
        try:
            fecha = request.form.get('fecha')
            anio = request.form.get('anio') or None
            hs_modulos = request.form.get('hs_modulos')
            motivo = request.form.get('motivo')
            observaciones = request.form.get('observaciones') or None

            # Validate required fields
            if not all([fecha, hs_modulos, motivo]):
                flash('Los campos obligatorios deben completarse.', 'error')
                return render_template('profesores/editar_cese.html', cese=cese)

            # Validate fecha
            try:
                datetime.strptime(fecha, '%Y-%m-%d')
            except ValueError:
                flash('Fecha inválida.', 'error')
                return render_template('profesores/editar_cese.html', cese=cese)

            # Validate motivo
            if motivo not in ['Jubilación', 'Renuncia', 'Fallecimiento', 'Otros']:
                flash('Motivo inválido.', 'error')
                return render_template('profesores/editar_cese.html', cese=cese)

            # Validate anio
            if anio and anio not in ['1°', '2°', '3°', '4°']:
                flash('Año inválido.', 'error')
                return render_template('profesores/editar_cese.html', cese=cese)

            # Validate hs_modulos
            try:
                hs_modulos = int(hs_modulos)
                if hs_modulos < 0:
                    flash('Módulos deben ser no negativos.', 'error')
                    return render_template('profesores/editar_cese.html', cese=cese)
            except ValueError:
                flash('Módulos deben ser un número válido.', 'error')
                return render_template('profesores/editar_cese.html', cese=cese)

            # Update cese
            query = """
                UPDATE ceses
                SET fecha = %s, anio = %s, hs_modulos = %s, motivo = %s, observaciones = %s
                WHERE id_cese = %s
            """
            ejecutar_sql(query, (fecha, anio, hs_modulos, motivo, observaciones, id_cese))

            flash('Cese actualizado con éxito.', 'success')
            return redirect(url_for('listar_ceses'))
        except Exception as e:
            print(f"Error updating cese: {str(e)}")
            flash(f'Error al actualizar cese: {str(e)}', 'error')
            return render_template('profesores/editar_cese.html', cese=cese)

    return render_template('profesores/editar_cese.html', cese=cese)

#################LISTAR ASISTENCIAS/INASISTENCIAS
@app.route('/listar_profesores_inasistencias')
@perfil_requerido(['1', '2'])
def listar_profesores_inasistencias():
    if 'id_usuario' not in session:
        return redirect(url_for('login'))

    try:
        profesores = ejecutar_sql("""
            SELECT dni_profesor, nombre, apellido 
            FROM profesores 
            ORDER BY apellido, nombre
        """) or []
    except:
        profesores = []

    return render_template('profesores/listar_profesores_inasistencias.html', profesores=profesores)

####################################################################
@app.route('/api/resumen_inasistencias_mes')
def api_resumen_inasistencias_mes():
    dni = request.args.get('dni')
    mes = request.args.get('mes')
    anio = request.args.get('anio')

    if not all([dni, mes, anio]):
        return jsonify({})

    try:
        # Validar mes (01-12)
        if not (1 <= int(mes) <= 12):
            return jsonify({})

        # Validar que anio sea número de 4 dígitos
        if not anio.isdigit() or len(anio) != 4:
            return jsonify({})

        anio = int(anio)

        # Consulta
        query = """
            SELECT 
                m.id_materia,
                m.nombre,
                SUM(CASE WHEN i.presente = 'Presente' THEN 1 ELSE 0 END) AS asistencias,
                SUM(CASE WHEN i.presente = 'Ausente' THEN 1 ELSE 0 END) AS inasistencias
            FROM inasistencias i
            JOIN materias m ON i.id_materia = m.id_materia
            WHERE i.dni_profesor = %s
              AND YEAR(i.fecha) = %s
              AND MONTH(i.fecha) = %s
            GROUP BY m.id_materia, m.nombre
            ORDER BY m.nombre
        """
        results = ejecutar_sql(query, (dni, anio, mes))
        
        if not results:
            return jsonify({'profesor': None, 'materias': []})

        # Profesor
        prof_result = ejecutar_sql(
            "SELECT dni_profesor, nombre, apellido FROM profesores WHERE dni_profesor = %s",
            (dni,)
        )
        if not prof_result:
            return jsonify({'profesor': None, 'materias': []})

        profesor = {
            'dni': prof_result[0][0],
            'nombre': prof_result[0][1],
            'apellido': prof_result[0][2]
        }

        materias = []
        for row in results:
            materias.append({
                'nombre': row[1],
                'asistencias': row[2] or 0,
                'inasistencias': row[3] or 0
            })

        return jsonify({
            'profesor': profesor,
            'materias': materias
        })

    except Exception as e:
        print(f"Error API: {e}")
        return jsonify({}), 500


#################CHECK FOJA
@app.route('/check_foja', methods=['POST'])
@perfil_requerido(['1', '2'])
def check_foja():
    foja = request.form.get('foja')
    print(f"Foja check requested: {foja}")
    if not foja:
        print("Foja check: No Foja provided")
        return jsonify({'exists': False})
    try:
        query = "SELECT COUNT(*) FROM profesores WHERE foja = %s"
        result = ejecutar_sql(query, (foja,))[0][0]
        exists = result > 0
        print(f"Foja check: {foja}, Exists: {exists}")
        return jsonify({'exists': exists})
    except Exception as e:
        print(f"Foja check error: {str(e)}")
        return jsonify({'exists': False})

#################CHECK REGISTRO
@app.route('/check_registro', methods=['POST'])
@perfil_requerido(['1', '2'])
def check_registro():
    registro = request.form.get('n_registro')
    print(f"Registro check requested: {registro}")
    if not registro:
        print("Registro check: No N° Registro provided")
        return jsonify({'exists': False})
    try:
        query = "SELECT COUNT(*) FROM profesores WHERE n_registro = %s"
        result = ejecutar_sql(query, (registro,))[0][0]
        exists = result > 0
        print(f"Registro check: {registro}, Exists: {exists}")
        return jsonify({'exists': exists})
    except Exception as e:
        print(f"Registro check error: {str(e)}")
        return jsonify({'exists': False})

#################CHECK DNI
@app.route('/check_dni', methods=['POST'])
@perfil_requerido(['1', '2'])
def check_dni():
    dni = request.form.get('dni_profesor')
    print(f"DNI check requested: {dni}")
    if not dni:
        print("DNI check: No DNI provided")
        return jsonify({'exists': False})
    try:
        query = "SELECT COUNT(*) FROM profesores WHERE dni_profesor = %s"
        result = ejecutar_sql(query, (dni,))[0][0]
        print(f"DNI check: {dni}, Exists: {result > 0}")
        return jsonify({'exists': result > 0})
    except Exception as e:
        print(f"DNI check error: {str(e)}")
        return jsonify({'exists': False})

#################AGREGAR TITULO
@app.route('/agregar_titulo', methods=['POST'])
@perfil_requerido(['1', '2'])
def agregar_titulo():
    dni_profesor = request.form.get('dni_profesor')
    titulo = request.form.get('titulo')
    expedido_por = request.form.get('expedido_por')
    duracion = request.form.get('duracion') or None
    finalizo = 1 if request.form.get('finalizo') else 0
    fecha_egreso = request.form.get('fecha_egreso') or None
    porcentaje_carrera = request.form.get('porcentaje_carrera') or None

    try:
        query = """
            INSERT INTO titulos_profesores 
            (dni_profesor, titulo, expedido_por, duracion, finalizo, fecha_egreso, porcentaje_carrera)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        ejecutar_sql(query, (dni_profesor, titulo, expedido_por, duracion, finalizo, fecha_egreso, porcentaje_carrera))
        flash('Título agregado correctamente.', 'success')
    except Exception as e:
        flash('Error al agregar el título.', 'danger')
    return redirect(url_for('editar_profesor', dni_profesor=dni_profesor))

#################EDITAR TITULO
@app.route('/editar_titulo', methods=['POST'])
@perfil_requerido(['1', '2'])
def editar_titulo():
    id_titulo = request.form.get('id_titulo')
    titulo = request.form.get('titulo')
    expedido_por = request.form.get('expedido_por')
    duracion = request.form.get('duracion') or None
    finalizo = 1 if request.form.get('finalizo') else 0
    fecha_egreso = request.form.get('fecha_egreso') or None
    porcentaje_carrera = request.form.get('porcentaje_carrera') or None

    try:
        query = """
            UPDATE titulos_profesores SET
            titulo = %s, expedido_por = %s, duracion = %s,
            finalizo = %s, fecha_egreso = %s, porcentaje_carrera = %s
            WHERE id_titulo = %s
        """
        ejecutar_sql(query, (titulo, expedido_por, duracion, finalizo, fecha_egreso, porcentaje_carrera, id_titulo))
        flash('Título actualizado correctamente.', 'success')
    except Exception as e:
        flash('Error al actualizar el título.', 'danger')
    return redirect(url_for('editar_profesor', dni_profesor=request.form.get('dni_profesor')))

#################ELIMINAR TITULO
@app.route('/eliminar_titulo', methods=['POST'])
@perfil_requerido(['1', '2'])
def eliminar_titulo():
    id_titulo = request.form.get('id_titulo')
    dni_profesor = request.form.get('dni_profesor')
    try:
        ejecutar_sql("DELETE FROM titulos_profesores WHERE id_titulo = %s", (id_titulo,))
        flash('Título eliminado.', 'success')
    except Exception as e:
        flash('Error al eliminar el título.', 'danger')
    return redirect(url_for('editar_profesor', dni_profesor=dni_profesor))











###PROFESORES######PROFESORES######PROFESORES######PROFESORES######PROFESORES######PROFESORES######PROFESORES######PROFESORES######PROFESORES######PROFESORES######PROFESORES######PROFESORES###













#FINALES##FINALES##FINALES##FINALES##FINALES##FINALES##FINALES##FINALES##FINALES##FINALES##FINALES##FINALES##FINALES##FINALES##FINALES##FINALES##FINALES##FINALES##FINALES##FINALES#
#################MESAS
@app.route('/mesas')
def mesas():
    if 'nombre' not in session:
        flash('Por favor, inicia sesión.', 'error')
        return redirect(url_for('login'))
    
    perfil = session.get('perfil')
    
    if perfil == '4':
        return redirect(url_for('mesas_disponibles'))
    elif perfil in ['1', '2']:
        flash('Gestión de mesas para administradores aún no implementada.', 'info')
        return redirect(url_for('home'))
    else:
        flash('No tienes permiso para acceder a esta sección.', 'error')
        return redirect(url_for('home'))

#################ALUMNO LISTADO DE MESAS

@app.route('/finales/mesas_disponibles', methods=['GET', 'POST'])
@perfil_requerido(['4'])
def mesas_disponibles():
    if 'id_usuario' not in session:
        flash('Error: Sesión no válida.', 'error')
        return redirect(url_for('login'))
    id_usuario = session['id_usuario']

    # Obtener materias aprobadas
    query_aprobadas = """
        SELECT id_materia FROM aprobaciones 
        WHERE id_usuario = %s AND aprobada = 1
    """
    materias_aprobadas = [row[0] for row in ejecutar_sql(query_aprobadas, (id_usuario,)) or []]

    # Obtener mesas disponibles
    query_mesas = """
        SELECT DISTINCT f.id_mesa, m.nombre, f.fecha_examen, f.fecha_apertura, f.fecha_cierre,
                        p.nombre, p.apellido, p.dni_profesor,
                        COALESCE(im.intentos_restantes, 8) AS intentos_restantes
        FROM mesas_f f
        JOIN materias m ON f.id_materia = m.id_materia
        JOIN profesores p ON f.dni_profesor = p.dni_profesor
        JOIN lista_carreras lc ON m.id_carrera = lc.id_carrera
        JOIN inscripciones_carreras ic ON m.id_carrera = ic.id_carrera
        LEFT JOIN intentos_materia im ON m.id_materia = im.id_materia AND im.id_usuario = %s
        LEFT JOIN aprobaciones a ON m.id_materia = a.id_materia AND a.id_usuario = %s
        LEFT JOIN inscripcion_f inf ON f.id_mesa = inf.id_mesa AND inf.id_usuario = %s AND inf.estado = 'inscripto'
        WHERE ic.id_usuario = %s
        AND f.fecha_apertura <= NOW()
        AND f.fecha_cierre >= NOW()
        AND (im.intentos_restantes IS NULL OR im.intentos_restantes > 0)
        AND (a.aprobada IS NULL OR a.aprobada = 0)
        AND inf.id_mesa IS NULL
        ORDER BY m.nombre ASC
    """
    mesas = ejecutar_sql(query_mesas, (id_usuario, id_usuario, id_usuario, id_usuario)) or []

    # Filtrar correlativas
    mesas_filtradas = []
    for mesa in mesas:
        id_mesa = mesa[0]
        query_correlativas = """
            SELECT id_materia_correlativa
            FROM correlativas
            WHERE id_materia = (SELECT id_materia FROM mesas_f WHERE id_mesa = %s)
        """
        correlativas_requeridas = [row[0] for row in ejecutar_sql(query_correlativas, (id_mesa,)) or []]
        cumple_correlativas = all(corr in materias_aprobadas for corr in correlativas_requeridas)
        if cumple_correlativas:
            mesas_filtradas.append(mesa)

    if request.method == 'POST':
        id_mesa = request.form.get('id_mesa')

        # Verificar mesa válida
        query_mesa_valida = """
            SELECT f.id_mesa, m.id_materia, f.fecha_examen
            FROM mesas_f f
            JOIN materias m ON f.id_materia = m.id_materia
            JOIN lista_carreras lc ON m.id_carrera = lc.id_carrera
            JOIN inscripciones_carreras ic ON m.id_carrera = ic.id_carrera
            LEFT JOIN intentos_materia im ON m.id_materia = im.id_materia AND im.id_usuario = %s
            LEFT JOIN aprobaciones a ON m.id_materia = a.id_materia AND a.id_usuario = %s
            LEFT JOIN inscripcion_f inf ON f.id_mesa = inf.id_mesa AND inf.id_usuario = %s AND inf.estado = 'inscripto'
            WHERE f.id_mesa = %s
            AND ic.id_usuario = %s
            AND f.fecha_apertura <= NOW()
            AND f.fecha_cierre >= NOW()
            AND (im.intentos_restantes IS NULL OR im.intentos_restantes > 0)
            AND (a.aprobada IS NULL OR a.aprobada = 0)
            AND inf.id_mesa IS NULL
        """
        mesa_valida = ejecutar_sql(query_mesa_valida, (id_usuario, id_usuario, id_usuario, id_mesa, id_usuario))
        if not mesa_valida:
            flash('No se puede inscribir en esta mesa.', 'error')
            return redirect(url_for('mesas_disponibles'))

        id_materia = mesa_valida[0][1]
        fecha_examen = mesa_valida[0][2]

        # Verificar correlativas
        query_correlativas = """
            SELECT id_materia_correlativa
            FROM correlativas
            WHERE id_materia = %s
        """
        correlativas_requeridas = [row[0] for row in ejecutar_sql(query_correlativas, (id_materia,)) or []]
        cumple_correlativas = all(corr in materias_aprobadas for corr in correlativas_requeridas)
        if not cumple_correlativas:
            flash('No cumples con las materias correlativas requeridas.', 'error')
            return redirect(url_for('mesas_disponibles'))

        try:
            # Inscribir (SIN restar intento aún)
            query_inscripcion = """
                INSERT INTO inscripcion_f (id_usuario, id_mesa, estado, fecha_inscripcion)
                VALUES (%s, %s, 'inscripto', NOW())
            """
            ejecutar_sql(query_inscripcion, (id_usuario, id_mesa))
            flash('Inscripción realizada con éxito.', 'success')
        except Exception as e:
            flash(f'Error al inscribir: {str(e)}', 'error')

        return redirect(url_for('mesas_disponibles'))

    return render_template('finales/mesas_disponibles.html', mesas=mesas_filtradas)


#################ALUMNO INSCRIBIRSE A MESA
@app.route('/finales/inscribir_mesa/<int:id_mesa>', methods=['GET', 'POST'])
@perfil_requerido(['4'])
def inscribir_mesa(id_mesa):
    if 'id_usuario' not in session:
        flash('Error: Sesión no válida.', 'error')
        return redirect(url_for('login'))
    id_usuario = session['id_usuario']
    now = datetime.now()

    # Verificar si ya está inscripto
    query_verificar_inscripcion = """
        SELECT id_inscripcion_final 
        FROM inscripcion_f 
        WHERE id_usuario = %s AND id_mesa = %s AND estado = 'inscripto'
    """
    inscripcion_existente = ejecutar_sql(query_verificar_inscripcion, (id_usuario, id_mesa))
    print(f"Verificación inscripción existente: {inscripcion_existente}")
    if inscripcion_existente:
        flash('Ya estás inscripto en esta mesa.', 'error')
        return redirect(url_for('mesas_disponibles'))

    # Validar mesa
    query_validar = """
        SELECT f.id_materia, f.fecha_apertura, f.fecha_cierre, 
               COALESCE(im.intentos_restantes, 4) AS intentos_restantes
        FROM mesas_f f
        LEFT JOIN intentos_materia im ON f.id_materia = im.id_materia AND im.id_usuario = %s
        WHERE f.id_mesa = %s AND %s BETWEEN f.fecha_apertura AND f.fecha_cierre
        AND (
            SELECT COUNT(c.id_materia_correlativa) 
            FROM correlativa c
            LEFT JOIN aprobaciones a ON c.id_materia_correlativa = a.id_materia 
            AND a.id_usuario = %s AND a.aprobada = 1
            WHERE c.id_materia = f.id_materia AND a.id_aprobacion IS NULL
        ) = 0
        AND (COALESCE(im.intentos_restantes, 4) > 0)
    """
    result = ejecutar_sql(query_validar, (id_usuario, id_mesa, now, id_usuario))
    print(f"Validación mesa: {result}")
    if not result:
        flash('No puedes inscribirte a esta mesa.', 'error')
        return redirect(url_for('mesas_disponibles'))
    
    id_materia = result[0][0]

    if request.method == 'POST':
        # Actualizar intentos
        query_intentos = """
            INSERT INTO intentos_materia (id_usuario, id_materia, intentos_restantes)
            VALUES (%s, %s, 3)
            ON DUPLICATE KEY UPDATE intentos_restantes = intentos_restantes - 1
        """
        intentos_result = ejecutar_sql(query_intentos, (id_usuario, id_materia))
        print(f"Resultado intentos_materia: {intentos_result}")  # None es normal para INSERT

        # Inscribir
        query_inscripcion = """
            INSERT INTO inscripcion_f (id_usuario, id_mesa, fecha_inscripcion, estado)
            VALUES (%s, %s, NOW(), 'inscripto')
        """
        inscripcion_result = ejecutar_sql(query_inscripcion, (id_usuario, id_mesa))
        print(f"Resultado inscripción: {inscripcion_result}")  # None es normal para INSERT
        
        # Para INSERTs, None es éxito (no hay error)
        flash('Inscripto exitosamente a la mesa.', 'success')
        return redirect(url_for('mesas_inscriptas'))

    # GET: Redirigir a POST para inscripción inmediata
    return redirect(url_for('inscribir_mesa', id_mesa=id_mesa, _method='POST'))

#################MESAS INSCRIPTAS ALUMNO
@app.route('/finales/mesas_inscriptas', methods=['GET'])
@perfil_requerido(['4'])
def mesas_inscriptas():
    if 'id_usuario' not in session:
        flash('Error: Sesión no válida.', 'error')
        return redirect(url_for('login'))
    id_usuario = session['id_usuario']

    # Obtener inscripciones activas
    query_inscriptos = """
        SELECT f.id_mesa, m.nombre, f.fecha_examen, inf.estado,
               COALESCE(im.intentos_restantes, 8) AS intentos_restantes,
               inf.id_inscripcion_final, p.nombre, p.apellido
        FROM inscripcion_f inf
        JOIN mesas_f f ON inf.id_mesa = f.id_mesa
        JOIN materias m ON f.id_materia = m.id_materia
        JOIN profesores p ON f.dni_profesor = p.dni_profesor
        LEFT JOIN intentos_materia im ON m.id_materia = im.id_materia AND im.id_usuario = %s
        WHERE inf.id_usuario = %s AND inf.estado = 'inscripto'
        ORDER BY m.nombre ASC
    """
    inscriptos = ejecutar_sql(query_inscriptos, (id_usuario, id_usuario)) or []

    return render_template('finales/mesas_inscriptas.html', inscriptos=inscriptos)

#################CANCELADOR DE MESA
@app.route('/finales/cancelar_mesa/<int:id_inscripcion_final>', methods=['POST'])
@perfil_requerido(['4'])
def cancelar_mesa(id_inscripcion_final):
    if 'id_usuario' not in session:
        flash('Error: Sesión no válida.', 'error')
        return redirect(url_for('login'))
    id_usuario = session['id_usuario']

    try:
        # Verificar inscripción
        query_inscripcion = """
            SELECT id_mesa, estado, fecha_inscripcion
            FROM inscripcion_f
            WHERE id_inscripcion_final = %s AND id_usuario = %s
        """
        inscripcion = ejecutar_sql(query_inscripcion, (id_inscripcion_final, id_usuario))
        if not inscripcion or inscripcion[0][1] != 'inscripto':
            flash('Inscripción no válida o ya cancelada.', 'error')
            return redirect(url_for('mesas_inscriptas'))

        id_mesa = inscripcion[0][0]
        fecha_inscripcion = inscripcion[0][2]

        # Obtener id_materia
        query_materia = """
            SELECT id_materia
            FROM mesas_f
            WHERE id_mesa = %s
        """
        materia = ejecutar_sql(query_materia, (id_mesa,))
        if not materia:
            flash('Mesa no encontrada.', 'error')
            return redirect(url_for('mesas_inscriptas'))
        id_materia = materia[0][0]

        # Obtener fecha_examen
        query_fecha_examen = """
            SELECT fecha_examen
            FROM mesas_f
            WHERE id_mesa = %s
        """
        fecha_examen = ejecutar_sql(query_fecha_examen, (id_mesa,))[0][0]

        # Cancelar inscripción
        query_cancelar = """
            UPDATE inscripcion_f
            SET estado = 'cancelado'
            WHERE id_inscripcion_final = %s
        """
        ejecutar_sql(query_cancelar, (id_inscripcion_final,))

        # Verificar si se puede devolver intento (>72h antes del examen)
        if fecha_examen - datetime.now() > timedelta(hours=72):
            query_restaurar_intento = """
                INSERT INTO intentos_materia (id_usuario, id_materia, intentos_restantes)
                VALUES (%s, %s, 8)
                ON DUPLICATE KEY UPDATE intentos_restantes = LEAST(intentos_restantes + 1, 8)
            """
            ejecutar_sql(query_restaurar_intento, (id_usuario, id_materia))
            flash('Inscripción cancelada y intento devuelto.', 'success')
        else:
            flash('Inscripción cancelada, pero el intento no se devuelve (menos de 72h).', 'warning')

    except Exception as e:
        flash(f'Error al cancelar inscripción: {str(e)}', 'error')
    return redirect(url_for('mesas_inscriptas'))


#################CREADOR DE MESA
@app.route('/finales/crear_mesa', methods=['GET', 'POST'])
@perfil_requerido(['1', '2'])
def crear_mesa():
    if 'id_usuario' not in session:
        flash('Error: Sesión no válida.', 'error')
        return redirect(url_for('login'))
    id_usuario = session['id_usuario']
    print(f"ID usuario: {id_usuario}, Accediendo a crear mesa")

    if request.method == 'POST':
        id_carrera = request.form.get('id_carrera')
        id_materia = request.form.get('id_materia')
        fecha_examen = request.form.get('fecha_examen')
        fecha_apertura = request.form.get('fecha_apertura')
        fecha_cierre = request.form.get('fecha_cierre')
        dni_profesor = request.form.get('dni_profesor')
        dni_suplente = request.form.get('dni_suplente')

        # Validate required fields
        try:
            if not id_carrera:
                raise ValueError("Carrera es requerida")
            id_carrera = int(id_carrera)
            if not id_materia:
                raise ValueError("Materia es requerida")
            id_materia = int(id_materia)
            if not dni_profesor:
                raise ValueError("Profesor titular es requerido")
            dni_profesor = int(dni_profesor)
            dni_suplente = int(dni_suplente) if dni_suplente else None
            if not fecha_examen:
                raise ValueError("Fecha de examen es requerida")
            fecha_examen = datetime.strptime(fecha_examen, '%Y-%m-%dT%H:%M')
            if not fecha_apertura:
                raise ValueError("Fecha de apertura es requerida")
            fecha_apertura = datetime.strptime(fecha_apertura, '%Y-%m-%dT%H:%M')
            if not fecha_cierre:
                raise ValueError("Fecha de cierre es requerida")
            fecha_cierre = datetime.strptime(fecha_cierre, '%Y-%m-%dT%H:%M')
        except ValueError as e:
            flash(f'Error en los datos: {str(e)}', 'error')
            return redirect(url_for('crear_mesa'))

        # Validate date consistency
        if fecha_apertura >= fecha_examen or fecha_cierre >= fecha_examen:
            flash('La fecha de apertura y cierre deben ser anteriores a la fecha del examen.', 'error')
            return redirect(url_for('crear_mesa'))
        if fecha_apertura >= fecha_cierre:
            flash('La fecha de apertura debe ser anterior a la fecha de cierre.', 'error')
            return redirect(url_for('crear_mesa'))

        # Validate carrera
        query_carrera = """
            SELECT id_carrera FROM lista_carreras WHERE id_carrera = %s AND activo = 1
        """
        carrera = ejecutar_sql(query_carrera, (id_carrera,))
        if not carrera:
            flash('La carrera seleccionada no existe o no está activa.', 'error')
            return redirect(url_for('crear_mesa'))

        # Validate materia and its relation to carrera
        query_materia = """
            SELECT id_materia FROM materias WHERE id_materia = %s AND id_carrera = %s
        """
        materia = ejecutar_sql(query_materia, (id_materia, id_carrera))
        if not materia:
            flash('La materia seleccionada no existe o no pertenece a la carrera seleccionada.', 'error')
            return redirect(url_for('crear_mesa'))

        # Check for existing mesa for the same id_materia with fecha_examen today or in the future
        query_mesa_exists = """
            SELECT id_mesa FROM mesas_f WHERE id_materia = %s AND fecha_examen >= NOW()
        """
        existing_mesa = ejecutar_sql(query_mesa_exists, (id_materia,))
        if existing_mesa:
            flash('Ya existe una mesa de examen activa o futura para esta materia.', 'error')
            return redirect(url_for('crear_mesa'))

        # Validate professors
        query_profesor = """
            SELECT dni_profesor FROM profesores WHERE dni_profesor = %s AND activo = 1
        """
        profesor = ejecutar_sql(query_profesor, (dni_profesor,))
        if not profesor:
            flash('El profesor titular no existe o no está activo.', 'error')
            return redirect(url_for('crear_mesa'))

        if dni_suplente:
            suplente = ejecutar_sql(query_profesor, (dni_suplente,))
            if not suplente:
                flash('El profesor suplente no existe o no está activo.', 'error')
                return redirect(url_for('crear_mesa'))

        # Insert mesa (rely on AUTO_INCREMENT for id_mesa)
        query_insert = """
            INSERT INTO mesas_f (id_materia, fecha_examen, fecha_apertura, fecha_cierre, dni_profesor, dni_suplente)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        params = (id_materia, fecha_examen, fecha_apertura, fecha_cierre, dni_profesor, dni_suplente)
        try:
            ejecutar_sql(query_insert, params)
            flash('Mesa creada con éxito.', 'success')
            return redirect(url_for('listar_mesas'))
        except Exception as e:
            print(f"Error al conectar a MySQL: {str(e)}")
            flash(f'Error al crear la mesa: {str(e)}', 'error')
            return redirect(url_for('crear_mesa'))

    # Fetch data for the form
    query_carreras = """
        SELECT id_carrera, id_instituto, id_turno, nombre, estado, año_cursada, activo
        FROM lista_carreras
        WHERE activo = 1
        ORDER BY nombre
    """
    query_materias = """
        SELECT id_materia, nombre, id_carrera
        FROM materias
        ORDER BY nombre
    """
    query_profesores = """
        SELECT dni_profesor, nombre, apellido
        FROM profesores
        WHERE activo = 1
        ORDER BY nombre, apellido
    """
    carreras = ejecutar_sql(query_carreras) or []
    materias = ejecutar_sql(query_materias) or []
    profesores = ejecutar_sql(query_profesores) or []

    return render_template('finales/crear_mesa.html', carreras=carreras, materias=materias, profesores=profesores)

#################LISTAR MESAS
@app.route('/listar_mesas', methods=['GET'])
@perfil_requerido(['1', '2'])
def listar_mesas():
    if 'id_usuario' not in session:
        flash('Error: Sesión no válida.', 'error')
        return redirect(url_for('login'))
    id_usuario = session['id_usuario']
    print(f"ID usuario: {id_usuario}, Accediendo a listar mesas")

    query_mesas = """
        SELECT f.id_mesa, m.nombre, f.fecha_examen, f.fecha_apertura, f.fecha_cierre,
               p.nombre, p.apellido, p.dni_profesor,
               ps.nombre AS suplente_nombre, ps.apellido AS suplente_apellido, f.dni_suplente
        FROM mesas_f f
        JOIN materias m ON f.id_materia = m.id_materia
        JOIN profesores p ON f.dni_profesor = p.dni_profesor
        LEFT JOIN profesores ps ON f.dni_suplente = ps.dni_profesor
        JOIN lista_carreras lc ON m.id_carrera = lc.id_carrera
        WHERE lc.id_carrera = %s
        ORDER BY m.nombre ASC
    """
    mesas = ejecutar_sql(query_mesas, (1,))  # Asumiendo id_carrera=1
    print(f"Mesas: {mesas}")
    if mesas is None:
        flash('Error al cargar mesas.', 'error')
        mesas = []

    return render_template('finales/listar_mesas.html', mesas=mesas)

################ELIMINADOR DE MESAS
@app.route('/finales/eliminar_mesa/<int:id_mesa>', methods=['POST'])
@perfil_requerido(['1', '2'])
def eliminar_mesa(id_mesa):
    if 'id_usuario' not in session:
        flash('Error: Sesión no válida.', 'error')
        return redirect(url_for('login'))

    try:
        # Obtener id_materia
        query_materia = """
            SELECT id_materia
            FROM mesas_f
            WHERE id_mesa = %s
        """
        materia = ejecutar_sql(query_materia, (id_mesa,))
        if not materia:
            flash('Mesa no encontrada.', 'error')
            return redirect(url_for('listar_mesas'))
        id_materia = materia[0][0]

        # Obtener inscripciones
        query_inscripciones = """
            SELECT id_usuario, id_inscripcion_final
            FROM inscripcion_f
            WHERE id_mesa = %s
        """
        inscripciones = ejecutar_sql(query_inscripciones, (id_mesa,)) or []

        # Cancelar inscripciones y devolver intentos SIEMPRE
        for inscripcion in inscripciones:
            id_usuario, id_inscripcion_final = inscripcion
            query_cancelar = """
                UPDATE inscripcion_f
                SET estado = 'cancelado'
                WHERE id_inscripcion_final = %s
            """
            ejecutar_sql(query_cancelar, (id_inscripcion_final,))

            query_restaurar_intento = """
                INSERT INTO intentos_materia (id_usuario, id_materia, intentos_restantes)
                VALUES (%s, %s, 8)
                ON DUPLICATE KEY UPDATE intentos_restantes = LEAST(intentos_restantes + 1, 8)
            """
            ejecutar_sql(query_restaurar_intento, (id_usuario, id_materia))

        # Eliminar la mesa
        query_eliminar_mesa = """
            DELETE FROM mesas_f
            WHERE id_mesa = %s
        """
        ejecutar_sql(query_eliminar_mesa, (id_mesa,))

        flash('Mesa eliminada con éxito.', 'success')
    except Exception as e:
        flash(f'Error al eliminar mesa: {str(e)}', 'error')
    return redirect(url_for('listar_mesas'))

################GESTOR NOTAS
@app.route('/finales/gestor_notas', methods=['GET', 'POST'])
@perfil_requerido(['1', '2'])
def gestor_notas():
    if 'id_usuario' not in session:
        flash('Error: Sesión no válida.', 'error')
        return redirect(url_for('login'))
    id_usuario = session['id_usuario']
    print(f"ID usuario: {id_usuario}")

    alumno_info = None
    materias = []
    profesores = []

    # Cargar profesores siempre, ordenados alfabéticamente
    query_profesores = """
        SELECT dni_profesor, CONCAT(nombre, ' ', apellido, ' (DNI: ', dni_profesor, ')') AS nombre_completo 
        FROM profesores
        WHERE activo = 1
        ORDER BY nombre, apellido
    """
    profesores = ejecutar_sql(query_profesores) or []
    if not profesores:
        print("Error: Consulta de profesores devolvió None")
        flash('Error al cargar profesores.', 'error')

    if request.method == 'POST':
        dni_alumno = request.form.get('dni_alumno')
        if 'action' in request.form and request.form['action'] == 'buscar':
            # Buscar id_usuario, nombre, apellido del alumno por DNI
            query_alumno = """
                SELECT id_usuario, nombre, apellido 
                FROM usuarios 
                WHERE dni = %s AND activo = 1
            """
            result_alumno = ejecutar_sql(query_alumno, (dni_alumno,))
            if not result_alumno:
                print(f"Error: Alumno con DNI {dni_alumno} no encontrado")
                flash('Alumno no encontrado.', 'error')
                return render_template('finales/gestor_notas.html', materias=[], profesores=profesores, dni_alumno=dni_alumno)

            id_alumno = result_alumno[0][0]
            nombre_alumno = result_alumno[0][1]
            apellido_alumno = result_alumno[0][2]

            # Obtener carrera del alumno
            query_carrera = """
                SELECT lc.nombre 
                FROM inscripciones_carreras ic
                JOIN lista_carreras lc ON ic.id_carrera = lc.id_carrera
                WHERE ic.id_usuario = %s AND ic.activo = 1
            """
            result_carrera = ejecutar_sql(query_carrera, (id_alumno,))
            if not result_carrera:
                flash('Alumno no inscripto en una carrera.', 'error')
                return render_template('finales/gestor_notas.html', materias=[], profesores=profesores, dni_alumno=dni_alumno)
            carrera_alumno = result_carrera[0][0]

            # Obtener materias de la carrera, ordenadas alfabéticamente
            query_materias = """
                SELECT id_materia, nombre 
                FROM materias 
                WHERE id_carrera = (SELECT id_carrera FROM inscripciones_carreras WHERE id_usuario = %s AND activo = 1)
                ORDER BY nombre
            """
            materias = ejecutar_sql(query_materias, (id_alumno,)) or []
            if not materias:
                flash('No se encontraron materias para la carrera del alumno.', 'error')

            alumno_info = {
                'id': id_alumno,
                'nombre': nombre_alumno,
                'apellido': apellido_alumno,
                'carrera': carrera_alumno
            }

            return render_template('finales/gestor_notas.html', alumno_info=alumno_info, materias=materias, profesores=profesores, dni_alumno=dni_alumno)

        elif 'action' in request.form and request.form['action'] == 'aprobar':
            id_alumno = request.form.get('id_alumno')
            id_materia = request.form.get('id_materia')
            dni_profesor = request.form.get('dni_profesor')
            nota = request.form.get('nota')

            if not all([id_alumno, id_materia, dni_profesor, nota]):
                flash('Todos los campos son obligatorios.', 'error')
                return render_template('finales/gestor_notas.html', materias=materias, profesores=profesores, dni_alumno=dni_alumno)

            # Validar nota
            try:
                nota = float(nota)
                if not 1 <= nota <= 10:
                    flash('La nota debe estar entre 1 y 10.', 'error')
                    return render_template('finales/gestor_notas.html', materias=materias, profesores=profesores, dni_alumno=dni_alumno)
            except ValueError:
                flash('La nota debe ser un número válido.', 'error')
                return render_template('finales/gestor_notas.html', materias=materias, profesores=profesores, dni_alumno=dni_alumno)

            # Actualizar o insertar aprobación
            query_aprobacion = """
                INSERT INTO aprobaciones (id_usuario, id_materia, dni_profesor, nota, aprobada)
                VALUES (%s, %s, %s, %s, 1)
                ON DUPLICATE KEY UPDATE dni_profesor = %s, nota = %s, aprobada = 1
            """
            try:
                ejecutar_sql(query_aprobacion, (id_alumno, id_materia, dni_profesor, nota, dni_profesor, nota))
                flash('Materia aprobada exitosamente.', 'success')
            except Exception as e:
                print(f"Error al conectar a MySQL: {str(e)}")
                flash(f'Error al aprobar la materia: {str(e)}', 'error')

            return redirect(url_for('/finales/gestor_notas'))

    return render_template('finales/gestor_notas.html', materias=materias, profesores=profesores)

################ACTA VOLANTE
@app.route('/finales/acta_volante/<int:id_mesa>', methods=['GET'])
@perfil_requerido(['1', '2'])
def acta_volante(id_mesa):
    if 'id_usuario' not in session:
        flash('Error: Sesión no válida.', 'error')
        return redirect(url_for('login'))
    id_usuario = session['id_usuario']
    print(f"ID usuario: {id_usuario}, Generando acta volante para id_mesa: {id_mesa}")

    # Obtener datos de la mesa
    query_mesa = """
        SELECT m.nombre AS materia, f.fecha_examen, 
               CONCAT(p.nombre, ' ', p.apellido) AS profesor, 
               CONCAT(ps.nombre, ' ', ps.apellido) AS suplente,
               lc.nombre AS carrera, tc.descripcion AS turno, 
               YEAR(f.fecha_examen) AS ano
        FROM mesas_f f
        JOIN materias m ON f.id_materia = m.id_materia
        JOIN profesores p ON f.dni_profesor = p.dni_profesor
        LEFT JOIN profesores ps ON f.dni_suplente = ps.dni_profesor
        JOIN lista_carreras lc ON m.id_carrera = lc.id_carrera
        LEFT JOIN inscripciones_carreras ic ON m.id_carrera = ic.id_carrera
        LEFT JOIN turno_carrera tc ON ic.id_turno = tc.id_turno
        WHERE f.id_mesa = %s
        LIMIT 1
    """
    mesa_data = ejecutar_sql(query_mesa, (id_mesa,))
    if not mesa_data:
        flash('Mesa no encontrada o sin datos asociados.', 'error')
        return redirect(url_for('listar_mesas'))

    materia, fecha_examen, profesor, suplente, carrera, turno, ano = mesa_data[0]
    localidad = ''  # Localidad en blanco
    print(f"Datos mesa: materia={materia}, fecha_examen={fecha_examen}, profesor={profesor}, suplente={suplente}, carrera={carrera}, turno={turno}, ano={ano}, localidad={localidad}")

    # Obtener alumnos inscriptos
    query_alumnos = """
        SELECT CONCAT(u.nombre, ' ', u.apellido) AS nombre, u.dni
        FROM inscripcion_f ins
        JOIN usuarios u ON ins.id_usuario = u.id_usuario
        WHERE ins.id_mesa = %s AND ins.estado = 'inscripto'
        ORDER BY u.apellido, u.nombre
    """
    alumnos = ejecutar_sql(query_alumnos, (id_mesa,))
    print(f"Alumnos inscriptos: {alumnos}")

    # Formatear fecha_examen para el footer
    mes_es = {
        'January': 'Enero', 'February': 'Febrero', 'March': 'Marzo', 'April': 'Abril',
        'May': 'Mayo', 'June': 'Junio', 'July': 'Julio', 'August': 'Agosto',
        'September': 'Septiembre', 'October': 'Octubre', 'November': 'Noviembre', 'December': 'Diciembre'
    }
    fecha_formateada = f"{fecha_examen.day} de {mes_es[fecha_examen.strftime('%B')]} de {fecha_examen.year}" if isinstance(fecha_examen, datetime) else fecha_examen

    # Preparar datos para la plantilla
    mesa = {
        'materia': materia,
        'fecha_examen': fecha_examen.strftime('%Y-%m-%d %H:%M') if isinstance(fecha_examen, datetime) else fecha_examen,
        'profesor': profesor,
        'suplente': suplente,
        'carrera': carrera,
        'turno': turno,
        'ano': ano,
        'localidad': localidad,
        'fecha_formateada': fecha_formateada
    }
    alumnos_list = [{'nombre': alumno[0], 'dni': alumno[1]} for alumno in alumnos]

    return render_template('finales/acta_volante.html', mesa=mesa, alumnos=alumnos_list)

#FINALES##FINALES##FINALES##FINALES##FINALES##FINALES##FINALES##FINALES##FINALES##FINALES##FINALES##FINALES##FINALES##FINALES##FINALES##FINALES##FINALES##FINALES##FINALES##FINALES##FINALES#





@app.route('/logout')
def logout():

    session.pop('nombre', None)
    session.pop('dni', None)

    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)