from db import DatabaseSingleton
import bcrypt

# Inicializa la base de datos
db = DatabaseSingleton()

# Datos del usuario
nombre = "admin"
usuario = "admin"
contraseña_plana = "admin012345"  # Contraseña en texto plano
rol = "Administrador"
activo = 1

# Genera el hash de la contraseña
contraseña_hash = bcrypt.hashpw(contraseña_plana.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# Inserta el usuario en la base de datos
db.execute("""
    INSERT INTO usuarios (nombre, usuario, contraseña, rol, activo)
    VALUES (?, ?, ?, ?, ?)
""", (nombre, usuario, contraseña_hash, rol, activo))

print(f"Usuario '{usuario}' creado con éxito. Contraseña: {contraseña_plana}")