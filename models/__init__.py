# Importar la clase Usuario para que esté disponible cuando importemos el módulo models
from .usuario import Usuario

# Si hay otros modelos, podríamos importarlos aquí también
# from .alumno import Alumno
# from .profesor import Profesor

# Podemos definir una lista de clases que queremos que sean accesibles directamente
__all__ = ['Usuario']
