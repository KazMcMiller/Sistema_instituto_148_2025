import os
import mysql.connector
from mysql.connector import Error

def ejecutar_sql(sentencia_sql, params=None):
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASS'),
            database=os.getenv('DB_DATABASE')
        )
        if connection.is_connected():
            db_info = connection.get_server_info()
            cursor = connection.cursor()
            cursor.execute(sentencia_sql, params)
            if sentencia_sql.strip().lower().startswith("select"):
                resultado = cursor.fetchall()
                return resultado
            else:
                connection.commit()
                return None
    except Error as e:
        print("Error al conectar a MySQL", e)
        return None
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()