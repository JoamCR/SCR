from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from db import DatabaseSingleton
from models import User
from config import Config, cache
import os
from datetime import datetime
import bcrypt
import re

tecnico_bp = Blueprint('tecnico', __name__, template_folder='../../templates')
db = DatabaseSingleton()

@tecnico_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo():
    from datetime import datetime
    if request.method == 'POST':
        try:
            nombre = request.form['nombre'].strip()
            primer_apellido = request.form['primer_apellido'].strip()
            segundo_apellido = request.form['segundo_apellido'].strip()
            telefono = request.form['telefono'].strip()
            tipo_equipo = request.form['tipo_equipo'].strip()
            marca = request.form['marca'].strip()
            modelo = request.form['modelo'].strip()
            serie = request.form.get('serie', '').strip()
            fecha_registro = request.form.get('fecha_registro', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

            servicios = request.form.getlist('servicio')
            if 'Otros' in servicios and request.form.get('otros_servicio'):
                otros = request.form['otros_servicio'].strip()
                if not otros:
                    raise ValueError("Especifique el servicio 'Otros'")
                servicios[servicios.index('Otros')] = f"Otros: {otros}"
            servicio_str = ', '.join(servicios) if servicios else 'Ninguno'

            accesorios = request.form.getlist('accesorios')
            if 'Otros' in accesorios and request.form.get('otros_accesorios'):
                otros_acc = request.form['otros_accesorios'].strip()
                if not otros_acc:
                    raise ValueError("Especifique el accesorio 'Otros'")
                accesorios[accesorios.index('Otros')] = f"Otros: {otros_acc}"
            accesorios_str = ', '.join(accesorios) if accesorios else 'Ninguno'

            notas = request.form.get('notas', '').strip()

            foto_inicial = request.files.get('foto_inicial')
            foto_inicial_path = None
            if foto_inicial and foto_inicial.filename:
                if not foto_inicial.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                    raise ValueError("Solo se permiten imágenes JPG o PNG para foto inicial")
                if not os.path.exists(Config.UPLOAD_FOLDER):
                    os.makedirs(Config.UPLOAD_FOLDER)
                if not os.access(Config.UPLOAD_FOLDER, os.W_OK):
                    raise PermissionError(f"No hay permisos de escritura en {Config.UPLOAD_FOLDER}")
                nombre_archivo = f"{nombre}_{datetime.now().strftime('%Y%m%d%H%M%S')}_inicial.jpg"
                foto_inicial.save(os.path.join(Config.UPLOAD_FOLDER, nombre_archivo))
                foto_inicial_path = nombre_archivo

            db.execute('''
                INSERT INTO servicios (nombre, primer_apellido, segundo_apellido, telefono, tipo_equipo, marca, modelo, serie, servicio, accesorios, estado, notas, foto_inicial, fecha_registro, tecnico_actual)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                nombre, primer_apellido, segundo_apellido, telefono, tipo_equipo, marca, modelo, serie, servicio_str, accesorios_str, 'En diagnóstico', notas, foto_inicial_path, fecha_registro, current_user.nombre
            ))
            flash("Servicio registrado con éxito", "success")
            return redirect(url_for('tecnico.panel'))
        except ValueError as ve:
            flash(f"Error de validación: {str(ve)}", "error")
        except Exception as e:
            flash(f"Error al registrar servicio: {str(e)}", "error")
    return render_template('nuevo.html', datetime=datetime)
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from db import DatabaseSingleton
from models import User
from config import Config, cache
import os
from datetime import datetime
import bcrypt
import re

tecnico_bp = Blueprint('tecnico', __name__, template_folder='../../templates')
db = DatabaseSingleton()

@tecnico_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            usuario = request.form['usuario'].strip()
            contraseña = request.form['contraseña'].encode('utf-8')
            if not usuario or not contraseña:
                raise ValueError("Usuario y contraseña son obligatorios")
            
            user_data = db.query("SELECT * FROM usuarios WHERE usuario = ? AND activo = 1", (usuario,))
            if not user_data:
                raise ValueError("Usuario no encontrado o inactivo")
            
            stored_password = user_data[0]['contraseña'] # La contraseña ya está en bytes desde la BD
            if bcrypt.checkpw(contraseña, stored_password):
                user = User(user_data[0]['id'], user_data[0]['nombre'], user_data[0]['usuario'], user_data[0]['rol'], user_data[0]['activo'])
                login_user(user)
                return redirect(url_for('index'))
            else:
                raise ValueError("Contraseña incorrecta")
        except ValueError as ve:
            flash(f"Error: {str(ve)}", "error")
        except Exception as e:
            flash(f"Error al iniciar sesión: {str(e)}", "error")
    return render_template('login.html')

@tecnico_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Sesión cerrada con éxito", "success")
    return redirect(url_for('index'))  # Redirigir al índice en lugar de '/login'

@tecnico_bp.route('/panel')
@login_required
def panel():
    fecha_registro = request.args.get('fecha_registro', '').strip()
    # Obtener parámetros de búsqueda y filtro
    buscar = request.args.get('buscar', '').strip()
    estado = request.args.get('estado', '').strip()
    tipo_equipo = request.args.get('tipo_equipo', '').strip()
    id_servicio = request.args.get('id_servicio', '').strip()
    cliente = request.args.get('cliente', '').strip()

    # Construir consulta dinámica
    query = "SELECT * FROM servicios WHERE 1=1"
    params = []
    if id_servicio:
        query += " AND id = ?"
        params.append(id_servicio)
    if cliente:
        query += " AND (nombre LIKE ? OR primer_apellido LIKE ? OR segundo_apellido LIKE ?)"
        cliente_param = f"%{cliente}%"
        params.extend([cliente_param]*3)
    if buscar:
        query += " AND (nombre LIKE ? OR primer_apellido LIKE ? OR segundo_apellido LIKE ? OR tipo_equipo LIKE ? OR marca LIKE ? OR modelo LIKE ? OR tecnico_actual LIKE ?)"
        buscar_param = f"%{buscar}%"
        params.extend([buscar_param]*7)
    if estado:
        query += " AND estado = ?"
        params.append(estado)
    if tipo_equipo and tipo_equipo != "":
        query += " AND tipo_equipo = ?"
        params.append(tipo_equipo)
    if fecha_registro:
        query += " AND date(fecha_registro) = ?"
        params.append(fecha_registro)
    query += " ORDER BY fecha_registro DESC"
    servicios = db.query(query, tuple(params))
    return render_template('panel.html', servicios=servicios)

@tecnico_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    servicio = db.query("SELECT * FROM servicios WHERE id = ?", (id,))
    if not servicio:
        flash("Servicio no encontrado", "error")
        return redirect(url_for('tecnico.panel'))
    servicio = servicio[0]

    if request.method == 'POST':
        try:
            estado = request.form['estado']
            if estado not in ['En diagnóstico', 'En reparación', 'Listo para entrega']:
                raise ValueError("Estado inválido")
            
            notas = request.form['notas'].strip()
            marca = request.form['marca'].strip()
            modelo = request.form['modelo'].strip()
            if not marca or not modelo:
                raise ValueError("Marca y Modelo son obligatorios")

            servicios = request.form.getlist('servicio')
            if 'Otros' in servicios and request.form.get('otros_servicio'):
                otros = request.form['otros_servicio'].strip()
                if not otros:
                    raise ValueError("Especifique el servicio 'Otros'")
                servicios[servicios.index('Otros')] = f"Otros: {otros}"
            servicio_str = ', '.join(servicios) if servicios else 'Ninguno'

            foto_servicio = request.files.get('foto_servicio')
            foto_final = request.files.get('foto_final')
            foto_servicio_path = servicio['foto_servicio']
            foto_final_path = servicio['foto_final']
            
            if foto_servicio and not foto_servicio.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                raise ValueError("Solo se permiten imágenes JPG o PNG para foto de servicio")
            if foto_final and not foto_final.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                raise ValueError("Solo se permiten imágenes JPG o PNG para foto final")
            
            if foto_servicio:
                if not os.path.exists(Config.UPLOAD_FOLDER):
                    os.makedirs(Config.UPLOAD_FOLDER)
                if not os.access(Config.UPLOAD_FOLDER, os.W_OK):
                    raise PermissionError(f"No hay permisos de escritura en {Config.UPLOAD_FOLDER}")
                nombre_archivo_servicio = f"{id}_servicio_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
                foto_servicio.save(os.path.join(Config.UPLOAD_FOLDER, nombre_archivo_servicio))
                foto_servicio_path = os.path.join('static/uploads', nombre_archivo_servicio).replace('\\', '/')
            if foto_final:
                if not os.path.exists(Config.UPLOAD_FOLDER):
                    os.makedirs(Config.UPLOAD_FOLDER)
                if not os.access(Config.UPLOAD_FOLDER, os.W_OK):
                    raise PermissionError(f"No hay permisos de escritura en {Config.UPLOAD_FOLDER}")
                nombre_archivo_final = f"{id}_final_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
                foto_final.save(os.path.join(Config.UPLOAD_FOLDER, nombre_archivo_final))
                foto_final_path = os.path.join('static/uploads', nombre_archivo_final).replace('\\', '/')

            db.execute("""
                UPDATE servicios SET estado = ?, marca = ?, modelo = ?, servicio = ?, notas = ?, foto_servicio = ?, foto_final = ?, 
                fecha_entrega = ?, tecnico_actual = ? WHERE id = ?
            """, (
                estado, marca, modelo, servicio_str, notas, foto_servicio_path, foto_final_path, 
                datetime.now().strftime('%Y-%m-%d %H:%M:%S') if estado == 'Listo para entrega' else servicio['fecha_entrega'],
                current_user.nombre, id
            ))
            db.execute("""
                INSERT INTO historial (servicio_id, tecnico, fecha_cambio, estado, notas)
                VALUES (?, ?, ?, ?, ?)
            """, (id, current_user.nombre, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), estado, notas))
            flash("Servicio actualizado con éxito", "success")
            return redirect(url_for('tecnico.editar', id=id)) # Redirigir a la misma página de edición
        except ValueError as ve:
            flash(f"Error de validación: {str(ve)}", "error")
        except Exception as e:
            flash(f"Error al actualizar: {str(e)}", "error")
        return redirect(url_for('tecnico.editar', id=id)) # Redirigir a la misma página en caso de error
    return render_template('editar.html', servicio=servicio)

@tecnico_bp.route('/eliminar_servicio/<int:id>', methods=['POST'])
@login_required
def eliminar_servicio(id):
    try:
        # Primero, eliminar los registros dependientes en la tabla 'historial'
        db.execute("DELETE FROM historial WHERE servicio_id = ?", (id,))
        # Luego, eliminar el servicio principal
        db.execute("DELETE FROM servicios WHERE id = ?", (id,))
        flash("Servicio eliminado con éxito.", "success")
    except Exception as e:
        flash(f"Error al eliminar el servicio: {str(e)}", "error")
    
    return redirect(url_for('tecnico.panel'))