from flask import Flask
from flask_login import LoginManager
from modules.public.routes import public_bp
from modules.tecnico.routes import tecnico_bp
from modules.admin.routes import admin_bp
from modules.reportes.routes import reportes_bp
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'tecnico.login'

@login_manager.user_loader
def load_user(user_id):
    from db import DatabaseSingleton
    db = DatabaseSingleton()
    user_data = db.query("SELECT * FROM usuarios WHERE id = ? AND activo = 1", (user_id,))
    if user_data:
        from models import User
        return User(user_data[0]['id'], user_data[0]['nombre'], user_data[0]['usuario'], user_data[0]['rol'], user_data[0]['activo'])
    return None

# Registrar blueprints
app.register_blueprint(public_bp, url_prefix='/')
app.register_blueprint(tecnico_bp, url_prefix='/tecnico')
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(reportes_bp, url_prefix='/reportes')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')