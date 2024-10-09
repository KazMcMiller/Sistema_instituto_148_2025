from flask import render_template, request, redirect, url_for, session
from models.usuario import Usuario
class AuthController:
    @staticmethod
    def login():
        if request.method == 'POST':
            dni = request.form['dni']
            password = request.form['password']

            usuario = Usuario.autenticar(dni, password)

            if usuario:
                session['dni'] = usuario.dni
                session['nombre'] = usuario.nombre

                # Verificar si el usuario tiene un perfil múltiple
                if usuario.es_perfil_multiplo():
                    return redirect(url_for('seleccionar_perfil'))

                # Redirigir según el perfil único
                elif usuario.tiene_perfil(2):  # 2: Alumno
                    return redirect(url_for('dashboard_alumno'))
                elif usuario.tiene_perfil(3):  # 3: Administrador
                    return redirect(url_for('dashboard_admin'))
                else:
                    return "Perfil de usuario no válido"
            else:
                return "DNI o contraseña incorrectos"
        
        return render_template('login.html')

    @staticmethod
    def logout():
        session.pop('nombre', None)
        session.pop('dni', None)
        return redirect(url_for('login'))
