from django.db import models, transaction
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db.models import UniqueConstraint, Q
from django.utils import timezone
from django.conf import settings
# 1. USER EXTENDIDO CON ROL (RBAC)
class User(AbstractUser):
    groups = models.ManyToManyField(
        Group,
        related_name='custom_user_groups',
        blank=True
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='custom_user_permissions',
        blank=True
    )

    ROLES = (
        ('ADMINISTRADOR', 'Administrador'),
        ('GERENTE', 'Gerente'),
        ('SUPERVISOR', 'Supervisor'),
        ('OPERADOR', 'Operador'),
        ('MOTORISTA', 'Motorista'),
    )
    rol = models.CharField(max_length=30, choices=ROLES)

    def __str__(self):
        return f"{self.username} ({self.rol})"

# 2. BASE FARMACIA
class Farmacia(models.Model):
    identificador_unico = models.CharField(max_length=50, unique=True)  # Identificador único
    nombre = models.CharField(max_length=255, default="Cruz Verde", editable=False)
    direccion = models.CharField(max_length=255)

    LAS_REGIONES = (
    ('REGIÓN DE ARICA Y PARINACOTA', 'Arica y Parinacota'),
    ('REGIÓN DE TARAPACÁ', 'Tarapacá'),
    ('REGIÓN DE ANTOFAGASTA', 'Antofagasta'),
    ('REGIÓN DE ATACAMA', 'Atacama'),
    ('REGIÓN DE COQUIMBO', 'Coquimbo'),
    ('REGIÓN DE VALPARAÍSO', 'Valparaíso'),
    ('REGIÓN METROPOLITANA DE SANTIAGO', 'Metropolitana de Santiago'),
    ('REGIÓN DE O HIGGINS', 'O Higgins'),
    ('REGIÓN DEL MAULE', 'Maule'),
    ('REGIÓN DE ÑUBLE', 'Ñuble'),
    ('REGIÓN DEL BIOBÍO ', 'Biobío'),
    ('REGIÓN DE LA ARAUCANÍA', 'Araucanía'),
    ('REGIÓN DE LOS RÍOS', 'Ríos'),
    ('REGIÓN DE LOS LAGOS', 'Lagos'),
    ('REGIÓN DE AYSÉN DEL GENERAL CARLOS IBÁÑEZ DEL CAMPO', 'Aysén del General Carlos Ibáñez del Campo'),
    ('REGIÓN DE MAGALLANES Y LA ANTÁRTICA CHILENA', 'Magallanes y la Antártica Chilena'),
)

    region = models.CharField(max_length=500, default='REGIÓN METROPOLITANA DE SANTIAGO', help_text="Seleccione una o más regiones, separadas por coma", choices=LAS_REGIONES)

    def get_region_list(self):
        if self.region:
            return [r.strip() for r in self.region.split(',')]
        return []

    def set_region_list(self, regions_list):
        if isinstance(regions_list, list):
            self.region = ','.join(regions_list)
        else:
            self.region = regions_list
    comuna = models.CharField(max_length=100)
    horario_recepcion_inicio = models.TimeField(help_text="Hora de inicio de la ventana de recepción (HH:MM:SS).")
    horario_recepcion_fin = models.TimeField(help_text="Hora de fin de la ventana de recepción (HH:MM:SS).") 
    
    DIAS_SEMANA = (
        ('LUN', 'Lunes'),
        ('MAR', 'Martes'),
        ('MIE', 'Miércoles'),
        ('JUE', 'Jueves'),
        ('VIE', 'Viernes'),
        ('SAB', 'Sábado'),
        ('DOM', 'Domingo'),
)

    dias_operativos = models.CharField(max_length=120, help_text="Seleccione los días de la semana en que la farmacia recibe despachos. Guardado como coma separado.")

    def get_dias_operativos_list(self):
        # Retorna dias_operativos como lista separando por coma
        if self.dias_operativos:
            return self.dias_operativos.split(',')
        return []

    def set_dias_operativos_list(self, dias_list):
        # Recibe lista y guarda como cadena separada por coma
        if isinstance(dias_list, list):
            self.dias_operativos = ','.join(dias_list)
        else:
            self.dias_operativos = dias_list

    # NUEVO MÉTODO AUXILIAR PARA OBTENER ETIQUETAS DE DÍAS OPERATIVOS
    def get_dias_operativos_labels(self):
        # Creamos un diccionario de mapeo {clave: etiqueta}
        dias_map = dict(self.DIAS_SEMANA)
        
        # Obtenemos la lista de claves guardadas (ej: ['LUN', 'MAR'])
        codes = self.get_dias_operativos_list()
        
        # Mapeamos cada clave a su etiqueta legible
        return [dias_map.get(code, code) for code in codes]

    telefono = models.CharField(max_length=30, blank=True, null=True)
    correo = models.EmailField(blank=True, null=True)
    activa = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        # Limpieza de dias_operativos
        if self.dias_operativos and isinstance(self.dias_operativos, str):
            self.dias_operativos = ','.join([d.strip() for d in self.dias_operativos.split(',')])
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre} ({self.identificador_unico}) - {self.region}, {self.comuna}"

        # if isinstance(self.dias_operativos, list):
        #     self.dias_operativos = ','.join(self.dias_operativos)
        # elif self.dias_operativos:
        #     # Clean any extraneous spaces
        #     self.dias_operativos = ','.join([d.strip() for d in self.dias_operativos.split(',')])
        # super().save(*args, **kwargs)

    imagen = models.ImageField(upload_to='farmacias/', blank=True, null=True)    # Campo para imagen

    def __str__(self):
        return f"{self.nombre} ({self.identificador_unico}) - {self.region}, {self.comuna}"

