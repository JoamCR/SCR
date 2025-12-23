from flask import Blueprint, render_template
from flask_login import login_required
from db import DatabaseSingleton
from config import cache  # Importar cache desde config.py

reportes_bp = Blueprint('reportes', __name__, template_folder='../../templates')
db = DatabaseSingleton()

@reportes_bp.route('/')
@login_required
@cache.cached(timeout=60)  # Cachear por 60 segundos
def reportes():
    servicios = db.query("SELECT servicio, COUNT(*) as count FROM servicios GROUP BY servicio")
    notas = db.query("SELECT notas, COUNT(*) as count FROM servicios WHERE notas IS NOT NULL GROUP BY notas")
    return render_template('reportes.html', servicios=servicios, notas=notas)