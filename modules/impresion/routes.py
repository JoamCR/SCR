import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, session
from flask_login import login_required, current_user
from flask import session
from db import DatabaseSingleton
from config import Config
import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle

impresion_bp = Blueprint('impresion', __name__, template_folder='../../templates')
db = DatabaseSingleton()

@impresion_bp.route('/reporte/<int:id>', methods=['GET', 'POST'])
@login_required
def reporte(id):
    def create_pdf(data):
        buffer = io.BytesIO()
        WIDTH, HEIGHT = letter
        HEADER_BLUE = colors.HexColor('#1E3A8A')
        GRAY_BG = colors.HexColor('#E5E7EB')
        p = canvas.Canvas(buffer, pagesize=letter)

        # Logo
        logo_path = os.path.join('static', 'images', 'logo.png')
        if os.path.exists(logo_path):
            p.drawImage(logo_path, WIDTH - 4.5*cm, HEIGHT - 2.5*cm, width=4*cm, height=2*cm, preserveAspectRatio=True, mask='auto')

        # Información de la empresa
        p.setFont('Helvetica', 8)
        p.drawString(1.5*cm, HEIGHT - 1*cm, data.get('membrete_nombre', 'MEX GROUP'))
        p.drawString(1.5*cm, HEIGHT - 1.4*cm, data.get('membrete_rfc', 'R.F.C MEL760421RH2   CURP: MEL760421HCCXNN03'))
        p.drawString(1.5*cm, HEIGHT - 1.8*cm, f"CEL: {data.get('celular', '9811310163')}   OFICINA: {data.get('membrete_telefono', '9811441303')}")
        p.drawString(1.5*cm, HEIGHT - 2.2*cm, data.get('membrete_direccion', 'CALLE 23 No 78 COL. PABLO GARCIA C.P. 24080'))
        p.drawString(1.5*cm, HEIGHT - 2.6*cm, data.get('membrete_ciudad', 'SAN FRANCISCO DE CAMPECHE, CAMP.'))
                                # El PDF se genera en memoria, no es necesario verificar existencia ni tamaño de archivo

        # Línea divisora azul
        p.setStrokeColor(HEADER_BLUE)
        p.setLineWidth(2)
        p.line(1.5*cm, HEIGHT - 3.2*cm, WIDTH - 1.5*cm, HEIGHT - 3.2*cm)

        # Información del cliente
        p.setLineWidth(0.5)
        p.setStrokeColor(colors.black)
        p.setFont('Helvetica', 10)
        y_pos = HEIGHT - 5*cm
        p.drawString(WIDTH - 6*cm, y_pos + 0.6*cm, f"Fecha: {data.get('fecha', '')}")
        p.drawString(1.5*cm, y_pos, f"CLIENTE: {data.get('cliente', '')}")
        # p.line(3.5*cm, y_pos - 0.1*cm, WIDTH / 2 + 2*cm, y_pos - 0.1*cm)
        y_pos -= 1*cm
        p.drawString(1.5*cm, y_pos, f"DIRECCION: {data.get('direccion', '')}")
        # p.line(4*cm, y_pos - 0.1*cm, WIDTH - 1.5*cm, y_pos - 0.1*cm)
        y_pos -= 1*cm
        p.drawString(1.5*cm, y_pos, f"DEPARTAMENTO: {data.get('departamento', '')}")
        # p.line(5*cm, y_pos - 0.1*cm, WIDTH - 1.5*cm, y_pos - 0.1*cm)
        y_pos -= 1*cm
        p.drawString(1.5*cm, y_pos, f"DEPENDENCIA: {data.get('dependencia', '')}")
        # p.line(4.8*cm, y_pos - 0.1*cm, WIDTH - 1.5*cm, y_pos - 0.1*cm)
        y_pos -= 1*cm
        p.drawString(1.5*cm, y_pos, f"TEL: {data.get('tel', '')}")
        # p.line(2.5*cm, y_pos - 0.1*cm, 8*cm, y_pos - 0.1*cm)
        

        # Tabla de equipo
        y_pos -= 1.5*cm
        p.setFillColor(HEADER_BLUE)
        p.rect(1.5*cm, y_pos, WIDTH - 3*cm, 0.8*cm, fill=1, stroke=0)
        p.setFillColor(colors.white)
        p.setFont('Helvetica-Bold', 10)
        p.drawCentredString(WIDTH / 2, y_pos + 0.3*cm, "DATOS DEL EQUIPO")
        y_pos -= 0.6*cm
        p.setFillColor(colors.black)
        p.setFont('Helvetica-Bold', 9)
        p.drawCentredString(2.5*cm, y_pos, "Cant.")
        p.drawCentredString(6*cm, y_pos, "Descripción")
        p.drawCentredString(10.5*cm, y_pos, "Marca")
        p.drawCentredString(14*cm, y_pos, "Modelo")
        p.drawCentredString(18*cm, y_pos, "No. De Serie")
        p.setFont('Helvetica', 9)
        y_pos -= 0.1*cm
        max_items = 1
        for i in range(max_items):
            y_pos -= 0.6*cm
            p.drawCentredString(2.5*cm, y_pos + 0.2*cm, data.get('eq_cant', '1'))
            p.drawString(4*cm, y_pos + 0.2*cm, data.get('eq_desc', ''))
            p.drawCentredString(10.5*cm, y_pos + 0.2*cm, data.get('eq_marca', ''))
            p.drawCentredString(14*cm, y_pos + 0.2*cm, data.get('eq_modelo', ''))
            p.drawCentredString(18*cm, y_pos + 0.2*cm, data.get('eq_serie', ''))

        # 4. FALLAS, SERVICIO Y PIEZAS
        y_pos -= 0.5*cm
        styles = getSampleStyleSheet()
        styleN = styles['Normal']
        styleN.fontSize = 9
        styleN.leading = 12
        def draw_section(x, y, width, height, title, content_text):
            p.setFont('Helvetica-Bold', 10)
            p.drawCentredString(x + width/2, y + height, title)
            # p.rect(x, y, width, height) # Eliminar el recuadro
            p_content_height = 0
            if content_text:
                p_content = Paragraph(content_text.replace('\n', '<br/>'), styleN)
                w, p_content_height = p_content.wrapOn(p, width - 0.4*cm, height - 0.4*cm)
                p_content.drawOn(p, x + 0.2*cm, y + height - p_content_height - 0.2*cm)
            # Retornar la nueva posición Y basada en la altura real del contenido
            return y - (p_content_height + 0.5*cm)
        y_pos = draw_section(1.2*cm, y_pos - 3*cm, WIDTH - 3*cm, 3*cm, "FALLAS Y OBSERVACIONES", data.get('fallas', ''))
        y_pos = draw_section(1.2*cm, y_pos - 1*cm, WIDTH - 3*cm, 3*cm, "SERVICIO REALIZADO", data.get('servicio', ''))

        # 4.5. FOTOS DEL SERVICIO
        p.setFont('Helvetica-Bold', 10)
        p.drawCentredString(WIDTH / 2, y_pos, "IMÁGENES DEL SERVICIO")
        y_pos -= 0.2*cm

        image_data = [
            ("Foto Inicial", data.get('foto_inicial')),
            ("Foto de Servicio", data.get('foto_servicio')),
            ("Foto Final", data.get('foto_final'))
        ]
        valid_images = [(label, path) for label, path in image_data if path and os.path.exists(path)]

        if valid_images:
            num_images = len(valid_images)
            total_spacing = (num_images - 1) * 0.2*cm
            img_width = (WIDTH - 3.5*cm - total_spacing) / num_images
            img_height = img_width * (3/4) # Proporción 4:3
            x_start = 2*cm
            y_pos -= img_height
            for i, (label, img_path) in enumerate(valid_images):
                current_x = x_start + i * (img_width + 0.2*cm)
                p.drawImage(img_path, current_x, y_pos, width=img_width, height=img_height, preserveAspectRatio=True, mask='auto')
                p.setFont('Helvetica', 7)
                p.drawCentredString(current_x + img_width/2, y_pos - 0.4*cm, label)
        else:
            p.setFont('Helvetica', 9)
            p.drawCentredString(WIDTH / 2, y_pos - 0.5*cm, "No hay imágenes adjuntas.")
        
        y_pos -= 1*cm # Espacio extra después de las imágenes
        # 5. ZONA INFERIOR (Acuerdo y Piezas)
        # p.setFillColor(GRAY_BG)
        # p.roundRect(1.5*cm, 3.5*cm, 10*cm, 3*cm, 4, stroke=0, fill=1)
        # p.setFillColor(colors.black)
        # legal_text = """
        # <b>DEBO (EMOS) Y PAGARÉ (MOS) INCONDICIONALMENTE POR ESTE PAGARÉ MERCANTIL</b><br/>
        # A la orden de JUAN GABRIEL MEX LEON, en esta PLAZA DE SAN FRANCISCO DE CAMPECHE, CAMPECHE EL TOTAL ANOTADO EN LA PARTE DERECHA POR MERCANCIAS Y/O SERVICIOS QUE RECIBÍ (MOS) A MI ENTERA CONFORMIDAD.
        # <br/><br/>
        # <b>OBSERVACIONES</b>
        # <li>TODA VERIFICACION CAUSA HONORARIOS.</li>
        # <li>LA EMPRESA NO SE HACE RESPONSABLE POR LA INFORMACION ALMACENADA EN LOS DISCOS DUROS U OTROS MEDIOS DE ALMACENAMIENTO.</li>
        # """
        # legal_paragraph = Paragraph(legal_text, styles['Normal'])
        # legal_paragraph.wrapOn(p, 9.5*cm, 2.8*cm)
        # legal_paragraph.drawOn(p, 1.7*cm, 3.7*cm)
        # p.setFont('Helvetica-Bold', 9)
        # p.drawCentredString(16*cm, 6.6*cm, "PIEZAS")
        # p.rect(12*cm, 3.5*cm, 8*cm, 3*cm)

        # 6. FIRMAS Y FOOTER
        p.line(2*cm, 3*cm, 9*cm, 3*cm)
        p.drawCentredString(5.5*cm, 2.6*cm, f"{data.get('cliente', '')}") 
        
        p.line(12*cm, 3*cm, 19*cm, 3*cm)
        p.drawCentredString(15.5*cm, 2.6*cm, f"{data.get('usuario', '')}")
        p.setFont('Helvetica-Bold', 7)
        p.drawString(1.5*cm, 2*cm, "DATOS BANCARIOS:")
        p.setFont('Helvetica', 7)
        p.drawString(1.5*cm, 1.7*cm, "BANCOMER")
        p.drawString(1.5*cm, 1.4*cm, "NUMERO DE CUENTA: 0175530334")
        p.drawString(1.5*cm, 1.1*cm, "NUMERO DE TRANSFERENCIA: 012050001755303345")
        p.setFont('Helvetica-Bold', 7)
        p.drawString(WIDTH - 6*cm, 2*cm, "CORREOS:")
        p.setFont('Helvetica', 7)
        p.drawString(WIDTH - 6*cm, 1.7*cm, "mexgroup2009@hotmail.es")
        p.drawString(WIDTH - 6*cm, 1.4*cm, "mexgroupventas@hotmail.com")
        p.drawString(WIDTH - 6*cm, 1.1*cm, "j_mex_r1@hotmail.com")

        # Íconos de la izquierda
        for idx, img in enumerate(['item1.png', 'item2.png', 'item3.png', 'item4.png']):
            img_path = os.path.join('static', 'images', img)
            y_img = [HEIGHT - 5*cm, HEIGHT - 11*cm, HEIGHT - 15*cm, 6*cm][idx]
            if os.path.exists(img_path):
                p.drawImage(img_path, 0.2*cm, y_img, width=1*cm, preserveAspectRatio=True, mask='auto')

        p.save()
        buffer.seek(0)
        return buffer
    servicio = db.query("SELECT * FROM servicios WHERE id = ?", (id,))
    if not servicio:
        flash("Servicio no encontrado", "error")
        return redirect(url_for('tecnico.panel'))
    servicio = servicio[0]

    # Usar membrete guardado en sesión o valores por defecto
    membrete = session.get('membrete', {
        'nombre': 'MEX GROUP',
        'direccion': 'Calle 23 entre 10 y 12 Pablo Garcia',
        'telefono': '9811441303',
        'celular': '9811310163',
        'departamento': '',
        'dependencia': ''
    })

    if request.method == 'POST':
        try:
            pdf_data = {
                **membrete, # Combina los datos del membrete
                'orden_no': id,
                'fecha': servicio['fecha_entrega'] if 'fecha_entrega' in servicio.keys() and servicio['fecha_entrega'] else datetime.now().strftime('%d/%m/%Y'),
                'usuario': servicio['tecnico_actual'] or 'N/A',
                'cliente': f"{servicio['nombre'] if 'nombre' in servicio.keys() else ''} {servicio['primer_apellido'] if 'primer_apellido' in servicio.keys() else ''} {servicio['segundo_apellido'] if 'segundo_apellido' in servicio.keys() else ''}".strip(),
                'tel': servicio['telefono'],
                'eq_desc': servicio['tipo_equipo'],
                'eq_marca': servicio['marca'],
                'eq_modelo': servicio['modelo'],
                'eq_serie': servicio['serie'] or 'N/A',
                'fallas': servicio['notas'] or 'Sin observaciones.',
                'servicio': servicio['servicio'] or 'No especificado.',
                'foto_inicial': servicio['foto_inicial'] if 'foto_inicial' in servicio.keys() and servicio['foto_inicial'] else None,
                'foto_servicio': servicio['foto_servicio'] if 'foto_servicio' in servicio.keys() and servicio['foto_servicio'] else None,
                'foto_final': servicio['foto_final'] if 'foto_final' in servicio.keys() and servicio['foto_final'] else None,
            }
            pdf_file = create_pdf(pdf_data)
            return send_file(pdf_file, as_attachment=True, download_name=f"reporte_servicio_{id}.pdf", mimetype='application/pdf')
        except Exception as e:
            import traceback
            error_msg = f"Error al generar o descargar el PDF: {str(e)}\n{traceback.format_exc()}"
            flash(error_msg, "danger")
            print(error_msg)

    return render_template('impresion.html', servicio=servicio, membrete=membrete)