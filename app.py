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

    # Obtener el número de página y la tabla seleccionada
    page = request.args.get('page', 1, type=int)
    table = request.args.get('table', 'alumnos')  # Por defecto será alumnos
    per_page = 5  # Número de registros por página
    offset = (page - 1) * per_page

    if table == 'alumnos':
        # Consulta paginada para la lista de alumnos
        query_alumnos = """
            SELECT id_usuario, dni, nombre_apellido, id_localidad, telefono
            FROM usuarios
            LIMIT %s OFFSET %s
        """
        alumnos = ejecutar_sql(query_alumnos, (per_page, offset))

        # Consulta para contar el total de alumnos
        query_total_alumnos = "SELECT COUNT(*) FROM usuarios"
        total_alumnos = ejecutar_sql(query_total_alumnos)[0][0]

        # Calcular el número total de páginas para alumnos
        total_paginas_alumnos = (total_alumnos + per_page - 1) // per_page

        return render_template(
            'alumnos.html', 
            alumnos=alumnos, 
            pre_inscripciones=[],  # No mostrar pre-inscripciones en esta vista
            page=page, 
            table='alumnos',
            total_paginas_alumnos=total_paginas_alumnos, 
            total_paginas_pre_inscripciones=None  # No se necesitan para alumnos
        )

    elif table == 'pre_inscripciones':
        # Consulta paginada para la lista de pre-inscripciones
        query_pre_inscripciones = """
            SELECT id_usuario, dni, nombre_apellido, id_localidad, telefono
            FROM pre_inscripciones
            LIMIT %s OFFSET %s
        """
        pre_inscripciones = ejecutar_sql(query_pre_inscripciones, (per_page, offset))

        # Consulta para contar el total de pre-inscripciones
        query_total_pre_inscripciones = "SELECT COUNT(*) FROM pre_inscripciones"
        total_pre_inscripciones = ejecutar_sql(query_total_pre_inscripciones)[0][0]

        # Calcular el número total de páginas para pre-inscripciones
        total_paginas_pre_inscripciones = (total_pre_inscripciones + per_page - 1) // per_page

        return render_template(
            'alumnos.html', 
            alumnos=[],  # No mostrar alumnos en esta vista
            pre_inscripciones=pre_inscripciones,
            page=page, 
            table='pre_inscripciones',
            total_paginas_alumnos=None,  # No se necesitan para pre-inscripciones
            total_paginas_pre_inscripciones=total_paginas_pre_inscripciones
        )


@app.route('/alumno/<int:id_usuario>', methods=['GET', 'POST'])
def editar_alumno(id_usuario):
    if 'nombre' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Recibir datos actualizados desde el formulario y actualizar en la base de datos
        datos = request.form.to_dict()
        # Normalizar campos que pueden ser nulos
        datos['lugar_nacimiento'] = datos['lugar_nacimiento'] if datos['lugar_nacimiento'] else None
        datos['telefono_alt'] = datos['telefono_alt'] if datos['telefono_alt'] else None
        datos['telefono_alt_propietario'] = datos['telefono_alt_propietario'] if datos['telefono_alt_propietario'] else None
        datos['titulo_base'] = datos['titulo_base'] if datos['titulo_base'] else None
        datos['anio_egreso_otros'] = datos['anio_egreso_otros'] if datos['anio_egreso_otros'] else None
        datos['actividad'] = datos['actividad'] if datos['actividad'] else None
        datos['horario_habitual'] = datos['horario_habitual'] if datos['horario_habitual'] else None
        datos['obra_social'] = datos['obra_social'] if datos['obra_social'] else None
        datos['piso'] = datos['piso'] if datos['piso'] and datos['piso'] != 'NULL' else None
        
        query_update = """
            UPDATE usuarios SET 
                nombre_apellido = %s, id_sexo = %s, fecha_nacimiento = %s, lugar_nacimiento = %s, 
                id_estado_civil = %s, cantidad_hijos = %s, familiares_a_cargo = %s, domicilio = %s, 
                piso = %s, id_localidad = %s, id_pais = %s, id_provincia = %s, codigo_postal = %s, 
                telefono = %s, telefono_alt = %s, telefono_alt_propietario = %s, email = %s, 
                titulo_base = %s, anio_egreso = %s, id_institucion = %s, otros_estudios = %s, 
                anio_egreso_otros = %s, trabaja = %s, actividad = %s, horario_habitual = %s, 
                obra_social = %s
            WHERE id_usuario = %s
        """
        
        ejecutar_sql(query_update, (
            datos['nombre_apellido'], datos['id_sexo'], datos['fecha_nacimiento'], datos['lugar_nacimiento'],
            datos['id_estado_civil'], datos['cantidad_hijos'], datos['familiares_a_cargo'], datos['domicilio'],
            datos['piso'], datos['id_localidad'], datos['id_pais'], datos['id_provincia'], datos['codigo_postal'],
            datos['telefono'], datos['telefono_alt'], datos['telefono_alt_propietario'], datos['email'],
            datos['titulo_base'], datos['anio_egreso'], datos['id_institucion'], datos['otros_estudios'],
            datos['anio_egreso_otros'], datos['trabaja'], datos['actividad'], datos['horario_habitual'],
            datos['obra_social'], id_usuario
        ))

        return redirect(url_for('alumnos'))

    # Si es una solicitud GET, obtener los datos del alumno para editar
    query_alumno = "SELECT * FROM usuarios WHERE id_usuario = %s"
    alumno = ejecutar_sql(query_alumno, (id_usuario,))[0]  # Obtener el primer resultado
    print (alumno)
    return render_template('editar_alumno.html', alumno=alumno)


