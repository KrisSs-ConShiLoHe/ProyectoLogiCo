# signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Moto, AsignacionMoto # Asegúrate de que los modelos estén importados
from django.utils import timezone

@receiver(post_save, sender=Moto)
def sincronizar_asignacion_con_moto(sender, instance, created, **kwargs):
    # Obtener los campos actualizados, si existen
    update_fields = kwargs.get('update_fields')
    
    # CONDICIÓN CRÍTICA DE ESCAPE: Solo procede si es una creación 
    # O si los campos de asignación (duenio/motorista_asignado) fueron modificados.
    if not created and update_fields and not ('duenio' in update_fields or 'motorista_asignado' in update_fields):
        return
    """
    Gestiona la creación/actualización de AsignacionMoto cuando el campo
    motorista_asignado en el modelo Moto es modificado.
    """
    
    # Solo actuamos si el dueño es MOTORISTA y se asignó un motorista.
    if instance.duenio == "MOTORISTA" and instance.motorista_asignado:
        
        motorista_nuevo = instance.motorista_asignado
        
        # Intentar encontrar una asignación activa para esta moto
        asignacion_activa = AsignacionMoto.objects.filter(moto=instance, activa=True).first()
        
        if asignacion_activa:
            # Caso 1: Actualización de Asignación Existente
            if asignacion_activa.motorista != motorista_nuevo:
                # 1. Desactivar la asignación anterior (libera el motorista viejo)
                asignacion_activa.activa = False
                asignacion_activa.fecha_desasignacion = timezone.now()
                asignacion_activa.save() # El save() de AsignacionMoto hará la limpieza.
                
                # 2. Crear nueva asignación
                AsignacionMoto.objects.create(
                    moto=instance,
                    motorista=motorista_nuevo,
                    activa=True
                )
        
        elif created or (kwargs.get('update_fields') and 'motorista_asignado' in kwargs.get('update_fields')):
            # Caso 2: Creación Inicial (Si no había asignación activa)
            AsignacionMoto.objects.create(
                moto=instance,
                motorista=motorista_nuevo,
                activa=True
            )
            
    # Manejar desasignación (Si el motorista_asignado fue puesto en NULL)
    elif instance.duenio == "EMPRESA" or (instance.motorista_asignado is None and not created):
        asignacion_activa = AsignacionMoto.objects.filter(moto=instance, activa=True).first()
        if asignacion_activa:
            asignacion_activa.activa = False
            asignacion_activa.fecha_desasignacion = timezone.now()
            asignacion_activa.save() # Esto libera la moto y motorista.