from datetime import datetime, timedelta
from django.utils import timezone

def rango_fechas_por_tipo(tipo_filtro, fecha=None, mes=None, anio=None):
    """
    Calcula el rango de fechas según el tipo de filtro y parámetros.
    
    Args:
        tipo_filtro: 'general', 'diario', 'mensual', 'anual'
        fecha: str en formato 'YYYY-MM-DD' (para diario)
        mes: str en formato 'YYYY-MM' (para mensual)
        anio: str o int (para anual)
    
    Returns:
        tuple: (fecha_desde, fecha_hasta) como objetos datetime
    """
    hoy = timezone.now().date()
    
    if tipo_filtro == 'diario':
        if fecha:
            try:
                fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                fecha_obj = hoy
        else:
            fecha_obj = hoy
        
        fecha_desde = timezone.make_aware(datetime.combine(fecha_obj, datetime.min.time()))
        fecha_hasta = timezone.make_aware(datetime.combine(fecha_obj, datetime.max.time()))
        
    elif tipo_filtro == 'mensual':
        if mes:
            try:
                fecha_obj = datetime.strptime(mes, '%Y-%m').date()
            except (ValueError, TypeError):
                fecha_obj = hoy
        else:
            fecha_obj = hoy
        
        primer_dia = fecha_obj.replace(day=1)
        # Último día del mes
        if fecha_obj.month == 12:
            ultimo_dia = fecha_obj.replace(year=fecha_obj.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            ultimo_dia = fecha_obj.replace(month=fecha_obj.month + 1, day=1) - timedelta(days=1)
        
        fecha_desde = timezone.make_aware(datetime.combine(primer_dia, datetime.min.time()))
        fecha_hasta = timezone.make_aware(datetime.combine(ultimo_dia, datetime.max.time()))
        
    elif tipo_filtro == 'anual':
        if anio:
            try:
                anio_int = int(anio)
            except (ValueError, TypeError):
                anio_int = hoy.year
        else:
            anio_int = hoy.year
        
        primer_dia = datetime(anio_int, 1, 1).date()
        ultimo_dia = datetime(anio_int, 12, 31).date()
        
        fecha_desde = timezone.make_aware(datetime.combine(primer_dia, datetime.min.time()))
        fecha_hasta = timezone.make_aware(datetime.combine(ultimo_dia, datetime.max.time()))
        
    else:  # general
        fecha_desde = None
        fecha_hasta = None
    
    return fecha_desde, fecha_hasta


def generar_nombre_archivo(tipo_filtro, formato, fecha=None, mes=None, anio=None):
    """
    Genera un nombre de archivo descriptivo para el reporte.
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if tipo_filtro == 'diario' and fecha:
        fecha_str = fecha.replace('-', '')
        return f"reporte_diario_{fecha_str}_{timestamp}.{formato.lower()}"
    elif tipo_filtro == 'mensual' and mes:
        mes_str = mes.replace('-', '')
        return f"reporte_mensual_{mes_str}_{timestamp}.{formato.lower()}"
    elif tipo_filtro == 'anual' and anio:
        return f"reporte_anual_{anio}_{timestamp}.{formato.lower()}"
    else:
        return f"reporte_general_{timestamp}.{formato.lower()}"