# 3. BASE MOTORISTA
class Motorista(models.Model):
    identificador_unico = models.CharField(max_length=40, unique=True)  # ID único
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, limit_choices_to={'rol': 'MOTORISTA'})
    nombre = models.CharField(max_length=100)
    apellido_paterno = models.CharField(max_length=100)
    apellido_materno = models.CharField(max_length=100)
    rut = models.CharField(max_length=16, unique=True)
    domicilio = models.CharField(max_length=150, blank=True, null=True)
    correo = models.EmailField(blank=True, null=True)
    telefono = models.CharField(max_length=30, blank=True, null=True)
    emergencia_nombre = models.CharField(max_length=100, blank=True, null=True)
    emergencia_telefono = models.CharField(max_length=30, blank=True, null=True)
    licencia_tipo = models.CharField(max_length=40, blank=True, null=True)  # Tipo de licencia
    licencia_vigente = models.BooleanField(default=False)   # Estado de licencia

    ESTADOS_DISPONIBILIDAD = (
    ('DISPONIBLE', 'Disponible'),
    ('ASIGNADO', 'Asignado'),
    ('EN_DESPACHO', 'En Despacho'),
    ('EN_DESCANSO', 'En Descanso'),
    ('CON_LICENCIA', 'Con Licencia'),
    ('INACTIVO', 'Inactivo'),
)

    disponibilidad = models.CharField(max_length=20, choices=ESTADOS_DISPONIBILIDAD, default='DISPONIBLE')

    TIENE_MOTO = (
        ('SIN_MOTO', 'Sin Moto'),
        ('CON_MOTO', 'Con Moto'),
    )

    posesion_moto = models.CharField(max_length=20, choices=TIENE_MOTO, default='SIN_MOTO')

    imagen = models.ImageField(upload_to='motoristas/', blank=True, null=True) # Foto motorista
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} {self.apellido_paterno} ({self.rut})"

