from django.shortcuts import render, redirect
from django.views.generic import View
from django.http import HttpResponse
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta, datetime
import csv
from io import BytesIO
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import inch
from ..models import Despacho, Motorista, Farmacia, Moto, AsignacionMoto, AsignacionFarmacia, ReportDownloadHistory
from ..decorators import RolRequiredMixin, LoginRequiredMixin, GerenteOnlyMixin
from django.utils.dateparse import parse_date
from reportlab.lib.styles import getSampleStyleSheet
from ..utils import rango_fechas_por_tipo, generar_nombre_archivo




# ============================================
# VISTAS DE DASHBOARD
# ============================================

class DashboardGeneralView(LoginRequiredMixin, View):
    """
    Dashboard General - acceso Admin/Supervisor/Gerente.
    Métricas clave del sistema.
    """
    template_name = 'dashboard/dashboard_general.html'

    def get(self, request):
        # Verificar roles permitidos
        if request.user.rol not in ['ADMINISTRADOR', 'GERENTE']:
            messages.error(request, 'No tienes acceso al dashboard general.')
            return redirect('home')
        
        # Métricas generales
        total_despachos = Despacho.objects.count()
        despachos_pendientes = Despacho.objects.filter(estado='PENDIENTE').count()
        despachos_en_ruta = Despacho.objects.filter(estado='EN_RUTA').count()
        despachos_entregados = Despacho.objects.filter(estado='ENTREGADO').count()
        despachos_incidencias = Despacho.objects.filter(estado='INCIDENCIA').count()
        
        # Últimos 7 días
        hace_7_dias = timezone.now() - timedelta(days=7)
        despachos_recientes = Despacho.objects.filter(fecha_hora_creacion__gte=hace_7_dias).count()
        
        # Motoristas activos
        motoristas_activos = Motorista.objects.filter(licencia_vigente=True).count()
        motoristas_total = Motorista.objects.count()
        
        # Motos disponibles
        motos_disponibles = Moto.objects.filter(estado='OPERATIVO').count()
        motos_total = Moto.objects.count()
        
        # Farmacias
        farmacias_total = Farmacia.objects.count()
        
        # Tiempo promedio de entrega (en minutos)
        despachos_entregados_obj = Despacho.objects.filter(
            estado='ENTREGADO',
            fecha_hora_estimada_llegada__isnull=False,
            fecha_hora_despacho__isnull=False
        )
        
        if despachos_entregados_obj.exists():
            total_minutos = sum(
                int((d.fecha_hora_estimada_llegada - d.fecha_hora_despacho).total_seconds() / 60)
                for d in despachos_entregados_obj
            )
            tiempo_promedio = total_minutos // len(despachos_entregados_obj)
        else:
            tiempo_promedio = 0
        
        context = {
            'total_despachos': total_despachos,
            'despachos_pendientes': despachos_pendientes,
            'despachos_en_ruta': despachos_en_ruta,
            'despachos_entregados': despachos_entregados,
            'despachos_incidencias': despachos_incidencias,
            'despachos_recientes': despachos_recientes,
            'motoristas_activos': motoristas_activos,
            'motoristas_total': motoristas_total,
            'motos_disponibles': motos_disponibles,
            'motos_total': motos_total,
            'farmacias_total': farmacias_total,
            'tiempo_promedio': tiempo_promedio,
        }
        
        return render(request, self.template_name, context)


