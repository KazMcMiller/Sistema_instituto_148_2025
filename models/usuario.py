import os
from utils.db_utils import ejecutar_sql

class Usuario:
    def __init__(self, id_usuario, dni, nombre):
        self.id_usuario = id_usuario
        self.dni = dni
        self.nombre = nombre

    @classmethod
    def autenticar(cls, dni, password):
        # Autenticar al usuario contra la base de datos
        query = "SELECT * FROM usuarios WHERE dni = %s AND pass = %s"
        result = ejecutar_sql(query, (dni, password))
        
        if result:
            id_usuario = result[0][0]  # Suponiendo que el ID del usuario está en la primera columna
            nombre = result[0][2]  # Suponiendo que el nombre está en la tercera columna
            return cls(id_usuario, dni, nombre)
        return None

    def obtener_perfiles(self):
        # Obtener los perfiles asociados al usuario
        query = "SELECT id_perfil FROM perfiles_usuarios WHERE id_usuarios = %s"
        perfiles = ejecutar_sql(query, (self.id_usuario,))
        return [perfil[0] for perfil in perfiles]

    def es_perfil_multiplo(self):
        # Verificar si el usuario tiene el perfil múltiple (id_perfil = 1)
        return 1 in self.obtener_perfiles()

    def tiene_perfil(self, id_perfil):
        # Verificar si el usuario tiene un perfil específico
        return id_perfil in self.obtener_perfiles()
