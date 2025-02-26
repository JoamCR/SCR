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
            
            #marca = request.form['marca'].strip() if 'marca' in request.form else servicio['marca']
            #modelo = request.form['modelo'].strip() if 'modelo' in request.form else servicio['modelo']
            #if not marca or not modelo:
            #    raise ValueError("Marca y Modelo son obligatorios")

            #marca = servicio['marca']  # Mantener el valor actual
            #modelo = servicio['modelo']  # Mantener el valor actual

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
                
                foto_servicio_path = os.path.join(Config.UPLOAD_FOLDER, f"{id}_servicio_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg")
                foto_servicio.save(foto_servicio_path)
            if foto_final:
                if not os.path.exists(Config.UPLOAD_FOLDER):
                    os.makedirs(Config.UPLOAD_FOLDER)
                if not os.access(Config.UPLOAD_FOLDER, os.W_OK):
                    raise PermissionError(f"No hay permisos de escritura en {Config.UPLOAD_FOLDER}")
                
                foto_final_path = os.path.join(Config.UPLOAD_FOLDER, f"{id}_final_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg")
                foto_final.save(foto_final_path)

            # agregar marca = ?, modelo = ? si es requerido
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

    # Posición inicial (de abajo hacia arriba)
    y = height - 50  # Margen superior

    # Membrete
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, height - 50, "Taller de Servicios Técnicos")
   
    y -= 20  #agregado

    c.setFont("Helvetica", 10)
    c.drawString(100, height - 70, "Dirección: Calle Ejemplo 123, Ciudad")
    y -= 15
    c.drawString(100, height - 85, "Teléfono: 123-456-7890")
    c.drawString(400, height - 50, f"Fecha: {servicio['fecha_entrega'] or datetime.now().strftime('%Y-%m-%d')}")
    y -= 30

    #Datos de cliente
    c.setFont("Helvetica-Bold", 12)
    c.drawString(100, height - 120, "Datos del Cliente")
    
    y -= 15

    c.setFont("Helvetica", 10)
    cliente = f"{servicio['nombre']} {servicio['primer_apellido']} {servicio['segundo_apellido']}"
    c.drawString(100, height - 135, f"Nombre: {cliente}")
    y -= 30

    #Datos del equipo
    c.setFont("Helvetica-Bold", 12)
    c.drawString(100, height - 170, "Datos del Equipo")
    y -= 15
    c.setFont("Helvetica", 10)
    c.drawString(100, height - 185, f"Tipo: {servicio['tipo_equipo']}")
    y -= 15
    
    c.drawString(100, height - 200, f"Marca/Modelo: {servicio['marca_modelo']}")
    y -= 15
    c.drawString(100, height - 215, f"Serie: {servicio['serie'] or 'No especificada'}")
    y -= 15
    c.drawString(100, height - 230, f"Accesorios: {servicio['accesorios']}")
    y -= 30


    #Servicio realizado
    c.setFont("Helvetica-Bold", 12)
    c.drawString(100, height - 265, "Servicio Realizado")
    y -= 15
    c.setFont("Helvetica", 10)
    c.drawString(100, height - 280, f"Servicio: {servicio['servicio']}")
    y -= 15
    c.drawString(100, height - 295, "Notas:")
    y -= 15
    text = c.beginText(100, height - 310) #text = c.beginText(100, y)

    text.setFont("Helvetica", 10)
    for line in (servicio['notas'] or '').split('\n'):
        text.textLine(line)
      
        y -= 15  # Ajustar y por cada línea
        if y < 50:  # Evitar que se salga de la página
            c.drawText(text)
            c.showPage()
            y = height - 50
            text = c.beginText(100, y)
            text.setFont("Helvetica", 10) ##


    c.drawText(text)

    y -=15

    # Imágenes (si existen)
    for foto_field, label in [('foto_inicial', 'Foto Inicial'), ('foto_servicio', 'Foto Durante Servicio'), ('foto_final', 'Foto Final')]:
        if servicio[foto_field]:
            if os.path.exists(servicio[foto_field]):
                c.setFont("Helvetica-Bold", 12)
                c.drawString(100, y, label)
                y -= 20
                try:
                    c.drawImage(servicio[foto_field], 100, y - 100, width=200, height=100, preserveAspectRatio=True)
                    y -= 120
                except Exception as e:
                    c.setFont("Helvetica", 10)
                    c.drawString(100, y, f"No se pudo cargar la imagen: {str(e)}")
                    y -= 15
            if y < 50:
                c.showPage()
                y = height - 50

#firmas

    y_tecnico = height - 400
    c.setFont("Helvetica-Bold", 12)
    c.drawString(100, y_tecnico, "Técnico")
    c.line(100, y_tecnico - 5, 250, y_tecnico - 5)

    y -=20

    c.setFont("Helvetica", 10)
    c.drawString(100, y_tecnico - 20, servicio['tecnico_actual'] or 'Sin asignar')

    y -=30

    y_usuario = y_tecnico - 50
    c.setFont("Helvetica-Bold", 12)
    c.drawString(100, y_usuario, "Usuario")
    c.line(100, y_usuario - 5, 250, y_usuario - 5)

    y -=20
    
    c.setFont("Helvetica", 10)
    c.drawString(100, y_usuario - 20, cliente)

    c.showPage()
    c.save()
    return send_file(pdf_path, as_attachment=True)