from flask_caching import Cache

class Config:
    SECRET_KEY = 'clave_secreta_taller'  # Cambiar en producción
    DATABASE_PATH = 'db/taller.db'
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB límite para fotos
    CACHE_TYPE = 'SimpleCache'  # Configuración para flask-caching

# Inicializar cache (será configurado con la app en app.py)
cache = Cache()