class DashboardRegionalView(RolRequiredMixin, View):
    """
    Dashboard Regional - acceso Gerente/Supervisor.
    Métricas por sucursal o región.
    """
    template_name = 'dashboard/dashboard_regional.html'
    roles_permitidos = ['ADMINISTRADOR', 'GERENTE', 'SUPERVISOR']

    def get(self, request):
        # Agrupar por región/comuna
        despachos_por_region = Farmacia.objects.values('region').annotate(
            total=Count('despacho')
        ).order_by('-total')
        
        despachos_por_estado = Despacho.objects.values('estado').annotate(
            total=Count('identificador_unico')
        ).order_by('-total')
        
        # Motoristas por rendimiento
        motoristas_rendimiento = Motorista.objects.annotate(
            total_despachos=Count('despacho')
        ).order_by('-total_despachos')[:10]
        
        context = {
            'despachos_por_region': despachos_por_region,
            'despachos_por_estado': despachos_por_estado,
            'motoristas_rendimiento': motoristas_rendimiento,
        }
        
        return render(request, self.template_name, context)


# ============================================
# VISTAS DE REPORTES
# ============================================

class ReporteCSVView(RolRequiredMixin, View):
    """
    Exportar reporte de despachos a CSV.
    Acceso: Gerente, Supervisor, Administrador.
    """
    roles_permitidos = ['GERENTE', 'SUPERVISOR', 'ADMINISTRADOR']

    def get(self, request):
        fecha_desde = request.GET.get('fecha_desde')
        fecha_hasta = request.GET.get('fecha_hasta')

        queryset = Despacho.objects.all()

        if fecha_desde:
            queryset = queryset.filter(fecha_hora_creacion__gte=fecha_desde)
        if fecha_hasta:
            queryset = queryset.filter(fecha_hora_creacion__lte=fecha_hasta)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="reporte_despachos.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'ID Despacho',
            'Tipo Movimiento',
            'Farmacia',
            'Motorista',
            'Estado',
            'Fecha Creación',
            'Fecha Toma Pedido',
            'Fecha Salida Farmacia',
            'Fecha Estimada Llegada',
            'Requiere Receta'
        ])

        for despacho in queryset:
            writer.writerow([
                despacho.identificador_unico,
                despacho.get_tipo_movimiento_display(),
                despacho.farmacia_origen.nombre if despacho.farmacia_origen else '',
                despacho.motorista_asignado.usuario.get_full_name() if despacho.motorista_asignado and despacho.motorista_asignado.usuario else '',
                despacho.get_estado_display(),
                despacho.fecha_hora_creacion.strftime('%Y-%m-%d %H:%M') if despacho.fecha_hora_creacion else '',
                despacho.fecha_hora_toma_pedido.strftime('%Y-%m-%d %H:%M') if despacho.fecha_hora_toma_pedido else '',
                despacho.fecha_hora_salida_farmacia.strftime('%Y-%m-%d %H:%M') if despacho.fecha_hora_salida_farmacia else '',
                despacho.fecha_hora_estimada_llegada.strftime('%Y-%m-%d %H:%M') if despacho.fecha_hora_estimada_llegada else '',
                'Sí' if despacho.tipo_movimiento == 'CON_RECETA' else 'No'
            ])

        return response


class ReportePDFView(RolRequiredMixin, View):
    """
    Exportar reporte de despachos a PDF.
    Acceso: Gerente, Supervisor, Administrador.
    """
    roles_permitidos = ['GERENTE', 'SUPERVISOR', 'ADMINISTRADOR']

    def get(self, request):
        fecha_desde = request.GET.get('fecha_desde')
        fecha_hasta = request.GET.get('fecha_hasta')

        queryset = Despacho.objects.all()
        if fecha_desde:
            queryset = queryset.filter(fecha_hora_creacion__gte=fecha_desde)
        if fecha_hasta:
            queryset = queryset.filter(fecha_hora_creacion__lte=fecha_hasta)

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []

        styles = getSampleStyleSheet()
        title = Paragraph("Reporte de Despachos", styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 0.3 * inch))

        # Header de la tabla
        data = [['ID Despacho', 'Tipo', 'Farmacia', 'Motorista', 'Estado', 'Fecha Creación', 'Requiere Receta']]

        for despacho in queryset[:100]:  # Limitar a 100 registros
            data.append([
                despacho.identificador_unico,
                despacho.get_tipo_movimiento_display(),
                despacho.farmacia_origen.nombre[:20] if despacho.farmacia_origen else '',
                despacho.motorista_asignado.usuario.get_full_name()[:20] if despacho.motorista_asignado and despacho.motorista_asignado.usuario else '',
                despacho.get_estado_display(),
                despacho.fecha_hora_creacion.strftime('%Y-%m-%d %H:%M') if despacho.fecha_hora_creacion else '',
                'Sí' if despacho.tipo_movimiento == 'CON_RECETA' else 'No'
            ])

        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), '#40466e'),
            ('TEXTCOLOR', (0, 0), (-1, 0), '#fff'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), '#f0f0f0'),
            ('GRID', (0, 0), (-1, -1), 1, '#ccc'),
        ]))

        elements.append(table)
        doc.build(elements)
        buffer.seek(0)

        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="reporte_despachos.pdf"'
        return response