# 4. BASE MOTO
class Moto(models.Model):
    identificador_unico = models.CharField(max_length=50, unique=True)
    patente = models.CharField(max_length=16, unique=True)              # Matrícula/placa
    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=50)
    color = models.CharField(max_length=40, blank=True, null=True)
    anio_fabricacion = models.IntegerField(blank=True, null=True)
    numero_chasis = models.CharField(max_length=60, blank=True, null=True)
    numero_motor = models.CharField(max_length=60, blank=True, null=True)
    permiso_circulacion_vigente = models.BooleanField(default=False)
    revision_tecnica_vigente = models.BooleanField(default=False)
    consumo_combustible = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text='L/100km')
    capacidad_carga = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, help_text='En Kg')

    ESTADOS_VEHICULO = (
    ('OPERATIVO', 'Operativo'),
    ('OCUPADO', 'Ocupado'),
    ('EN_TALLER', 'En Taller'),
    ('FUERA_DE_SERVICIO', 'Fuera de Servicio'),
    ('EN_MANTENIMIENTO', 'En Mantenimiento'),
)

    estado = models.CharField(max_length=20, choices=ESTADOS_VEHICULO, default='OPERATIVO')
    imagen = models.ImageField(upload_to='motos/', blank=True, null=True)

    # Datos de rendimiento
    velocidad_promedio = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text='Km/h')
    frenadas_bruscas = models.PositiveIntegerField(default=0, help_text='Por día')
    aceleraciones_rapidas = models.PositiveIntegerField(default=0, help_text='Por día')
    tiempo_inactividad_horas = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text='Horas')

    def __str__(self):
        return f"{self.patente} - {self.marca} {self.modelo}"


# Historial de mantenimientos (uno a muchos)
class MantenimientoMoto(models.Model):
    moto = models.ForeignKey(Moto, on_delete=models.CASCADE, related_name='mantenimientos')
    fecha_mantenimiento = models.DateField()
    descripcion = models.TextField()
    tipo_servicio = models.CharField(max_length=60) # Ej: "Aceite", "Neumáticos", "Reparación"
    kilometraje = models.PositiveIntegerField(blank=True, null=True)
    proximo_mantenimiento = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"Manten. {self.tipo_servicio} ({self.fecha_mantenimiento}) de {self.moto.patente}"


# 5. ASIGNACIÓN MOTO A MOTORISTA
class AsignacionMoto(models.Model):
    motorista = models.ForeignKey(Motorista, on_delete=models.CASCADE)
    moto = models.ForeignKey(Moto, on_delete=models.CASCADE)
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    fecha_desasignacion = models.DateTimeField(null=True, blank=True)
    activa = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['motorista'], condition=Q(activa=True), name='motorista_una_asignacion_activa1'),
            models.UniqueConstraint(fields=['moto'], condition=Q(activa=True), name='moto_una_asignacion_activa1'),
        ]
        ordering = ['-fecha_asignacion']

    def save(self, *args, **kwargs):
        with transaction.atomic():
            super().save(*args, **kwargs)
            if self.activa:
                # Desactivar otras asignaciones activas y liberar sus recursos
                AsignacionMoto.objects.filter(
                    motorista=self.motorista, activa=True
                ).exclude(pk=self.pk).update(activa=False, fecha_desasignacion=timezone.now())
                AsignacionMoto.objects.filter(
                    moto=self.moto, activa=True
                ).exclude(pk=self.pk).update(activa=False, fecha_desasignacion=timezone.now())
                # Marcar ambos como ocupados
                self.motorista.posesion_moto = 'CON_MOTO'
                self.motorista.save(update_fields=['posesion_moto'])
                self.moto.estado = 'OCUPADO'
                self.moto.save(update_fields=['estado'])
            else:
                if not self.fecha_desasignacion:
                    self.fecha_desasignacion = timezone.now()
                    AsignacionMoto.objects.filter(pk=self.pk).update(fecha_desasignacion=self.fecha_desasignacion)
                # Liberar recursos solo si NO tienen otra asignación activa
                if not AsignacionMoto.objects.filter(motorista=self.motorista, activa=True).exclude(pk=self.pk).exists():
                    self.motorista.posesion_moto = 'SIN_MOTO'
                    self.motorista.save(update_fields=['posesion_moto'])
                if not AsignacionMoto.objects.filter(moto=self.moto, activa=True).exclude(pk=self.pk).exists():
                    self.moto.estado = 'OPERATIVO'
                    self.moto.save(update_fields=['estado'])


    @property
    def duracion(self):
        """Retorna la duración de la asignación"""
        if self.activa:
            return timezone.now() - self.fecha_asignacion
        elif self.fecha_desasignacion:
            return self.fecha_desasignacion - self.fecha_asignacion
        return None
    
    @property
    def dias_asignado(self):
        """Retorna días de duración"""
        duracion = self.duracion
        return duracion.days if duracion else 0


