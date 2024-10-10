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
        return render_template('home.html', nombre=session['nombre'])
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
            
            # Obtener todos los perfiles asociados al usuario
            query_perfil = "SELECT id_perfil FROM perfiles_usuarios WHERE id_usuarios = %s"
            perfiles = ejecutar_sql(query_perfil, (result[0][0],))  # result[0][0] es el id_usuario

            # Convertir los perfiles en una lista de ids para facilitar la verificación
            perfil_ids = [perfil[0] for perfil in perfiles]

            # Si el usuario tiene el perfil múltiple (id_perfil = 1)
            if 1 in perfil_ids:
                return redirect(url_for('seleccionar_perfil'))

            # Si el usuario solo tiene el perfil de alumno (id_perfil = 2)
            elif 2 in perfil_ids and len(perfil_ids) == 1:
                return redirect(url_for('dashboard_alumno'))

            # Si el usuario solo tiene el perfil de administrador (id_perfil = 3)
            elif 3 in perfil_ids and len(perfil_ids) == 1:
                return redirect(url_for('dashboard_admin'))

            # Si el usuario tiene perfiles no válidos o una combinación inesperada
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
