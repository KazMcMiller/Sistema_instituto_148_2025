# Importar el controlador de autenticación para que esté disponible cuando importemos el módulo controllers
from .auth_controller import AuthController

# Si hay otros controladores, podemos importarlos aquí
# from .alumno_controller import AlumnoController
# from .profesor_controller import ProfesorController

# Definir las clases o funciones que serán accesibles directamente
__all__ = ['AuthController']