# 6. ASIGNACIÓN MOTORISTA A FARMACIA
class AsignacionFarmacia(models.Model):
    motorista = models.ForeignKey(Motorista, on_delete=models.CASCADE)
    farmacia = models.ForeignKey(Farmacia, on_delete=models.CASCADE)
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    fecha_desasignacion = models.DateTimeField(null=True, blank=True)
    activa = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['motorista'], condition=Q(activa=True), name='motorista_una_asignacion_activa2'),
            # models.UniqueConstraint(fields=['farmacia'], condition=Q(activa=True), name='farmacia_una_asignacion_activa2'),
        ]
        ordering = ['-fecha_asignacion']

    def __str__(self):
        return f"{self.motorista} → {self.farmacia} ({'Activa' if self.activa else 'Inactiva'})"

    def save(self, *args, **kwargs):
        with transaction.atomic():
            # super().save(*args, **kwargs)
            if self.activa:
                # Desactivar otras asignaciones activas y liberar sus recursos
                AsignacionFarmacia.objects.filter(
                    motorista=self.motorista, activa=True
                ).exclude(pk=self.pk).update(activa=False, fecha_desasignacion=timezone.now())
                super().save(*args, **kwargs)
                # AsignacionFarmacia.objects.filter(
                #     farmacia=self.farmacia, activa=True
                # ).exclude(pk=self.pk).update(activa=False, fecha_desasignacion=timezone.now())
                # Marcar ambos como ocupados
                self.motorista.disponibilidad = 'ASIGNADO'
                self.motorista.save(update_fields=['disponibilidad'])

            else:
                super().save(*args, **kwargs)
                if not self.fecha_desasignacion:
                    self.fecha_desasignacion = timezone.now()

                    AsignacionFarmacia.objects.filter(pk=self.pk).update(fecha_desasignacion=self.fecha_desasignacion)
                # Liberar recursos solo si NO tienen otra asignación activa
                if not AsignacionFarmacia.objects.filter(motorista=self.motorista, activa=True).exclude(pk=self.pk).exists():
                    self.motorista.disponibilidad = 'DISPONIBLE'
                    self.motorista.save(update_fields=['disponibilidad'])

    @property
    def duracion(self):
        """Retorna la duración de la asignación"""
        if self.activa:
            return timezone.now() - self.fecha_asignacion
        elif self.fecha_desasignacion:
            return self.fecha_desasignacion - self.fecha_asignacion
        return None
    
    @property
    def dias_asignado(self):
        """Retorna días de duración"""
        duracion = self.duracion
        return duracion.days if duracion else 0