@app.route('/alumno/<int:id_usuario>/borrar', methods=['POST'])
def borrar_alumno(id_usuario):
    if 'nombre' not in session:
        return redirect(url_for('login'))

    # Consulta para eliminar al alumno de la base de datos
    query_borrar = " UPDATE usuarios SET activo = 0 WHERE id_usuario = %s"
    ejecutar_sql(query_borrar, (id_usuario,))
    
    return redirect(url_for('alumnos'))

@app.route('/ingresante/<int:id_usuario>', methods=['GET', 'POST'])
def editar_ingresante(id_usuario):
    if 'nombre' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Recibir datos actualizados desde el formulario y convertir a diccionario
        datos = request.form.to_dict()
        # Normalizar campos que pueden ser nulos
        datos['lugar_nacimiento'] = datos['lugar_nacimiento'] or None
        datos['telefono_alt'] = datos['telefono_alt'] or None
        datos['telefono_alt_propietario'] = datos['telefono_alt_propietario'] or None
        datos['titulo_base'] = datos['titulo_base'] or None
        datos['titulo_base'] = datos['titulo_base'] or None
        datos['anio_egreso_otros'] = datos['anio_egreso_otros'] or None
        datos['actividad'] = datos['actividad'] or None
        datos['horario_habitual'] = datos['horario_habitual'] or None
        datos['obra_social'] = datos['obra_social'] or None
        datos['anio_egreso_otros'] = datos['anio_egreso_otros'] or None
        datos['piso'] = datos['piso'] if datos['piso'] != 'NULL' else None
        query_insert = """
            INSERT INTO usuarios (
                dni, nombre_apellido, id_sexo, fecha_nacimiento, lugar_nacimiento,
                id_estado_civil, cantidad_hijos, familiares_a_cargo, domicilio, piso, id_localidad,
                id_pais, id_provincia, codigo_postal, telefono, telefono_alt, telefono_alt_propietario,
                email, titulo_base, anio_egreso, id_institucion, otros_estudios, anio_egreso_otros,
                trabaja, actividad, horario_habitual, obra_social, pass, activo
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """

        # Ejecutar la consulta
        ejecutar_sql(query_insert, (
            datos['dni'], datos['nombre_apellido'], datos['id_sexo'], datos['fecha_nacimiento'],
            datos['lugar_nacimiento'], datos['id_estado_civil'], datos['cantidad_hijos'], datos['familiares_a_cargo'],
            datos['domicilio'], datos['piso'], datos['id_localidad'], datos['id_pais'], datos['id_provincia'],
            datos['codigo_postal'], datos['telefono'], datos['telefono_alt'], datos['telefono_alt_propietario'],
            datos['email'], datos['titulo_base'], datos['anio_egreso'], datos['id_institucion'],
            datos['otros_estudios'], datos['anio_egreso_otros'], datos['trabaja'], datos['actividad'],
            datos['horario_habitual'], datos['obra_social'], 12345678, 1
        ))

        # Consulta para eliminar el ingresante de la tabla `pre_inscripciones` después de ser trasladado
        query_delete = "DELETE FROM pre_inscripciones WHERE id_usuario = %s"
        ejecutar_sql(query_delete, (id_usuario,))

        return redirect(url_for('alumnos'))

    # Si es una solicitud GET, obtener los datos del ingresante para editar
    query_ingresante = "SELECT * FROM pre_inscripciones WHERE id_usuario = %s"
    ingresante = ejecutar_sql(query_ingresante, (id_usuario,))[0]  # Obtener el primer resultado
    print (ingresante)
    
    return render_template('editar_ingresante.html', alumno=ingresante)



