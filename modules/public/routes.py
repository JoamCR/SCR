from flask import Blueprint, render_template, request, redirect, url_for, flash
from db import DatabaseSingleton
from config import Config
import os
from datetime import datetime
import re

public_bp = Blueprint('public', __name__, template_folder='../../templates')
db = DatabaseSingleton()

@public_bp.route('/nuevo', methods=['GET', 'POST'])
def nuevo():
    if request.method == 'POST':
        try:
            # Validaciones
            nombre = request.form['nombre'].strip()
            primer_apellido = request.form['primer_apellido'].strip()
            segundo_apellido = request.form['segundo_apellido'].strip()
            telefono = request.form['telefono'].strip()
            if not all([nombre, primer_apellido, segundo_apellido, telefono]):
                raise ValueError("Todos los campos de cliente son obligatorios")
            if not re.match(r'^\d{10}$', telefono):
                raise ValueError("El teléfono debe ser un número de 10 dígitos")

            tipo_equipo = request.form['tipo_equipo']
            marca_modelo = request.form['marca_modelo'].strip()
            if not marca_modelo:
                raise ValueError("Marca/Modelo es obligatorio")
            if tipo_equipo not in ['Laptop', 'CPU', 'Impresora', 'Otros']:
                raise ValueError("Tipo de equipo inválido")

            serie = request.form.get('serie', '').strip()
            
            foto = request.files['foto_inicial']
            if not foto:
                raise ValueError("La foto inicial es obligatoria")
            if foto and not foto.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                raise ValueError("Solo se permiten imágenes JPG o PNG")
            foto_path = os.path.join(Config.UPLOAD_FOLDER, f"{datetime.now().strftime('%Y%m%d%H%M%S')}_inicial.jpg")
            foto.save(foto_path)

            accesorios = request.form.getlist('accesorios')
            accesorios_str = ', '.join(accesorios) if accesorios else 'Ninguno'

            servicios = request.form.getlist('servicio')
            if 'Otros' in servicios and request.form.get('otros_servicio'):
                otros = request.form['otros_servicio'].strip()
                if not otros:
                    raise ValueError("Especifique el servicio 'Otros'")
                servicios[servicios.index('Otros')] = f"Otros: {otros}"
            servicio_str = ', '.join(servicios) if servicios else 'Ninguno'

            db.execute("""
                INSERT INTO servicios (nombre, primer_apellido, segundo_apellido, telefono, tipo_equipo, marca_modelo, servicio, accesorios, serie, fecha_registro, foto_inicial)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                nombre, primer_apellido, segundo_apellido, telefono, tipo_equipo, marca_modelo,
                servicio_str, accesorios_str, serie, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), foto_path
            ))
            flash("Equipo registrado con éxito", "success")
        except ValueError as ve:
            flash(f"Error de validación: {str(ve)}", "error")
        except Exception as e:
            flash(f"Error al registrar: {str(e)}", "error")
        return redirect(url_for('public.nuevo'))
    return render_template('nuevo.html')