from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, id, nombre, usuario, rol, activo):
        self.id = id
        self.nombre = nombre
        self.usuario = usuario
        self.rol = rol
        self.activo = activo