@app.route('/ingresante/<int:id_usuario>/borrar', methods=['POST'])
def borrar_ingresante(id_usuario):
    if 'nombre' not in session:
        return redirect(url_for('login'))

    # Consulta para eliminar al ingresante de la base de datos
    query_borrar = "DELETE FROM pre_inscripciones WHERE id_usuario = %s"
    ejecutar_sql(query_borrar, (id_usuario,))
    
    return redirect(url_for('alumnos'))

    
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
    
    # Consultar los países y las provincias
    query_paises = "SELECT id_pais, nombre FROM paises"
    paises = ejecutar_sql(query_paises)

    query_provincias = "SELECT id_provincia, nombre, id_pais FROM provincias"
    provincias = ejecutar_sql(query_provincias)

    return render_template('pre_inscripcion.html', paises=paises, provincias=provincias)



@app.route('/pre_inscripcion_2', methods=['POST'])
def pre_inscripcion_2():
    if 'nombre' not in session:
        return redirect(url_for('login'))

    # Recibir los datos del formulario anterior
    datos_personales = request.form.to_dict()
    
    # Guardar en la sesión para usarlos más adelante
    session['datos_personales'] = datos_personales

    # Aquí obtienes el país seleccionado previamente (lo que corresponde a Argentina o no)
    id_pais_estudio = int(datos_personales['id_pais'])

    query_provincias = "SELECT id_provincia, id_pais, nombre FROM provincias"
    provincias = ejecutar_sql(query_provincias)
    # Pasar el ID del país al template de pre_inscripcion_2
    return render_template('pre_inscripcion_2.html', id_pais_estudio=id_pais_estudio, provincias=provincias)


@app.route('/guardar_pre_inscripcion', methods=['POST'])
def guardar_pre_inscripcion():
    # Verificar si el usuario está autenticado

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
    trabaja = datos.get('trabaja')  # Asumimos que '2' significa que no trabaja si no está presente
    actividad = datos.get('actividad', '') if trabaja == 'si' else None
    horario_habitual = datos.get('horario_habitual', '') if trabaja == 'si' else None
    obra_social = datos.get('obra_social', '') if trabaja == 'si' else None

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
        datos['otros_estudios'], datos['anio_egreso_otros'], trabaja,
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

    # Consultar los países y las provincias
    query_paises = "SELECT id_pais, nombre FROM paises"
    paises = ejecutar_sql(query_paises)

    query_provincias = "SELECT id_provincia, nombre, id_pais FROM provincias"
    provincias = ejecutar_sql(query_provincias)

    return render_template('inscribite.html', paises=paises, provincias=provincias)


@app.route('/inscribite_2', methods=['POST'])
def inscribite_2():
    # Recibir los datos del formulario anterior
    datos_personales = request.form.to_dict()
    
    # Guardar en la sesión para usarlos más adelante
    session['datos_personales'] = datos_personales

    # Aquí obtienes el país seleccionado previamente (lo que corresponde a Argentina o no)
    id_pais_estudio = int(datos_personales['id_pais'])

    query_provincias = "SELECT id_provincia, id_pais, nombre FROM provincias"
    provincias = ejecutar_sql(query_provincias)
    # Pasar el ID del país al template de pre_inscripcion_2
    return render_template('inscribite_2.html', id_pais_estudio=id_pais_estudio, provincias=provincias)

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