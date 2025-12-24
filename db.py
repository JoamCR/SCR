import sqlite3
from config import Config

class DatabaseSingleton:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.conn = sqlite3.connect(Config.DATABASE_PATH, check_same_thread=False)
            cls._instance.conn.row_factory = sqlite3.Row
            cls._instance.init_db()
        return cls._instance
    
    def init_db(self):
        try:
            cursor = self.conn.cursor()
            cursor.executescript('''
                CREATE TABLE IF NOT EXISTS servicios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    primer_apellido TEXT NOT NULL,
                    segundo_apellido TEXT NOT NULL,
                    telefono TEXT NOT NULL,
                    tipo_equipo TEXT NOT NULL,
                    marca TEXT NOT NULL,
                    modelo TEXT NOT NULL,
                    serie TEXT,
                    servicio TEXT,
                    accesorios TEXT,
                    estado TEXT DEFAULT 'En diagnóstico',
                    notas TEXT,
                    foto_inicial TEXT,
                    foto_servicio TEXT,
                    foto_final TEXT,
                    fecha_registro TEXT,
                    fecha_entrega TEXT,
                    tecnico_actual TEXT
                );

                CREATE TABLE IF NOT EXISTS historial (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    servicio_id INTEGER,
                    tecnico TEXT,
                    fecha_cambio TEXT,
                    estado TEXT,
                    notas TEXT,
                    FOREIGN KEY (servicio_id) REFERENCES servicios(id)
                );

                CREATE TABLE IF NOT EXISTS notas_servicio (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    servicio_id INTEGER,
                    nota TEXT,
                    fecha TEXT,
                    usuario TEXT,
                    FOREIGN KEY (servicio_id) REFERENCES servicios(id)
                );

                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    usuario TEXT NOT NULL UNIQUE,
                    contraseña TEXT NOT NULL,
                    rol TEXT NOT NULL,
                    activo INTEGER DEFAULT 1 CHECK (activo IN (0, 1))
                );
            ''')
            # Crear índices para optimizar consultas
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_servicio ON servicios(servicio)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_notas ON servicios(notas)')
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error al inicializar la base de datos: {str(e)}")
            raise

    def query(self, sql, params=()):
        cursor = self.conn.cursor()
        cursor.execute(sql, params)
        result = cursor.fetchall()
        cursor.close()
        return result

    def execute(self, sql, params=()):
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, params)
            self.conn.commit()
            cursor.close()
        except sqlite3.Error as e:
            print(f"Error al ejecutar SQL: {str(e)}")
            raise