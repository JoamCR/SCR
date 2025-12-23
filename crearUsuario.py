import sqlite3
import bcrypt # Importar bcrypt para hashing seguro
from db import DatabaseSingleton

def create_admin_user():
    """
    Crea un usuario administrador en la base de datos.
    """
    print("--- Creación de Usuario Administrador ---")
    
    # --- DATOS DEL ADMINISTRADOR ---
    # Puedes cambiar estos valores si lo deseas
    nombre = "Administrador"
    usuario = "administrador"
    contraseña_plana = "admin123" # ¡IMPORTANTE! Cambia esta contraseña por una más segura
    rol = "Administrador"
    
    # --- HASHING DE CONTRASEÑA con bcrypt ---
    contraseña_hash = bcrypt.hashpw(contraseña_plana.encode('utf-8'), bcrypt.gensalt())
    
    try:
        # Obtenemos la instancia de la base de datos
        db = DatabaseSingleton()
        
        # Verificamos si el usuario ya existe
        existe = db.query("SELECT id FROM usuarios WHERE usuario = ?", (usuario,))
        if existe:
            print(f"El usuario '{usuario}' ya existe. No se ha creado un nuevo usuario.")
            return

        # Creamos la consulta SQL para insertar el nuevo usuario
        sql = "INSERT INTO usuarios (nombre, usuario, contraseña, rol, activo) VALUES (?, ?, ?, ?, ?)"
        params = (nombre, usuario, contraseña_hash, rol, 1) # Añadir activo=1
        
        # Ejecutamos la consulta
        db.execute(sql, params)
        
        print("\n¡Éxito!")
        print(f"Usuario administrador '{usuario}' creado correctamente.")
        print("-----------------------------------------")

    except sqlite3.Error as e:
        print(f"Error de base de datos al crear el usuario: {e}")
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")

if __name__ == '__main__':
    # Este bloque se ejecuta solo cuando corres el script directamente
    create_admin_user()
