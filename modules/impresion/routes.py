from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, session
from flask_login import login_required, current_user
from flask import session
from db import DatabaseSingleton
from config import Config
import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle

impresion_bp = Blueprint('impresion', __name__, template_folder='../../templates')
db = DatabaseSingleton()

@impresion_bp.route('/reporte/<int:id>', methods=['GET', 'POST'])
@login_required
def reporte(id):
    servicio = db.query("SELECT * FROM servicios WHERE id = ?", (id,))
    if not servicio:
        flash("Servicio no encontrado", "error")
        return redirect(url_for('tecnico.panel'))
    servicio = servicio[0]

    if request.method == 'POST':
        if 'guardar_membrete' in request.form:  # Botón para guardar membrete
            try:
                # Obtener datos del membrete desde el formulario
                membrete_nombre = request.form['membrete_nombre'].strip()
                membrete_direccion = request.form['membrete_direccion'].strip()
                membrete_telefono = request.form['membrete_telefono'].strip()
                if not membrete_nombre:
                    raise ValueError("El nombre del taller es obligatorio")
                
                # Guardar membrete en la sesión
                session['membrete'] = {
                    'nombre': membrete_nombre,
                    'direccion': membrete_direccion,
                    'telefono': membrete_telefono
                }
                flash("Membrete actualizado con éxito", "success")
                return redirect(url_for('impresion.reporte', id=id))
            
            except ValueError as ve:
                flash(f"Error de validación: {str(ve)}", "error")
            except Exception as e:
                flash(f"Error al guardar el membrete: {str(e)}", "error")
            return redirect(url_for('impresion.reporte', id=id))

        # Generar PDF con el membrete actualizado
        try:
            # Obtener membrete de la sesión o usar valores por defecto
            membrete = session.get('membrete', {
                'nombre': 'Taller de Servicios Técnicos',
                'direccion': 'Calle Ejemplo 123, Ciudad',
                'telefono': '123-456-7890'
            })

            membrete_nombre = membrete['nombre']
            membrete_direccion = membrete['direccion']
            membrete_telefono = membrete['telefono']

            # Verificar que la carpeta de uploads exista y sea escribible
            if not os.path.exists(Config.UPLOAD_FOLDER):
                os.makedirs(Config.UPLOAD_FOLDER)
                print(f"Creada carpeta: {Config.UPLOAD_FOLDER}")
            if not os.access(Config.UPLOAD_FOLDER, os.W_OK):
                raise PermissionError(f"No hay permisos de escritura en {Config.UPLOAD_FOLDER}")

            # Generar PDF
            pdf_path = os.path.join(Config.UPLOAD_FOLDER, f"reporte_servicio_{id}.pdf")
            print(f"Intentando generar PDF en: {pdf_path}")
            c = canvas.Canvas(pdf_path, pagesize=letter)
            width, height = letter
            margen_izquierdo = 50
            margen_derecho = width - 50
            margen_inferior = 50
            margen_superior = height - 50

            # Posición inicial
            y = margen_superior

           # Membrete
            c.setFont("Helvetica", 16)  # Cambiado a Helvetica 16
            c.drawString(margen_izquierdo, y, membrete['nombre'])
            y -= 20
            c.setFont("Helvetica", 12)  # Cambiado a Helvetica 12
            c.drawString(margen_izquierdo, y, membrete['direccion'])
            y -= 15
            c.drawString(margen_izquierdo, y, membrete['telefono'])
            fecha = servicio['fecha_entrega'] or datetime.now().strftime('%Y/%m-%d %H:%M:%S')
            c.drawString(margen_derecho - 100, y + 35, f"Fecha: {fecha}")
            y -= 20

            # Línea divisoria (HR)
            c.setLineWidth(1)
            c.line(margen_izquierdo, y, margen_derecho, y)
            y -= 20

            # Datos del Cliente
            c.setFont("Helvetica", 16)  # Cambiado a Helvetica 16
            c.drawString(margen_izquierdo, y, "Datos del Cliente")
            y -= 20
            #Lista de los datos
            c.setFont("Helvetica", 12)  # Cambiado a Helvetica 12
            cliente = f"Nombre: {servicio['nombre']} {servicio['primer_apellido']} {servicio['segundo_apellido']}"
            c.drawString(margen_izquierdo, y, cliente)
            y -= 20
            #otros campos opcionales
            c.setFont("Helvetica", 12)
            cliente = f"Telefono: {servicio['telefono']} "
            c.drawString(margen_izquierdo, y, cliente)
            y -= 20
                
            # Línea divisoria poner -15 de preferencia para mejor margen
            c.line(margen_izquierdo, y, margen_derecho, y)
            y -= 15

            # Detalles del Equipo (Tabla)
            c.setFont("Helvetica", 16)
            c.drawString(margen_izquierdo, y, "Detalles del Equipo")
            y -= 20
            data = [
                ["Tipo", "Marca", "Modelo", "Serie", "Accesorios"],
                [servicio['tipo_equipo'], servicio['marca'], servicio['modelo'], servicio['serie'] or 'No especificada', servicio['accesorios']]
            ]

            # Calcular anchos dinámicos con prioridad para "Accesorios" y usar todo el ancho disponible
            ancho_total_disponible = width - margen_izquierdo - margen_derecho  # 512 puntos
            col_widths = []
            for i in range(5):
                if i == 4:  # Columna "Accesorios" (índice 4)
                    max_width = max(c.stringWidth(str(row[i]), "Helvetica", 12) for row in data) + 30  # Más padding para texto largo
                    col_widths.append(max(max_width, 150))  # Mínimo de 150 puntos para "Accesorios"
                else:  # Otras columnas
                    max_width = max(c.stringWidth(str(row[i]), "Helvetica", 12) for row in data) + 20  # Padding estándar
                    col_widths.append(max(min(max_width, (ancho_total_disponible - 150) // 4), 80))  # Mínimo de 80, máximo ajustado

            # Ajustar proporcionalmente para usar todo el ancho disponible, asegurando mínimo para "Accesorios"
            total_calculado = sum(col_widths)
            if total_calculado < ancho_total_disponible:
                factor = ancho_total_disponible / total_calculado
                col_widths = [min(w * factor, ancho_total_disponible // 5) if i != 4 else max(w * factor, 150) for i, w in enumerate(col_widths)]
            elif total_calculado > ancho_total_disponible:
                factor = ancho_total_disponible / total_calculado
                col_widths = [max(w * factor, 80) if i != 4 else max(w * factor, 150) for i, w in enumerate(col_widths)]

            # Crear la tabla con mejor estilo y espaciado, ocupando todo el ancho
            tabla = Table(data, colWidths=col_widths)
            tabla.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 12),
                ('LEADING', (0, 0), (-1, -1), 14),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('LEFTPADDING', (0, 0), (-1, -1), 5),
                ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),  # Bordes visibles
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),  # Líneas internas sutiles
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('WORDWRAP', (0, 0), (-1, -1), True),
            ]))

            # Calcular dimensiones y dibujar, ocupando todo el ancho disponible
            tabla.wrapOn(c, ancho_total_disponible, height)
            tabla_width, tabla_height = tabla.wrap(ancho_total_disponible, height)
            if y - tabla_height - 10 < margen_inferior:
                c.showPage()
                y = margen_superior
            tabla.drawOn(c, margen_izquierdo, y - tabla_height - 10)  # Usar márgenes exactos
            y -= tabla_height + 25  # Más espacio después de la tabla
           
           
           # Línea divisoria
            c.line(margen_izquierdo, y, margen_derecho, y)
            y -= 15

            # Servicio Realizado
            c.setFont("Helvetica-Bold", 14)
            c.drawCentredString(width / 2, y, "Servicio Realizado")
            y -= 20
            c.setFont("Helvetica", 12)
            text_object = c.beginText(margen_izquierdo, y)
            text_object.setFont("Helvetica", 12)
            text_object.setLeading(14)
            max_width = margen_derecho - margen_izquierdo
            servicio_text = f"Servicio: {servicio['servicio']}"
            for line in servicio_text.split('\n'):
                while c.stringWidth(line, "Helvetica", 12) > max_width:
                    split_point = len(line) - 1
                    while split_point > 0 and c.stringWidth(line[:split_point], "Helvetica", 12) > max_width:
                        split_point -= 1
                    text_object.textLine(line[:split_point])
                    line = line[split_point:].strip()
                    y -= 14
                    if y < 150:
                        c.drawText(text_object)
                        c.showPage()
                        y = margen_superior
                        text_object = c.beginText(margen_izquierdo, y)
                        text_object.setFont("Helvetica", 12)
                        text_object.setLeading(14)
                text_object.textLine(line)
                y -= 14
                if y < 150:
                    c.drawText(text_object)
                    c.showPage()
                    y = margen_superior
                    text_object = c.beginText(margen_izquierdo, y)
                    text_object.setFont("Helvetica", 12)
                    text_object.setLeading(14)
            c.drawText(text_object)
            y -= 15

            c.drawString(margen_izquierdo, y, "Notas:")
            y -= 15

            # Manejo de Notas con ajuste de líneas largas
            notas = servicio['notas'] or 'Sin notas'
            text_object = c.beginText(margen_izquierdo, y)
            text_object.setFont("Helvetica", 12)
            text_object.setLeading(14)
            max_width = margen_derecho - margen_izquierdo
            for line in notas.split('\n'):
                while c.stringWidth(line, "Helvetica", 12) > max_width:
                    split_point = len(line) - 1
                    while split_point > 0 and c.stringWidth(line[:split_point], "Helvetica", 12) > max_width:
                        split_point -= 1
                    text_object.textLine(line[:split_point])
                    line = line[split_point:].strip()
                    y -= 14
                    if y < 150:
                        c.drawText(text_object)
                        c.showPage()
                        y = margen_superior
                        text_object = c.beginText(margen_izquierdo, y)
                        text_object.setFont("Helvetica", 12)
                        text_object.setLeading(14)
                text_object.textLine(line)
                y -= 14
                if y < 150:
                    c.drawText(text_object)
                    c.showPage()
                    y = margen_superior
                    text_object = c.beginText(margen_izquierdo, y)
                    text_object.setFont("Helvetica", 12)
                    text_object.setLeading(14)
            c.drawText(text_object)
            y -= 20

            # Línea divisoria (continúa como estaba)
            c.line(margen_izquierdo, y, margen_derecho, y)
            y -= 15

            # Después de las Notas y antes de la línea divisoria

            # Fotos
            fotos = [f for f in [servicio['foto_inicial'], servicio['foto_servicio'], servicio['foto_final']] if f]
            print(f"Fotos detectadas: {fotos}")  # Depuración
            fotos_validas = []
            for foto in fotos:
                foto_path = os.path.join(Config.UPLOAD_FOLDER, os.path.basename(foto)) if not os.path.isabs(foto) else foto
                if os.path.exists(foto_path):
                    fotos_validas.append(foto_path)
                else:
                    print(f"No se encontró la foto: {foto_path}")  # Depuración
            if fotos_validas:
                if y < 200:
                    c.showPage()
                    y = margen_superior
                c.setFont("Helvetica-Bold", 14)
                c.drawString(margen_izquierdo, y, "Fotos")
                y -= 25  # Ajuste para más espacio antes de las fotos
                x = margen_izquierdo
                for foto in fotos_validas[:3]:
                    try:
                        c.drawImage(foto, x, y - 100, width=150, height=100, preserveAspectRatio=True)
                        print(f"Dibujando foto: {foto}")  # Depuración
                        x += 160
                    except Exception as e:
                        print(f"Error al dibujar la foto {foto}: {str(e)}")  # Depuración
                y -= 120
            else:
                print("No hay fotos válidas para mostrar en el PDF")  # Depuración

            # Línea divisoria
            c.line(margen_izquierdo, y, margen_derecho, y)
            y -= 15

            # Firmas
            if y > 150:
                y = margen_inferior + 50
            else:
                c.showPage()
                y = margen_inferior + 50

            c.setFont("Helvetica", 12)
            # Técnico (izquierda)
            c.line(margen_izquierdo, y, margen_izquierdo + 150, y)
            c.drawString(margen_izquierdo + 50 , y - 15, "Técnico")
            c.drawString(margen_izquierdo + 50, y - 30, servicio['tecnico_actual'] or 'Sin asignar')
            # Usuario (derecha)
            c.line(margen_derecho - 150, y, margen_derecho, y)
            c.drawString(margen_derecho - 100, y - 15, "Usuario")
            c.drawString(margen_derecho - 100, y - 30, f"{servicio['nombre']} {servicio['primer_apellido']} {servicio['segundo_apellido']}")
            c.save()
            print(f"PDF generado en: {pdf_path}")

            # Verificar que el archivo exista antes de enviarlo
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"El archivo PDF {pdf_path} no se generó correctamente")
            
            # Verificar tamaño del archivo para confirmar que no está vacío
            if os.path.getsize(pdf_path) == 0:
                raise FileNotFoundError(f"El archivo PDF {pdf_path} está vacío")

            # Enviar el archivo para descarga
            print(f"Enviando archivo: {pdf_path}")
            return send_file(pdf_path, as_attachment=True, download_name=f"reporte_servicio_{id}.pdf")
            
        except ValueError as ve:
            flash(f"Error de validación: {str(ve)}", "error")
        except FileNotFoundError as fe:
            flash(f"Error al descargar: {str(fe)} - Verifica permisos en {Config.UPLOAD_FOLDER}", "error")
        except PermissionError as pe:
            flash(f"Error de permisos: {str(pe)} - Ajusta permisos en {Config.UPLOAD_FOLDER}", "error")
        except Exception as e:
            flash(f"Error al generar o descargar el PDF: {str(e)}", "error")
            print(f"Error detallado: {str(e)} - Revisa la terminal para más detalles")
        return redirect(url_for('impresion.reporte', id=id))
    
        # Previsualización (usar membrete guardado o valores por defecto)
    membrete = session.get('membrete', {
        'nombre': 'Taller de Servicios Técnicos',
        'direccion': 'Calle Ejemplo 123, Ciudad',
        'telefono': '123-456-7890'
    })
    
    return render_template('impresion.html', servicio=servicio, membrete=membrete)