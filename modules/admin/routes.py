from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from db import DatabaseSingleton
import bcrypt
import re

admin_bp = Blueprint('admin', __name__, template_folder='../../templates')
db = DatabaseSingleton()

@admin_bp.route('/usuarios', methods=['GET', 'POST'])
@login_required
def usuarios():
    if current_user.rol != 'Administrador':
        flash("Acceso denegado", "error")
        return redirect(url_for('tecnico.panel'))
    
    if request.method == 'POST':
        try:
            nombre = request.form['nombre'].strip()
            usuario = request.form['usuario'].strip()
            contraseña = request.form['contraseña'].encode('utf-8')
            rol = request.form['rol']
            
            if not all([nombre, usuario, contraseña]):
                raise ValueError("Todos los campos son obligatorios")
            if not re.match(r'^[a-zA-Z0-9_]{4,20}$', usuario):
                raise ValueError("Usuario debe tener entre 4 y 20 caracteres alfanuméricos")
            if len(contraseña) < 8:
                raise ValueError("La contraseña debe tener al menos 8 caracteres")
            if rol not in ['Técnico', 'Administrador']:
                raise ValueError("Rol inválido")
            
            contraseña_hash = bcrypt.hashpw(contraseña, bcrypt.gensalt())
            db.execute("INSERT INTO usuarios (nombre, usuario, contraseña, rol) VALUES (?, ?, ?, ?)",
                       (nombre, usuario, contraseña_hash, rol))
            flash("Usuario creado con éxito", "success")
        except ValueError as ve:
            flash(f"Error de validación: {str(ve)}", "error")
        except Exception as e:
            flash(f"Error al crear usuario: {str(e)}", "error")
        return redirect(url_for('admin.usuarios'))
    
    usuarios = db.query("SELECT * FROM usuarios")
    return render_template('usuarios.html', usuarios=usuarios)

@admin_bp.route('/desactivar/<int:id>', methods=['POST'])
@login_required
def desactivar(id):
    if current_user.rol != 'Administrador':
        flash("Acceso denegado", "error")
        return redirect(url_for('tecnico.panel'))
    try:
        db.execute("UPDATE usuarios SET activo = 0 WHERE id = ?", (id,))
        flash("Usuario desactivado con éxito", "success")
    except Exception as e:
        flash(f"Error al desactivar usuario: {str(e)}", "error")
    return redirect(url_for('admin.usuarios'))