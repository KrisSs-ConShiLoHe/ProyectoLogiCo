"""
Vistas de Dashboard y Reportes
"""
from django.shortcuts import render, redirect
from django.views.generic import View
from django.http import HttpResponse
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta, datetime
import csv
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from ..models import Despacho, Motorista, Farmacia, Moto, AsignacionMoto, AsignacionFarmacia, ReportDownloadHistory
from ..decorators import RolRequiredMixin, LoginRequiredMixin, GerenteOnlyMixin
from datetime import datetime
import dateparser
parse_date = dateparser.parse('2015, Ago 15, 1:08 pm')





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
            total=Count('id')
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
        total=Count('id')
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


def rango_fechas_por_tipo(tipo_reporte):
    hoy = datetime.now().date()
    if tipo_reporte == "diario":
        return hoy, hoy
    elif tipo_reporte == "mensual":
        primero = hoy.replace(day=1)
        return primero, hoy
    elif tipo_reporte == "anual":
        primero = hoy.replace(month=1, day=1)
        return primero, hoy
    return None, None

def reportes_filtro(request):
    """
    Muestra la pantalla de filtros (general, diario, mensual, anual), preview y botones de exportación.
    """
    tipo_filtro = request.GET.get("tipo_filtro", "diario")
    fecha_str = request.GET.get("fecha", "")
    mes_str = request.GET.get("mes", "")
    anio_str = request.GET.get("anio", "")
    motorista_id = request.GET.get("id_motorista", "")

    queryset = Despacho.objects.all()

    fecha_desde, fecha_hasta = None, None
    if tipo_filtro == "diario" and fecha_str:
        fecha_desde = fecha_hasta = parse_date(fecha_str)
    elif tipo_filtro == "mensual" and mes_str:
        fecha_desde = parse_date(mes_str + "-01")
        if fecha_desde.month == 12:
            next_month = fecha_desde.replace(year=fecha_desde.year + 1, month=1, day=1)
        else:
            next_month = fecha_desde.replace(month=fecha_desde.month + 1, day=1)
        fecha_hasta = next_month - timedelta(days=1)
    elif tipo_filtro == "anual" and anio_str.isdigit():
        fecha_desde = datetime(int(anio_str), 1, 1)
        fecha_hasta = datetime(int(anio_str), 12, 31)

    if fecha_desde:
        queryset = queryset.filter(fecha_hora_creacion__gte=fecha_desde)
    if fecha_hasta:
        queryset = queryset.filter(fecha_hora_creacion__lte=fecha_hasta)
    if motorista_id:
        queryset = queryset.filter(motorista_asignado__identificador_unico=motorista_id)

    # Puedes limitar resultados si es necesario: .order_by('-fecha_hora_creacion')[:100]
    return render(request, "dashboard/dashboard_report_list.html", {
        "despachos": queryset,
        "tipo_filtro": tipo_filtro,
        "fecha": fecha_str,
        "mes": mes_str,
        "anio": anio_str,
        "id_motorista": motorista_id,
    })

def reporte_csv(request):
    if not request.user.is_authenticated:
        return redirect('login')

    # Permisos
    if request.user.rol not in ['GERENTE', 'SUPERVISOR', 'ADMINISTRADOR', 'OPERADOR']:
        messages.error(request, 'No tienes permiso para descargar reportes.')
        return redirect('home')

    # Obten los filtros desde GET (puedes usar POST si prefieres)
    tipo_filtro = request.GET.get("tipo_filtro", "diario")
    fecha_str = request.GET.get("fecha", "")
    mes_str = request.GET.get("mes", "")
    anio_str = request.GET.get("anio", "")
    motorista_id = request.GET.get("id_motorista", "")  # Cambia a id_motorista para consistencia

    fecha_desde, fecha_hasta = None, None

    # Calcular rangos de fecha según filtro
    if tipo_filtro == "diario" and fecha_str:
        fecha_desde = fecha_hasta = parse_date(fecha_str)
    elif tipo_filtro == "mensual" and mes_str:
        fecha_desde = parse_date(mes_str + "-01")
        if fecha_desde.month == 12:
            next_month = fecha_desde.replace(year=fecha_desde.year + 1, month=1, day=1)
        else:
            next_month = fecha_desde.replace(month=fecha_desde.month + 1, day=1)
        fecha_hasta = next_month - timedelta(days=1)
    elif tipo_filtro == "anual" and anio_str.isdigit():
        fecha_desde = datetime(int(anio_str), 1, 1)
        fecha_hasta = datetime(int(anio_str), 12, 31)
    elif tipo_filtro == "general":
        fecha_desde, fecha_hasta = None, None

    queryset = Despacho.objects.all()
    if fecha_desde:
        queryset = queryset.filter(fecha_hora_creacion__gte=fecha_desde)
    if fecha_hasta:
        queryset = queryset.filter(fecha_hora_creacion__lte=fecha_hasta)
    if motorista_id:
        queryset = queryset.filter(motorista_asignado__identificador_unico=motorista_id)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="reporte_despachos.csv"'
    writer = csv.writer(response)
    writer.writerow([
        'ID Pedido',
        'Tipo Movimiento',
        'Farmacia',
        'Motorista',
        'Estado',
        'Fecha Creación',
        'Fecha Despacho',
        'Fecha Entrega',
        'Tiempo Entrega (min)',
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
            despacho.fecha_hora_despacho.strftime('%Y-%m-%d %H:%M') if despacho.fecha_hora_despacho else '',
            despacho.fecha_hora_estimada_llegada.strftime('%Y-%m-%d %H:%M') if despacho.fecha_hora_estimada_llegada else '',
            despacho.tiempo_entrega_minutos or '',
            'Sí' if despacho.requiere_receta else 'No'
        ])

    return response


def reporte_pdf(request):
    """
    Exportar reporte PDF - vista por función.
    """
    if not request.user.is_authenticated:
        return redirect('login')
    

    tipo_reporte = request.GET.get("tipo", "diario")
    fecha_desde, fecha_hasta = rango_fechas_por_tipo(tipo_reporte)


    if request.user.rol not in ['GERENTE', 'SUPERVISOR', 'ADMINISTRADOR', 'OPERADOR']:
        messages.error(request, 'No tienes permiso para descargar reportes.')
        return redirect('home')
    
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
    elements.append(Spacer(1, 0.3*inch))
    
    data = [['ID Pedido', 'Tipo', 'Farmacia', 'Motorista', 'Estado', 'Fecha Creación']]
    
    for despacho in queryset[:100]:
        data.append([
            despacho.identificador_unico,
            despacho.get_tipo_movimiento_display(),
            despacho.farmacia_origen.nombre[:20] if despacho.farmacia_origen else '',
            despacho.motorista_asignado.usuario.get_full_name()[:20] if despacho.motorista_asignado and despacho.motorista_asignado.usuario else '',
            despacho.get_estado_display(),
            despacho.fecha_hora_creacion.strftime('%Y-%m-%d') if despacho.fecha_hora_creacion else ''
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


def puede_descargar(user, tipo):
    if user.rol in ['ADMINISTRADOR', 'GERENTE'] and tipo in ['diario', 'mensual', 'anual']:
        return True
    if user.rol in ['SUPERVISOR', 'OPERADOR'] and tipo == 'diario':
        return True
    return False
