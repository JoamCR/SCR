from flask import Blueprint, render_template
from flask_login import login_required
from db import DatabaseSingleton

reportes_bp = Blueprint('reportes', __name__, template_folder='../../templates')
db = DatabaseSingleton()

@reportes_bp.route('/')
@login_required
def reportes():
    servicios = db.query("SELECT servicio, COUNT(*) as count FROM servicios GROUP BY servicio")
    return render_template('reportes.html', servicios=servicios)