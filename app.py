from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_session import Session
from dotenv import load_dotenv
from utils.db_utils import ejecutar_sql
import json
from functools import wraps
from flask import jsonify
from io import BytesIO
from flask import send_file
import openpyxl
from openpyxl import Workbook
from openpyxl.styles import Font
from datetime import date, datetime, timedelta


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
def alumnos():
    if 'nombre' not in session:
        return redirect(url_for('login'))

    # Obtener el nombre de búsqueda, número de página, estado activo y tabla seleccionada
    nombre_busqueda = request.args.get('nombre', '').strip()  # Nombre a buscar
    estado_activo = request.args.get('activo', 'todos')  # Estado activo: 'todos', 'activos' o 'inactivos'
    page = request.args.get('page', 1, type=int)
    table = request.args.get('table', 'alumnos')
    per_page = 5
    offset = (page - 1) * per_page

    # Construir condiciones de búsqueda y filtro
    nombre_filter = f"%{nombre_busqueda}%"
    activo_filter = None if estado_activo == 'todos' else ('1' if estado_activo == 'activos' else '0')

    if table == 'alumnos':
        # Consulta de alumnos con filtro de nombre y estado
        query_alumnos = """
            SELECT u.id_usuario, u.dni, u.nombre, l.nombre AS localidad, u.telefono
            FROM usuarios u
            LEFT JOIN localidades l ON u.id_localidad = l.id_localidad
            WHERE u.nombre LIKE %s
        """
        params = [nombre_filter]

        if activo_filter is not None:
            query_alumnos += " AND u.activo = %s"
            params.append(activo_filter)

        query_alumnos += " ORDER BY u.id_usuario LIMIT %s OFFSET %s"
        params.extend([per_page, offset])

        alumnos = ejecutar_sql(query_alumnos, tuple(params))

        # Contar el total de alumnos según el filtro de búsqueda y estado
        query_total_alumnos = "SELECT COUNT(*) FROM usuarios WHERE nombre LIKE %s"
        total_params = [nombre_filter]

        if activo_filter is not None:
            query_total_alumnos += " AND activo = %s"
            total_params.append(activo_filter)

        total_alumnos = ejecutar_sql(query_total_alumnos, tuple(total_params))[0][0]
        total_paginas_alumnos = (total_alumnos + per_page - 1) // per_page

        return render_template(
            'alumnos.html', 
            alumnos=alumnos,
            pre_inscripciones=[],
            page=page,
            table='alumnos',
            nombre_busqueda=nombre_busqueda,
            estado_activo=estado_activo,
            total_paginas_alumnos=total_paginas_alumnos,
            total_paginas_pre_inscripciones=None
        )

    elif table == 'pre_inscripciones':
        # Consulta de pre-inscripciones con filtro de nombre y estado
        query_pre_inscripciones = """
            SELECT u.id_usuario, u.dni, u.nombre, l.nombre AS localidad, u.telefono
            FROM pre_inscripciones u
            LEFT JOIN localidades l ON u.id_localidad = l.id_localidad
            WHERE u.nombre LIKE %s
        """
        params = [nombre_filter]

        if activo_filter is not None:
            query_pre_inscripciones += " AND u.activo = %s"
            params.append(activo_filter)

        query_pre_inscripciones += " ORDER BY u.id_usuario LIMIT %s OFFSET %s"
        params.extend([per_page, offset])

        pre_inscripciones = ejecutar_sql(query_pre_inscripciones, tuple(params))

        # Contar el total de pre-inscripciones según el filtro de búsqueda y estado
        query_total_pre_inscripciones = "SELECT COUNT(*) FROM pre_inscripciones WHERE nombre LIKE %s"
        total_params = [nombre_filter]

        if activo_filter is not None:
            query_total_pre_inscripciones += " AND activo = %s"
            total_params.append(activo_filter)

        total_pre_inscripciones = ejecutar_sql(query_total_pre_inscripciones, tuple(total_params))[0][0]
        total_paginas_pre_inscripciones = (total_pre_inscripciones + per_page - 1) // per_page

        return render_template(
            'alumnos.html',
            alumnos=[],
            pre_inscripciones=pre_inscripciones,
            page=page,
            table='pre_inscripciones',
            nombre_busqueda=nombre_busqueda,
            estado_activo=estado_activo,
            total_paginas_alumnos=None,
            total_paginas_pre_inscripciones=total_paginas_pre_inscripciones
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

    
@app.route('/profesores')
@perfil_requerido(['1', '2', '3'])  # Solo perfiles 1 (directivo) y 3 (profesor) pueden acceder
def profesores():
    if 'nombre' not in session:
        return redirect(url_for('login'))
    # Renderiza la página de gestión de profesores
    return render_template('profesores.html')

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
@perfil_requerido(['1', '2'])
def pre_inscripcion():
    if 'nombre' not in session:
        return redirect(url_for('login'))

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

        if existe_dni > 0: #si existe, volver a enviar los datos y recargar la pagina, dando un mensaje de error
            return render_template(
                'pre_inscripcion.html',
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
        return redirect(url_for('pre_inscripcion_2'))

    # Renderizar la página sin mensaje de error al cargar por primera vez (GET)
    return render_template(
        'pre_inscripcion.html',
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

#sigue el formulario y guarda todo para pre_inscripcion_3
@app.route('/pre_inscripcion_2', methods=['GET', 'POST'])
@perfil_requerido(['1', '2'])
def pre_inscripcion_2():
    if 'nombre' not in session:
        return redirect(url_for('login'))

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
        'pre_inscripcion_2.html',
        id_pais_estudio=id_pais_estudio,
        provincias=provincias,
    )

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
    
@app.route('/mesas_disponibles', methods=['GET', 'POST'])
@perfil_requerido(['4'])
def mesas_disponibles():
    if 'id_usuario' not in session:
        flash('Error: Sesión no válida.', 'error')
        return redirect(url_for('login'))
    id_usuario = session['id_usuario']
    print(f"ID usuario: {id_usuario}, Accediendo a mesas disponibles")

    # Obtener materias aprobadas del usuario
    query_aprobadas = """
        SELECT id_materia
        FROM aprobaciones
        WHERE id_usuario = %s AND aprobada = 1
    """
    materias_aprobadas = [row[0] for row in ejecutar_sql(query_aprobadas, (id_usuario,)) or []]
    print(f"Materias aprobadas: {materias_aprobadas}")

    # Obtener mesas disponibles
    query_mesas = """
        SELECT DISTINCT f.id_mesa, m.nombre, f.fecha_examen, f.fecha_apertura, f.fecha_cierre,
                        p.nombre, p.apellido, p.dni_profesor,
                        COALESCE(im.intentos_restantes, 4) AS intentos_restantes
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
    print(f"Mesas disponibles: {mesas}")

    # Filtrar mesas por correlativas
    mesas_filtradas = []
    for mesa in mesas:
        id_mesa, nombre_materia, fecha_examen, fecha_apertura, fecha_cierre, nombre_profesor, apellido_profesor, dni_profesor, intentos_restantes = mesa
        # Verificar correlativas
        query_correlativas = """
            SELECT id_materia_correlativa
            FROM correlativas
            WHERE id_materia = (
                SELECT id_materia FROM mesas_f WHERE id_mesa = %s
            )
        """
        correlativas_requeridas = [row[0] for row in ejecutar_sql(query_correlativas, (id_mesa,)) or []]
        cumple_correlativas = all(corr in materias_aprobadas for corr in correlativas_requeridas)
        if cumple_correlativas:
            mesas_filtradas.append(mesa)
        else:
            print(f"Mesa {id_mesa} filtrada por falta de correlativas: {correlativas_requeridas}")

    if request.method == 'POST':
        id_mesa = request.form.get('id_mesa')
        print(f"Intentando inscribir en mesa: {id_mesa}")

        # Verificar si la mesa es válida
        query_mesa_valida = """
            SELECT f.id_mesa, m.id_materia
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

        # Verificar correlativas
        id_materia = mesa_valida[0][1]
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

        # Inscribir al usuario
        query_inscripcion = """
            INSERT INTO inscripcion_f (id_usuario, id_mesa, estado, fecha_inscripcion)
            VALUES (%s, %s, 'inscripto', NOW())
        """
        try:
            ejecutar_sql(query_inscripcion, (id_usuario, id_mesa))
            # Actualizar intentos
            query_intentos = """
                INSERT INTO intentos_materia (id_usuario, id_materia, intentos_restantes)
                VALUES (%s, %s, 4)
                ON DUPLICATE KEY UPDATE intentos_restantes = intentos_restantes - 1
            """
            ejecutar_sql(query_intentos, (id_usuario, id_materia))
            flash('Inscripción realizada con éxito.', 'success')
        except Exception as e:
            flash(f'Error al inscribir: {str(e)}', 'error')
        return redirect(url_for('mesas_disponibles'))

    return render_template('mesas_disponibles.html', mesas=mesas_filtradas)

@app.route('/inscribir_mesa/<int:id_mesa>', methods=['GET', 'POST'])
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


@app.route('/mesas_inscriptas', methods=['GET'])
@perfil_requerido(['4'])
def mesas_inscriptas():
    if 'id_usuario' not in session:
        flash('Error: Sesión no válida.', 'error')
        return redirect(url_for('login'))
    id_usuario = session['id_usuario']
    print(f"ID usuario: {id_usuario}, Accediendo a mesas inscriptas")

    query_inscriptos = """
        SELECT f.id_mesa, m.nombre, f.fecha_examen, ins.estado,
               COALESCE(im.intentos_restantes, 4) AS intentos_restantes,
               ins.id_inscripcion_final,
               p.nombre, p.apellido, p.dni_profesor
        FROM inscripcion_f ins
        JOIN mesas_f f ON ins.id_mesa = f.id_mesa
        JOIN materias m ON f.id_materia = m.id_materia
        JOIN profesores p ON f.dni_profesor = p.dni_profesor
        LEFT JOIN intentos_materia im ON m.id_materia = im.id_materia AND im.id_usuario = %s
        WHERE ins.id_usuario = %s AND ins.estado = 'inscripto'
        ORDER BY m.nombre ASC
    """
    inscriptos = ejecutar_sql(query_inscriptos, (id_usuario, id_usuario)) or []
    print(f"Inscriptos: {inscriptos}")
    if not inscriptos:
        flash('No estás inscripto en ninguna mesa.', 'info')

    return render_template('mesas_inscriptas.html', inscriptos=inscriptos)

@app.route('/cancelar_mesa/<int:id_inscripcion_final>', methods=['POST'])
@perfil_requerido(['4'])
def cancelar_mesa(id_inscripcion_final):
    if 'id_usuario' not in session:
        flash('Error: Sesión no válida.', 'error')
        return redirect(url_for('login'))
    id_usuario = session['id_usuario']
    now = datetime.now()
    print(f"ID usuario: {id_usuario}, Intentando cancelar inscripción: {id_inscripcion_final}")

    query_mesa = """
        SELECT f.fecha_examen, m.id_materia
        FROM inscripcion_f ins
        JOIN mesas_f f ON ins.id_mesa = f.id_mesa
        JOIN materias m ON f.id_materia = m.id_materia
        WHERE ins.id_inscripcion_final = %s AND ins.id_usuario = %s AND ins.estado = 'inscripto'
    """
    result = ejecutar_sql(query_mesa, (id_inscripcion_final, id_usuario))
    if not result:
        flash('Inscripción no encontrada o ya cancelada.', 'error')
        return redirect(url_for('mesas_inscriptas'))

    fecha_examen, id_materia = result[0]
    try:
        if now < fecha_examen - timedelta(hours=72):
            query_devolver = """
                UPDATE intentos_materia 
                SET intentos_restantes = LEAST(intentos_restantes + 1, 4)
                WHERE id_usuario = %s AND id_materia = %s
            """
            ejecutar_sql(query_devolver, (id_usuario, id_materia))

        query_cancelar = """
            UPDATE inscripcion_f 
            SET estado = 'cancelado' 
            WHERE id_inscripcion_final = %s AND id_usuario = %s
        """
        ejecutar_sql(query_cancelar, (id_inscripcion_final, id_usuario))
        flash('Inscripción cancelada con éxito.', 'success')
    except Exception as e:
        flash(f'Error al cancelar inscripción: {str(e)}', 'error')
    return redirect(url_for('mesas_inscriptas'))

@app.route('/crear_mesa', methods=['GET', 'POST'])
@perfil_requerido(['1', '2'])
def crear_mesa():
    if 'id_usuario' not in session:
        flash('Error: Sesión no válida.', 'error')
        return redirect(url_for('login'))
    id_usuario = session['id_usuario']
    print(f"ID usuario: {id_usuario}, Accediendo a crear mesa")

    if request.method == 'POST':
        id_materia = request.form.get('id_materia')
        fecha_examen = request.form.get('fecha_examen')
        fecha_apertura = request.form.get('fecha_apertura')
        fecha_cierre = request.form.get('fecha_cierre')
        dni_profesor = request.form.get('dni_profesor')
        dni_suplente = request.form.get('dni_suplente')

        # Validar datos
        try:
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

        # Validar que las fechas sean coherentes
        if fecha_apertura >= fecha_examen or fecha_cierre >= fecha_examen:
            flash('La fecha de apertura y cierre deben ser anteriores a la fecha del examen.', 'error')
            return redirect(url_for('crear_mesa'))
        if fecha_apertura >= fecha_cierre:
            flash('La fecha de apertura debe ser anterior a la fecha de cierre.', 'error')
            return redirect(url_for('crear_mesa'))

        # Verificar que la materia existe
        query_materia = """
            SELECT id_materia FROM materias WHERE id_materia = %s
        """
        materia = ejecutar_sql(query_materia, (id_materia,))
        if not materia:
            flash('La materia seleccionada no existe.', 'error')
            return redirect(url_for('crear_mesa'))

        # Verificar que los profesores existan
        query_profesor = """
            SELECT dni_profesor FROM profesores WHERE dni_profesor = %s
        """
        profesor = ejecutar_sql(query_profesor, (dni_profesor,))
        if not profesor:
            flash('El profesor titular no existe.', 'error')
            return redirect(url_for('crear_mesa'))

        if dni_suplente:
            suplente = ejecutar_sql(query_profesor, (dni_suplente,))
            if not suplente:
                flash('El profesor suplente no existe.', 'error')
                return redirect(url_for('crear_mesa'))

        # Generar id_mesa automáticamente
        query_id_mesa = """
            SELECT COALESCE(MAX(id_mesa), 0) + 1 AS next_id FROM mesas_f
        """
        result_id = ejecutar_sql(query_id_mesa)
        id_mesa = result_id[0][0] if result_id else 1

        # Insertar la mesa
        query_insert = """
            INSERT INTO mesas_f (id_mesa, id_materia, fecha_examen, fecha_apertura, fecha_cierre, dni_profesor, dni_suplente)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        params = (id_mesa, id_materia, fecha_examen, fecha_apertura, fecha_cierre, dni_profesor, dni_suplente)
        try:
            ejecutar_sql(query_insert, params)
            flash('Mesa creada con éxito.', 'success')
            return redirect(url_for('listar_mesas'))
        except Exception as e:
            print(f"Error al conectar a MySQL: {str(e)}")
            flash(f'Error al crear la mesa: {str(e)}', 'error')
            return redirect(url_for('crear_mesa'))

    # Obtener materias y profesores para el formulario, ordenadas alfabéticamente
    query_materias = """
        SELECT id_materia, nombre FROM materias WHERE id_carrera = 1 ORDER BY nombre
    """
    query_profesores = """
        SELECT dni_profesor, CONCAT(nombre, ' ', apellido) AS nombre_completo
        FROM profesores
        ORDER BY nombre, apellido
    """
    materias = ejecutar_sql(query_materias) or []
    profesores = ejecutar_sql(query_profesores) or []

    return render_template('crear_mesa.html', materias=materias, profesores=profesores)

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

    return render_template('listar_mesas.html', mesas=mesas)

@app.route('/eliminar_mesa/<int:id_mesa>', methods=['POST'])
@perfil_requerido(['1', '2'])
def eliminar_mesa(id_mesa):
    if 'id_usuario' not in session:
        flash('Error: Sesión no válida.', 'error')
        return redirect(url_for('login'))
    id_usuario = session['id_usuario']
    print(f"ID usuario: {id_usuario}")

    # Obtener id_materia de la mesa
    query_id_materia = """
        SELECT id_materia FROM mesas_f WHERE id_mesa = %s
    """
    id_materia_result = ejecutar_sql(query_id_materia, (id_mesa,))
    if not id_materia_result:
        flash('Mesa no encontrada.', 'error')
        return redirect(url_for('listar_mesas'))
    id_materia = id_materia_result[0][0]

    # Obtener inscripciones ligadas
    query_inscripciones = """
        SELECT id_usuario
        FROM inscripcion_f
        WHERE id_mesa = %s AND estado = 'inscripto'
    """
    inscripciones = ejecutar_sql(query_inscripciones, (id_mesa,))
    print(f"Inscripciones ligadas: {inscripciones}")

    # Devolver intentos para cada alumno inscripto
    for inscripcion in inscripciones:
        id_alumno = inscripcion[0]
        query_devolver = """
            UPDATE intentos_materia 
            SET intentos_restantes = intentos_restantes + 1 
            WHERE id_usuario = %s AND id_materia = %s
        """
        ejecutar_sql(query_devolver, (id_alumno, id_materia))
        print(f"Devolvido intento a alumno {id_alumno} para materia {id_materia}")

    # Eliminar inscripciones
    query_eliminar_inscripciones = """
        DELETE FROM inscripcion_f
        WHERE id_mesa = %s
    """
    ejecutar_sql(query_eliminar_inscripciones, (id_mesa,))
    print("Inscripciones eliminadas")

    # Eliminar la mesa
    query_eliminar = """
        DELETE FROM mesas_f
        WHERE id_mesa = %s
    """
    ejecutar_sql(query_eliminar, (id_mesa,))
    print("Mesa eliminada")

    # Verificar eliminación
    query_verificar = """
        SELECT id_mesa FROM mesas_f WHERE id_mesa = %s
    """
    verificado = ejecutar_sql(query_verificar, (id_mesa,))
    if not verificado:
        print("Mesa eliminada correctamente")
        flash('Mesa eliminada exitosamente. Inscripciones eliminadas y intentos devueltos.', 'success')
    else:
        print("Error: No se pudo eliminar la mesa")
        flash('Error al eliminar la mesa.', 'error')

    return redirect(url_for('listar_mesas'))


@app.route('/gestor_notas', methods=['GET', 'POST'])
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
                return render_template('gestor_notas.html', materias=[], profesores=profesores, dni_alumno=dni_alumno)

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
                return render_template('gestor_notas.html', materias=[], profesores=profesores, dni_alumno=dni_alumno)
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

            return render_template('gestor_notas.html', alumno_info=alumno_info, materias=materias, profesores=profesores, dni_alumno=dni_alumno)

        elif 'action' in request.form and request.form['action'] == 'aprobar':
            id_alumno = request.form.get('id_alumno')
            id_materia = request.form.get('id_materia')
            dni_profesor = request.form.get('dni_profesor')
            nota = request.form.get('nota')

            if not all([id_alumno, id_materia, dni_profesor, nota]):
                flash('Todos los campos son obligatorios.', 'error')
                return render_template('gestor_notas.html', materias=materias, profesores=profesores, dni_alumno=dni_alumno)

            # Validar nota
            try:
                nota = float(nota)
                if not 1 <= nota <= 10:
                    flash('La nota debe estar entre 1 y 10.', 'error')
                    return render_template('gestor_notas.html', materias=materias, profesores=profesores, dni_alumno=dni_alumno)
            except ValueError:
                flash('La nota debe ser un número válido.', 'error')
                return render_template('gestor_notas.html', materias=materias, profesores=profesores, dni_alumno=dni_alumno)

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

            return redirect(url_for('gestor_notas'))

    return render_template('gestor_notas.html', materias=materias, profesores=profesores)

@app.route('/acta_volante/<int:id_mesa>', methods=['GET'])
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
               YEAR(f.fecha_examen) AS ano, l.nombre AS localidad
        FROM mesas_f f
        JOIN materias m ON f.id_materia = m.id_materia
        JOIN profesores p ON f.dni_profesor = p.dni_profesor
        LEFT JOIN profesores ps ON f.dni_suplente = ps.dni_profesor
        JOIN lista_carreras lc ON m.id_carrera = lc.id_carrera
        JOIN institutos i ON lc.id_instituto = i.id_instituto
        JOIN localidades l ON i.id_localidad = l.id_localidad
        LEFT JOIN inscripciones_carreras ic ON m.id_carrera = ic.id_carrera
        LEFT JOIN turno_carrera tc ON ic.id_turno = tc.id_turno
        WHERE f.id_mesa = %s
        LIMIT 1
    """
    mesa_data = ejecutar_sql(query_mesa, (id_mesa,))
    if not mesa_data:
        flash('Mesa no encontrada o sin datos asociados.', 'error')
        return redirect(url_for('listar_mesas'))

    materia, fecha_examen, profesor, suplente, carrera, turno, ano, localidad = mesa_data[0]
    print(f"Datos mesa: materia={materia}, fecha_examen={fecha_examen}, profesor={profesor}, suplente={suplente}, carrera={carrera}, turno={turno}, localidad={localidad}")

    # Obtener alumnos inscriptos
    query_alumnos = """
        SELECT CONCAT(u.nombre, ' ', u.apellido) AS alumno, u.dni
        FROM inscripcion_f ins
        JOIN usuarios u ON ins.id_usuario = u.id_usuario
        WHERE ins.id_mesa = %s AND ins.estado = 'inscripto'
        ORDER BY u.apellido, u.nombre
    """
    alumnos = ejecutar_sql(query_alumnos, (id_mesa,))
    print(f"Alumnos inscriptos: {alumnos}")

    # Crear Excel con openpyxl
    wb = Workbook()
    ws = wb.active
    ws.title = "Acta Volante"

    # row1: ACTA VOLANTE DE EVALUACIONES
    ws['A1'] = "ACTA VOLANTE DE EVALUACIONES"
    ws['A1'].font = Font(bold=True, size=14)
    ws.merge_cells('A1:K1')

    # row2: Evaluaciones de alumnos Regulares
    ws['A2'] = "Evaluaciones de alumnos Regulares"
    ws.merge_cells('A2:K2')

    # row3: CARRERA: (CARRERA)
    ws['A3'] = "CARRERA:"
    ws['B3'] = carrera
    ws.merge_cells('B3:K3')

    # row4: Fecha en negrita
    ws['K4'] = fecha_examen.strftime('%Y-%m-%d %H:%M') if isinstance(fecha_examen, datetime) else fecha_examen
    ws['K4'].font = Font(bold=True)

    # row5: ASIGNATURA: (Materia), AÑO: (Año materia), TURNO: (turno carrera)
    ws['A5'] = "ASIGNATURA:"
    ws['B5'] = materia
    ws.merge_cells('B5:G5')
    ws['H5'] = "AÑO:"
    ws['I5'] = ano
    ws['J5'] = "TURNO:"
    ws['K5'] = turno if turno else "No especificado"

    # row7: Encabezados
    ws['A7'] = "N° de Orden"
    ws['B7'] = "Documento de Identidad"
    ws['C7'] = "Apellido y Nombres"
    ws.merge_cells('C7:H7')
    ws['I7'] = "Evaluaciones"
    ws['J7'] = ""
    ws['K7'] = "Observaciones"
    ws['I8'] = "En número"
    ws['J8'] = "En letras"

    # row9 a row23: Alumnos
    for idx, alumno in enumerate(alumnos, start=1):
        row = idx + 8
        ws[f'A{row}'] = idx
        ws[f'B{row}'] = alumno[1]  # DNI
        ws[f'C{row}'] = alumno[0].upper()  # Apellido y Nombres en mayúsculas
        ws.merge_cells(f'C{row}:H{row}')
        ws[f'I{row}'] = ""  # Nota en número (vacío)
        ws[f'J{row}'] = ""  # Nota en letras (vacío)
        ws[f'K{row}'] = ""  # Observaciones (vacío)

    # row26: PRESIDENTE, VOCAL, VOCAL
    ws['A26'] = f"PRESIDENTE: {profesor if profesor else '............................................................................'}"
    ws.merge_cells('A26:D26')
    ws['E26'] = f"VOCAL: {suplente if suplente else '..................................................................'}"
    ws.merge_cells('E26:G26')
    ws['H26'] = "VOCAL:..................................................................."
    ws.merge_cells('H26:K26')

    # row28-31: Totales
    ws['K28'] = f"TOTAL ALUMNOS: {len(alumnos)}"
    ws['K29'] = "APROBADOS:........................................................"
    ws['K30'] = "APLAZADOS:........................................................"
    ws['K31'] = "AUSENTES:..........................................................."

    # row32: Localidad, día, mes, año
    mes_es = {
        'January': 'Enero', 'February': 'Febrero', 'March': 'Marzo', 'April': 'Abril',
        'May': 'Mayo', 'June': 'Junio', 'July': 'Julio', 'August': 'Agosto',
        'September': 'Septiembre', 'October': 'Octubre', 'November': 'Noviembre', 'December': 'Diciembre'
    }
    ws['A32'] = f"{localidad}, {fecha_examen.day} de {mes_es[fecha_examen.strftime('%B')]} de {fecha_examen.year}"
    ws.merge_cells('A32:K32')

    # Ajustar ancho de columnas
    ws.column_dimensions['A'].width = 10
    ws.column_dimensions['B'].width = 15
    ws.column_dimensions['C'].width = 40
    ws.column_dimensions['I'].width = 12
    ws.column_dimensions['J'].width = 15
    ws.column_dimensions['K'].width = 20

    # Guardar en buffer y descargar
    output = BytesIO()
    wb.save(output)
    output.seek(0)

    filename = f"acta_volante_mesa_{id_mesa}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        download_name=filename,
        as_attachment=True
    )

@app.route('/logout')
def logout():

    session.pop('nombre', None)
    session.pop('dni', None)

    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)

    