# ============================================
# FUNCIONES AUXILIARES
# ============================================

def dashboard_general(request):
    """
    Dashboard General - vista por función.
    """
    if not request.user.is_authenticated:
        return redirect('login')
    
    # Verificar roles permitidos
    if request.user.rol not in ['ADMINISTRADOR', 'GERENTE']:
        messages.error(request, 'No tienes acceso al dashboard general.')
        return redirect('home')
    
    # Métricas generales
    total_despachos = Despacho.objects.count()
    despachos_pendientes = Despacho.objects.filter(estado='PENDIENTE').count()
    despachos_en_ruta = Despacho.objects.filter(estado='EN_RUTA').count()
    despachos_entregados = Despacho.objects.filter(estado='ENTREGADO').count()
    despachos_incidencias = Despacho.objects.filter(estado='INCIDENCIA').count()
    
    # Últimos 7 días
    hace_7_dias = timezone.now() - timedelta(days=7)
    despachos_recientes = Despacho.objects.filter(fecha_hora_creacion__gte=hace_7_dias).count()
    
    # Motoristas activos
    motoristas_activos = Motorista.objects.filter(licencia_vigente=True).count()
    motoristas_total = Motorista.objects.count()
    
    # Motos disponibles
    motos_disponibles = Moto.objects.filter(estado='OPERATIVO').count()
    motos_total = Moto.objects.count()
    
    # Farmacias
    farmacias_total = Farmacia.objects.count()
    
    # Tiempo promedio de entrega
    despachos_entregados_obj = Despacho.objects.filter(
        estado='ENTREGADO',
        fecha_hora_estimada_llegada__isnull=False,
        fecha_hora_despacho__isnull=False
    )
    
    if despachos_entregados_obj.exists():
        total_minutos = sum(
            int((d.fecha_hora_estimada_llegada - d.fecha_hora_despacho).total_seconds() / 60)
            for d in despachos_entregados_obj
        )
        tiempo_promedio = total_minutos // len(despachos_entregados_obj)
    else:
        tiempo_promedio = 0
    
    context = {
        'total_despachos': total_despachos,
        'despachos_pendientes': despachos_pendientes,
        'despachos_en_ruta': despachos_en_ruta,
        'despachos_entregados': despachos_entregados,
        'despachos_incidencias': despachos_incidencias,
        'despachos_recientes': despachos_recientes,
        'motoristas_activos': motoristas_activos,
        'motoristas_total': motoristas_total,
        'motos_disponibles': motos_disponibles,
        'motos_total': motos_total,
        'farmacias_total': farmacias_total,
        'tiempo_promedio': tiempo_promedio,
    }
    
    return render(request, 'dashboard/dashboard_general.html', context)


