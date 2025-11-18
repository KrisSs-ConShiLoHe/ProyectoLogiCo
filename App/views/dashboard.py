"""
Vistas de Dashboard y Reportes
"""
from django.shortcuts import render, redirect
from django.views.generic import View
from django.http import HttpResponse
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
import csv
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from ..models import Despacho, Motorista, Farmacia, Moto, AsignacionMoto, AsignacionFarmacia
from ..decorators import RolRequiredMixin, LoginRequiredMixin, GerenteOnlyMixin


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
        if request.user.rol not in ['ADMINISTRADOR', 'SUPERVISOR', 'GERENTE']:
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
        motos_disponibles = Moto.objects.filter(disponible=True).count()
        motos_total = Moto.objects.count()
        
        # Farmacias
        farmacias_total = Farmacia.objects.count()
        
        # Tiempo promedio de entrega (en minutos)
        despachos_entregados_obj = Despacho.objects.filter(
            estado='ENTREGADO',
            fecha_hora_entrega__isnull=False,
            fecha_hora_despacho__isnull=False
        )
        
        if despachos_entregados_obj.exists():
            total_minutos = sum(
                int((d.fecha_hora_entrega - d.fecha_hora_despacho).total_seconds() / 60)
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
    roles_permitidos = ['GERENTE', 'SUPERVISOR']

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
    Acceso: Gerente, Supervisor.
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
        
        # Crear respuesta CSV
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
                despacho.id_pedido_externo,
                despacho.get_tipo_movimiento_display(),
                despacho.farmacia_origen.nombre,
                despacho.motorista_asignado.usuario.get_full_name(),
                despacho.get_estado_display(),
                despacho.fecha_hora_creacion.strftime('%Y-%m-%d %H:%M'),
                despacho.fecha_hora_despacho.strftime('%Y-%m-%d %H:%M') if despacho.fecha_hora_despacho else '',
                despacho.fecha_hora_entrega.strftime('%Y-%m-%d %H:%M') if despacho.fecha_hora_entrega else '',
                despacho.tiempo_entrega_minutos or '',
                'Sí' if despacho.requiere_receta else 'No'
            ])
        
        return response


class ReportePDFView(RolRequiredMixin, View):
    """
    Exportar reporte de despachos a PDF.
    Acceso: Gerente, Supervisor.
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
        
        # Crear PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        
        styles = getSampleStyleSheet()
        
        # Título
        title = Paragraph("Reporte de Despachos", styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 0.3*inch))
        
        # Tabla
        data = [['ID Pedido', 'Tipo', 'Farmacia', 'Motorista', 'Estado', 'Fecha Creación']]
        
        for despacho in queryset[:100]:  # Limitar a 100 registros
            data.append([
                despacho.id_pedido_externo,
                despacho.get_tipo_movimiento_display(),
                despacho.farmacia_origen.nombre[:20],
                despacho.motorista_asignado.usuario.get_full_name()[:20],
                despacho.get_estado_display(),
                despacho.fecha_hora_creacion.strftime('%Y-%m-%d')
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
        
        # Generar PDF
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
    if request.user.rol not in ['ADMINISTRADOR', 'SUPERVISOR', 'GERENTE']:
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
    motos_disponibles = Moto.objects.filter(disponible=True).count()
    motos_total = Moto.objects.count()
    
    # Farmacias
    farmacias_total = Farmacia.objects.count()
    
    # Tiempo promedio de entrega
    despachos_entregados_obj = Despacho.objects.filter(
        estado='ENTREGADO',
        fecha_hora_entrega__isnull=False,
        fecha_hora_despacho__isnull=False
    )
    
    if despachos_entregados_obj.exists():
        total_minutos = sum(
            int((d.fecha_hora_entrega - d.fecha_hora_despacho).total_seconds() / 60)
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


def reporte_csv(request):
    """
    Exportar reporte CSV - vista por función.
    """
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.user.rol not in ['GERENTE', 'SUPERVISOR', 'ADMINISTRADOR']:
        messages.error(request, 'No tienes permiso para descargar reportes.')
        return redirect('home')
    
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
            despacho.id_pedido_externo,
            despacho.get_tipo_movimiento_display(),
            despacho.farmacia_origen.nombre,
            despacho.motorista_asignado.usuario.get_full_name(),
            despacho.get_estado_display(),
            despacho.fecha_hora_creacion.strftime('%Y-%m-%d %H:%M'),
            despacho.fecha_hora_despacho.strftime('%Y-%m-%d %H:%M') if despacho.fecha_hora_despacho else '',
            despacho.fecha_hora_entrega.strftime('%Y-%m-%d %H:%M') if despacho.fecha_hora_entrega else '',
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
    
    if request.user.rol not in ['GERENTE', 'SUPERVISOR', 'ADMINISTRADOR']:
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
            despacho.id_pedido_externo,
            despacho.get_tipo_movimiento_display(),
            despacho.farmacia_origen.nombre[:20],
            despacho.motorista_asignado.usuario.get_full_name()[:20],
            despacho.get_estado_display(),
            despacho.fecha_hora_creacion.strftime('%Y-%m-%d')
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