# 7. DESPACHO - TRAZABILIDAD Y MOVIMIENTO
class Despacho(models.Model):
    identificador_unico = models.CharField(max_length=50, unique=True)
    farmacia_origen = models.ForeignKey(Farmacia, on_delete=models.CASCADE)
    motorista_asignado = models.ForeignKey(Motorista, on_delete=models.CASCADE)
    fecha_hora_creacion = models.DateTimeField(auto_now_add=True)
    fecha_hora_toma_pedido = models.DateTimeField(null=True, blank=True)
    fecha_hora_salida_farmacia = models.DateTimeField(null=True, blank=True)
    fecha_hora_despacho = models.DateTimeField(null=True, blank=True)
    fecha_hora_estimada_llegada = models.DateTimeField(blank=True, null=True)
    direccion_entrega = models.CharField(max_length=255)

    # Estado y seguimiento
    ESTADOS = (
        ('PENDIENTE', 'Pendiente'),
        ('EN_RUTA', 'En Ruta'),
        ('ENTREGADO', 'Entregado'),
        ('INCIDENCIA', 'Incidencia'),
        ('ANULADO', 'Anulado'),
        ('REENVIO', 'Reenvío'),
    )

    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    incidencia_motivo = models.TextField(blank=True, null=True)
    incidencia_fecha_hora = models.DateTimeField(blank=True, null=True)
    motivo_reenvio = models.TextField(blank=True, null=True)

    # Tipo de movimiento
    MOVIMIENTOS = (
        ('DIRECTO', 'Directo'),
        ('CON_RECETA', 'Con Receta'),
        ('CON_TRASLADO', 'Con Traslado'),
        ('REENVIO', 'Reenvío'),
    )
    
    tipo_movimiento = models.CharField(max_length=20, choices=MOVIMIENTOS)
    
    # Campos para receta y traslado
    numero_receta = models.CharField(max_length=50, blank=True, null=True)
    fecha_emision_receta = models.DateField(blank=True, null=True)
    medico_prescribiente = models.CharField(max_length=100, blank=True, null=True)
    paciente_nombre = models.CharField(max_length=100, blank=True, null=True)
    paciente_edad = models.IntegerField(blank=True, null=True)
    tipo_establecimiento_traslado = models.CharField(max_length=100, blank=True, null=True)
    
    imagen = models.ImageField(upload_to='despachos/', blank=True, null=True)
    # Fecha creación y salida
    # Removed duplicate field below
    # fecha_hora_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Despacho {self.identificador_unico} ({self.get_estado_display()})"

    @property
    def requiere_receta(self):
        """
        Retorna True si el despacho tiene una receta asociada; False si no.
        Puedes ajustar la lógica para que dependa de tus reglas de negocio.
        """
        return bool(self.numero_receta and self.fecha_emision_receta)
    
    @property
    def tiempo_entrega_minutos(self):
        if self.fecha_hora_salida_farmacia and self.fecha_hora_estimada_llegada:
            diff = self.fecha_hora_estimada_llegada - self.fecha_hora_salida_farmacia
            return int(diff.total_seconds() // 60)
        else:
            return None
    
    class Meta:
        permissions = [
            ("can_view_dashboard_general", "Puede ver el dashboard general"),
            ("can_view_dashboard_regional", "Puede ver el dashboard regional"),
            ("can_export_csv", "Puede exportar CSV"),
            ("can_export_pdf", "Puede exportar PDF"),
        ]


# Contenido del pedido (productos asociados al despacho)
class ProductoPedido(models.Model):
    despacho = models.ForeignKey(Despacho, on_delete=models.CASCADE, related_name='productos')
    codigo_producto = models.CharField(max_length=100)
    nombre_producto = models.CharField(max_length=150)
    cantidad = models.PositiveIntegerField()
    numero_lote = models.CharField(max_length=60, blank=True, null=True)
    numero_serie = models.CharField(max_length=60, blank=True, null=True)

    def __str__(self):
        return f"Prod. {self.nombre_producto} ({self.codigo_producto}) x {self.cantidad}"


class ReportDownloadHistory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    report_type = models.CharField(max_length=50)  # e.g., 'despacho', 'otro'
    filter_type = models.CharField(max_length=20, null=True, blank=True)  # e.g., 'diario', 'mensual', 'anual'
    filter_date = models.DateField(null=True, blank=True)
    filter_month = models.CharField(max_length=7, null=True, blank=True)  # YYYY-MM format
    filter_year = models.PositiveIntegerField(null=True, blank=True)
    motorista_id = models.CharField(max_length=100, null=True, blank=True)
    format = models.CharField(max_length=10)  # 'csv' or 'pdf'

    def __str__(self):
        return f"{self.user.username} - {self.report_type} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