def dashboard_regional(request):
    """
    Dashboard Regional - vista por función.
    """
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.user.rol not in ['GERENTE', 'SUPERVISOR', 'ADMINISTRADOR']:
        messages.error(request, 'No tienes acceso al dashboard regional.')
        return redirect('home')
    
    # Agrupar por región
    despachos_por_region = Farmacia.objects.values('region').annotate(
        total=Count('despacho')
    ).order_by('-total')
    
    despachos_por_estado = Despacho.objects.values('estado').annotate(
        total=Count('identificador_unico')
    ).order_by('-total')
    
    # Motoristas por rendimiento
    motoristas_rendimiento = Motorista.objects.annotate(
        total_despachos=Count('despacho')
    ).order_by('-total_despachos')[:10]
    
    context = {
        'despachos_por_region': despachos_por_region,
        'despachos_por_estado': despachos_por_estado,
        'motoristas_rendimiento': motoristas_rendimiento,
    }
    
    return render(request, 'dashboard/dashboard_regional.html', context)


def reportes_filtro(request):
    """
    Vista principal de reportes: muestra historial de descargas y preview de despachos.
    """
    if request.user.rol not in ['GERENTE', 'SUPERVISOR', 'ADMINISTRADOR', 'OPERADOR']:
        messages.error(request, 'No tienes permiso para acceder a reportes.')
        return redirect('home')
    
    # ========== PARÁMETROS DE FILTRO ==========
    tipo_filtro = request.GET.get('tipo_filtro', 'diario')
    fecha = request.GET.get('fecha', '')
    mes = request.GET.get('mes', '')
    anio = request.GET.get('anio', '')
    motorista_id = request.GET.get('id_motorista', '')
    
    # Filtros para historial
    historial_desde = request.GET.get('historial_fecha_desde', '')
    historial_hasta = request.GET.get('historial_fecha_hasta', '')
    
    # ========== DESPACHOS (PREVIEW) ==========
    fecha_desde, fecha_hasta = rango_fechas_por_tipo(tipo_filtro, fecha, mes, anio)
    
    despachos = Despacho.objects.select_related(
        'farmacia_origen', 
        'motorista_asignado',
        'motorista_asignado__usuario'
    ).all()
    
    if fecha_desde:
        despachos = despachos.filter(fecha_hora_creacion__gte=fecha_desde)
    if fecha_hasta:
        despachos = despachos.filter(fecha_hora_creacion__lte=fecha_hasta)
    if motorista_id:
        despachos = despachos.filter(motorista_asignado__identificador_unico=motorista_id)
    
    despachos = despachos.order_by('-fecha_hora_creacion')
    
    # ========== HISTORIAL DE DESCARGAS ==========
    historial = ReportDownloadHistory.objects.filter(
        user=request.user
    ).select_related('motorista')
    
    if historial_desde:
        try:
            historial_desde_dt = datetime.strptime(historial_desde, '%Y-%m-%d')
            historial = historial.filter(fecha_descarga__gte=historial_desde_dt)
        except ValueError:
            pass
    
    if historial_hasta:
        try:
            historial_hasta_dt = datetime.strptime(historial_hasta, '%Y-%m-%d')
            historial_hasta_dt = historial_hasta_dt.replace(hour=23, minute=59, second=59)
            historial = historial.filter(fecha_descarga__lte=historial_hasta_dt)
        except ValueError:
            pass
    
    historial = historial[:50]  # Últimos 50 reportes
    
    # ========== ESTADÍSTICAS ==========
    total_despachos = despachos.count()
    estadisticas = despachos.aggregate(
        pendientes=Count('identificador_unico', filter=Q(estado='PENDIENTE')),
        en_ruta=Count('identificador_unico', filter=Q(estado='EN_RUTA')),
        entregados=Count('identificador_unico', filter=Q(estado='ENTREGADO')),
        con_incidencia=Count('identificador_unico', filter=Q(estado='INCIDENCIA'))
    )
    
    # ========== VALORES PARA FORMULARIO ==========
    hoy = datetime.now()
    if not fecha:
        fecha = hoy.strftime('%Y-%m-%d')
    if not mes:
        mes = hoy.strftime('%Y-%m')
    if not anio:
        anio = str(hoy.year)
    
    context = {
        'despachos': despachos[:100],  # Limitar preview a 100
        'historial': historial,
        'tipo_filtro': tipo_filtro,
        'fecha': fecha,
        'mes': mes,
        'anio': anio,
        'id_motorista': motorista_id,
        'historial_fecha_desde': historial_desde,
        'historial_fecha_hasta': historial_hasta,
        'total_despachos': total_despachos,
        'estadisticas': estadisticas,
        'motoristas': Motorista.objects.filter(activo=True),
    }
    
    return render(request, 'dashboard/dashboard_report_list.html', context)


