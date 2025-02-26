from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_user, logout_user, login_required, current_user
from db import DatabaseSingleton
from models import User
from config import Config
import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
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
            
            stored_password = user_data[0]['contraseña'].encode('utf-8')
            if bcrypt.checkpw(contraseña, stored_password):
                user = User(user_data[0]['id'], user_data[0]['nombre'], user_data[0]['usuario'], user_data[0]['rol'], user_data[0]['activo'])
                login_user(user)
                return redirect(url_for('tecnico.panel'))
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
    return redirect(url_for('tecnico.login'))

@tecnico_bp.route('/panel')
@login_required
def panel():
    servicios = db.query("SELECT * FROM servicios ORDER BY fecha_registro DESC")
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
            
            foto_servicio = request.files.get('foto_servicio')
            foto_final = request.files.get('foto_final')
            foto_servicio_path = servicio['foto_servicio']
            foto_final_path = servicio['foto_final']
            
            if foto_servicio and not foto_servicio.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                raise ValueError("Solo se permiten imágenes JPG o PNG para foto de servicio")
            if foto_final and not foto_final.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                raise ValueError("Solo se permiten imágenes JPG o PNG para foto final")
            
            if foto_servicio:
                foto_servicio_path = os.path.join(Config.UPLOAD_FOLDER, f"{id}_servicio_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg")
                foto_servicio.save(foto_servicio_path)
            if foto_final:
                foto_final_path = os.path.join(Config.UPLOAD_FOLDER, f"{id}_final_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg")
                foto_final.save(foto_final_path)

            db.execute("""
                UPDATE servicios SET estado = ?, notas = ?, foto_servicio = ?, foto_final = ?, 
                fecha_entrega = ?, tecnico_actual = ? WHERE id = ?
            """, (
                estado, notas, foto_servicio_path, foto_final_path, 
                datetime.now().strftime('%Y-%m-%d %H:%M:%S') if estado == 'Listo para entrega' else servicio['fecha_entrega'],
                current_user.nombre, id
            ))
            db.execute("""
                INSERT INTO historial (servicio_id, tecnico, fecha_cambio, estado, notas)
                VALUES (?, ?, ?, ?, ?)
            """, (id, current_user.nombre, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), estado, notas))
            flash("Servicio actualizado con éxito", "success")
        except ValueError as ve:
            flash(f"Error de validación: {str(ve)}", "error")
        except Exception as e:
            flash(f"Error al actualizar: {str(e)}", "error")
        return redirect(url_for('tecnico.panel'))
    return render_template('editar.html', servicio=servicio)

@tecnico_bp.route('/hoja/<int:id>')
@login_required
def hoja(id):
    servicio = db.query("SELECT * FROM servicios WHERE id = ?", (id,))
    if not servicio:
        flash("Servicio no encontrado", "error")
        return redirect(url_for('tecnico.panel'))
    servicio = servicio[0]
    
    pdf_path = os.path.join(Config.UPLOAD_FOLDER, f"hoja_servicio_{id}.pdf")
    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, height - 50, "Taller de Servicios Técnicos")
    c.setFont("Helvetica", 10)
    c.drawString(100, height - 70, "Dirección: Calle Ejemplo 123, Ciudad")
    c.drawString(100, height - 85, "Teléfono: 123-456-7890")
    c.drawString(400, height - 50, f"Fecha: {servicio['fecha_entrega'] or datetime.now().strftime('%Y-%m-%d')}")

    c.setFont("Helvetica-Bold", 12)
    c.drawString(100, height - 120, "Datos del Cliente")
    c.setFont("Helvetica", 10)
    cliente = f"{servicio['nombre']} {servicio['primer_apellido']} {servicio['segundo_apellido']}"
    c.drawString(100, height - 135, f"Nombre: {cliente}")

    c.setFont("Helvetica-Bold", 12)
    c.drawString(100, height - 170, "Datos del Equipo")
    c.setFont("Helvetica", 10)
    c.drawString(100, height - 185, f"Tipo: {servicio['tipo_equipo']}")
    c.drawString(100, height - 200, f"Marca/Modelo: {servicio['marca_modelo']}")
    c.drawString(100, height - 215, f"Serie: {servicio['serie'] or 'No especificada'}")
    c.drawString(100, height - 230, f"Accesorios: {servicio['accesorios']}")

    c.setFont("Helvetica-Bold", 12)
    c.drawString(100, height - 265, "Servicio Realizado")
    c.setFont("Helvetica", 10)
    c.drawString(100, height - 280, f"Servicio: {servicio['servicio']}")
    c.drawString(100, height - 295, "Notas:")
    text = c.beginText(100, height - 310)
    text.setFont("Helvetica", 10)
    for line in (servicio['notas'] or '').split('\n'):
        text.textLine(line)
    c.drawText(text)

    y_tecnico = height - 400
    c.setFont("Helvetica-Bold", 12)
    c.drawString(100, y_tecnico, "Técnico")
    c.line(100, y_tecnico - 5, 250, y_tecnico - 5)
    c.setFont("Helvetica", 10)
    c.drawString(100, y_tecnico - 20, servicio['tecnico_actual'] or 'Sin asignar')

    y_usuario = y_tecnico - 50
    c.setFont("Helvetica-Bold", 12)
    c.drawString(100, y_usuario, "Usuario")
    c.line(100, y_usuario - 5, 250, y_usuario - 5)
    c.setFont("Helvetica", 10)
    c.drawString(100, y_usuario - 20, cliente)

    c.showPage()
    c.save()
    return send_file(pdf_path, as_attachment=True)