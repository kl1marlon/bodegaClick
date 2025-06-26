from rest_framework.views import APIView
from django.http import HttpResponse
from .models import Factura
from datetime import datetime
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors

class FacturaReportePDFView(APIView):
    """
    Vista para generar y descargar reportes de facturas en formato PDF.
    Permite filtrar por fecha_desde y fecha_hasta.
    """
    
    def get(self, request):
        """
        Genera un PDF con el reporte de facturas, opcionalmente filtrado por fecha.
        
        Query params:
            fecha_desde (str): Fecha inicial en formato YYYY-MM-DD
            fecha_hasta (str): Fecha final en formato YYYY-MM-DD
        """
        # Obtener parámetros de filtro
        fecha_desde = request.query_params.get('fecha_desde')
        fecha_hasta = request.query_params.get('fecha_hasta')
        
        # Preparar queryset base con prefetching para optimizar
        queryset = Factura.objects.all().prefetch_related(
            'detalles', 
            'detalles__producto'
        ).order_by('-fecha')
        
        # Aplicar filtros si se proporcionaron
        if fecha_desde:
            fecha_desde_obj = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
            queryset = queryset.filter(fecha__date__gte=fecha_desde_obj)
            
        if fecha_hasta:
            fecha_hasta_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
            queryset = queryset.filter(fecha__date__lte=fecha_hasta_obj)
        
        # Crear un buffer para el PDF
        buffer = BytesIO()
        
        # Configurar el documento PDF
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            title='Reporte de Facturas',
            author='BodegaClick'
        )
        
        # Lista para almacenar los elementos del PDF
        elements = []
        
        # Configurar estilos
        styles = getSampleStyleSheet()
        title_style = styles['Heading1']
        subtitle_style = styles['Heading2']
        normal_style = styles['Normal']
        
        # Título del reporte
        elements.append(Paragraph('Reporte de Facturas', title_style))
        elements.append(Spacer(1, 12))
        
        # Añadir rango de fechas si se aplicó algún filtro
        if fecha_desde or fecha_hasta:
            fecha_texto = 'Rango de fechas: '
            if fecha_desde:
                fecha_texto += f'Desde {fecha_desde}'
            if fecha_desde and fecha_hasta:
                fecha_texto += ' '
            if fecha_hasta:
                fecha_texto += f'Hasta {fecha_hasta}'
            elements.append(Paragraph(fecha_texto, normal_style))
            elements.append(Spacer(1, 12))
        
        # Añadir fecha de generación del reporte
        elements.append(Paragraph(f'Generado el: {datetime.now().strftime("%Y-%m-%d %H:%M")}', normal_style))
        elements.append(Spacer(1, 20))
        
        # Verificar si hay facturas
        if not queryset.exists():
            elements.append(Paragraph('No se encontraron facturas para el período seleccionado.', normal_style))
        else:
            # Para cada factura, añadir su información
            for factura in queryset:
                # Información de la factura
                elements.append(Paragraph(f'Factura #{factura.numero}', subtitle_style))
                elements.append(Paragraph(f'Fecha: {factura.fecha.strftime("%Y-%m-%d %H:%M")}', normal_style))
                elements.append(Paragraph(f'Moneda: {factura.get_moneda_display()}', normal_style))
                elements.append(Paragraph(f'Total BS: {factura.total_bs}', normal_style))
                elements.append(Paragraph(f'Total USD: {factura.total_usd}', normal_style))
                elements.append(Spacer(1, 10))
                
                # Encabezados para la tabla de detalles
                data = [['Producto', 'Cantidad', 'Precio Unitario', 'Total']]
                
                # Añadir detalles
                for detalle in factura.detalles.all():
                    data.append([
                        detalle.producto.nombre,
                        f"{detalle.cantidad:.2f}",
                        f"{detalle.precio_unitario:.2f}",
                        f"{detalle.total:.2f}"
                    ])
                
                # Crear tabla
                table = Table(data, colWidths=[250, 80, 100, 100])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                elements.append(table)
                elements.append(Spacer(1, 20))  # Espacio entre facturas
        
        # Generar el PDF
        doc.build(elements)
        
        # Preparar la respuesta HTTP
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        
        # Configurar el nombre del archivo para descarga
        fecha_hoy = datetime.now().strftime('%Y%m%d')
        response['Content-Disposition'] = f'attachment; filename="reporte_facturas_{fecha_hoy}.pdf"'
        
        return response