def reporte_csv(request):
    """
    Generar y descargar reporte en formato CSV.
    """
    if request.user.rol not in ['GERENTE', 'SUPERVISOR', 'ADMINISTRADOR', 'OPERADOR']:
        messages.error(request, 'No tienes permiso para descargar reportes.')
        return redirect('home')
    
    # Obtener parámetros
    tipo_filtro = request.GET.get('tipo', 'general')
    fecha = request.GET.get('fecha', '')
    mes = request.GET.get('mes', '')
    anio = request.GET.get('anio', '')
    motorista_id = request.GET.get('id_motorista', '')
    
    # Calcular rango de fechas
    fecha_desde, fecha_hasta = rango_fechas_por_tipo(tipo_filtro, fecha, mes, anio)
    
    # Filtrar despachos
    queryset = Despacho.objects.select_related(
        'farmacia_origen',
        'motorista_asignado',
        'motorista_asignado__usuario'
    ).all()
    
    if fecha_desde:
        queryset = queryset.filter(fecha_hora_creacion__gte=fecha_desde)
    if fecha_hasta:
        queryset = queryset.filter(fecha_hora_creacion__lte=fecha_hasta)
    if motorista_id:
        queryset = queryset.filter(motorista_asignado__identificador_unico=motorista_id)
    
    queryset = queryset.order_by('-fecha_hora_creacion')
    
    # Generar nombre de archivo
    filename = generar_nombre_archivo(tipo_filtro, 'csv', fecha, mes, anio)
    
    # Crear CSV
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    writer.writerow([
        'ID Despacho',
        'Tipo Movimiento',
        'Farmacia',
        'Motorista',
        'Estado',
        'Fecha Creación',
        'Fecha Toma Pedido',
        'Fecha Salida Farmacia',
        'Fecha Estimada Llegada',
        'Tiempo Entrega (min)',
        'Dirección Entrega',
        'Requiere Receta'
    ])
    
    for despacho in queryset:
        writer.writerow([
            despacho.identificador_unico,
            despacho.get_tipo_movimiento_display(),
            despacho.farmacia_origen.nombre if despacho.farmacia_origen else '',
            despacho.motorista_asignado.nombre_completo if despacho.motorista_asignado else '',
            despacho.get_estado_display(),
            despacho.fecha_hora_creacion.strftime('%Y-%m-%d %H:%M') if despacho.fecha_hora_creacion else '',
            despacho.fecha_hora_toma_pedido.strftime('%Y-%m-%d %H:%M') if despacho.fecha_hora_toma_pedido else '',
            despacho.fecha_hora_salida_farmacia.strftime('%Y-%m-%d %H:%M') if despacho.fecha_hora_salida_farmacia else '',
            despacho.fecha_hora_estimada_llegada.strftime('%Y-%m-%d %H:%M') if despacho.fecha_hora_estimada_llegada else '',
            despacho.tiempo_entrega_minutos or '',
            despacho.direccion_entrega,
            'Sí' if despacho.tipo_movimiento == 'CON_RECETA' else 'No'
        ])
    
    # Registrar en historial
    ReportDownloadHistory.objects.create(
        user=request.user,
        tipo_reporte=tipo_filtro.upper(),
        formato='CSV',
        fecha_desde=fecha_desde.date() if fecha_desde else None,
        fecha_hasta=fecha_hasta.date() if fecha_hasta else None,
        motorista_id=motorista_id if motorista_id else None,
        cantidad_registros=queryset.count(),
        nombre_archivo=filename
    )
    
    return response


