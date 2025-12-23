import sqlite3
import os
from config import Config

def limpiar_base_de_datos():
    """
    Elimina todos los registros de las tablas 'servicios' e 'historial'
    y reinicia los contadores de autoincremento para empezar desde el ID 1.
    """
    db_path = Config.DATABASE_PATH
    
    if not os.path.exists(db_path):
        print(f"Error: La base de datos no se encontró en la ruta: {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("Eliminando datos de la tabla 'historial'...")
        cursor.execute("DELETE FROM historial;")
        
        print("Eliminando datos de la tabla 'servicios'...")
        cursor.execute("DELETE FROM servicios;")

        print("Reiniciando contadores de ID para 'servicios' e 'historial'...")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name = 'servicios';")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name = 'historial';")

        conn.commit()
        print("\n¡Limpieza completada con éxito!")
        print("Se han eliminado todos los datos de servicios y su historial. Los nuevos registros comenzarán desde el ID 1.")

    except sqlite3.Error as e:
        print(f"Ocurrió un error de base de datos: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    confirmacion = input("¿Estás seguro de que deseas eliminar TODOS los datos de servicios y su historial? (escribe 'si' para confirmar): ")
    if confirmacion.lower() == 'si':
        limpiar_base_de_datos()
    else:
        print("Operación cancelada.")