def reporte_pdf(request):
    """
    Generar y descargar reporte en formato PDF.
    """
    if request.user.rol not in ['GERENTE', 'SUPERVISOR', 'ADMINISTRADOR', 'OPERADOR']:
        messages.error(request, 'No tienes permiso para descargar reportes.')
        return redirect('home')
    
    # Obtener parámetros
    tipo_filtro = request.GET.get('tipo', 'general')
    fecha = request.GET.get('fecha', '')
    mes = request.GET.get('mes', '')
    anio = request.GET.get('anio', '')
    motorista_id = request.GET.get('id_motorista', '')
    
    # Calcular rango de fechas
    fecha_desde, fecha_hasta = rango_fechas_por_tipo(tipo_filtro, fecha, mes, anio)
    
    # Filtrar despachos
    queryset = Despacho.objects.select_related(
        'farmacia_origen',
        'motorista_asignado',
        'motorista_asignado__usuario'
    ).all()
    
    if fecha_desde:
        queryset = queryset.filter(fecha_hora_creacion__gte=fecha_desde)
    if fecha_hasta:
        queryset = queryset.filter(fecha_hora_creacion__lte=fecha_hasta)
    if motorista_id:
        queryset = queryset.filter(motorista_asignado__identificador_unico=motorista_id)
    
    queryset = queryset.order_by('-fecha_hora_creacion')[:100]  # Limitar PDF a 100
    
    # Generar nombre de archivo
    filename = generar_nombre_archivo(tipo_filtro, 'pdf', fecha, mes, anio)
    
    # Crear PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
    elements = []
    
    styles = getSampleStyleSheet()
    
    # Título
    if tipo_filtro == 'diario' and fecha:
        titulo = f"Reporte Diario de Despachos - {fecha}"
    elif tipo_filtro == 'mensual' and mes:
        titulo = f"Reporte Mensual de Despachos - {mes}"
    elif tipo_filtro == 'anual' and anio:
        titulo = f"Reporte Anual de Despachos - {anio}"
    else:
        titulo = "Reporte General de Despachos"
    
    title = Paragraph(titulo, styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 0.3*inch))
    
    # Información adicional
    info_text = f"Generado por: {request.user.get_full_name()} | Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    info = Paragraph(info_text, styles['Normal'])
    elements.append(info)
    elements.append(Spacer(1, 0.2*inch))
    
    # Tabla
    data = [[
        'ID', 'Tipo', 'Farmacia', 'Motorista', 
        'Estado', 'Fecha Creación', 'Tiempo (min)'
    ]]
    
    for despacho in queryset:
        data.append([
            str(despacho.identificador_unico),
            despacho.get_tipo_movimiento_display()[:15],
            (despacho.farmacia_origen.nombre[:20] if despacho.farmacia_origen else '')[:20],
            (despacho.motorista_asignado.nombre_completo[:20] if despacho.motorista_asignado else '')[:20],
            despacho.get_estado_display(),
            despacho.fecha_hora_creacion.strftime('%Y-%m-%d') if despacho.fecha_hora_creacion else '',
            str(despacho.tiempo_entrega_minutos or '-')
        ])
    
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#40466e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    # Registrar en historial
    ReportDownloadHistory.objects.create(
        user=request.user,
        tipo_reporte=tipo_filtro.upper(),
        formato='PDF',
        fecha_desde=fecha_desde.date() if fecha_desde else None,
        fecha_hasta=fecha_hasta.date() if fecha_hasta else None,
        motorista_id=motorista_id if motorista_id else None,
        cantidad_registros=len(queryset),
        nombre_archivo=filename
    )
    
    return response