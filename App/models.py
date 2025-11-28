from django.db import models, transaction
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db.models import UniqueConstraint, Q
from django.utils import timezone
from django.conf import settings


# # 1. USER EXTENDIDO CON ROL (RBAC)
# class User(AbstractUser):
#     groups = models.ManyToManyField(
#         Group,
#         related_name='custom_user_groups',
#         blank=True
#     )
#     user_permissions = models.ManyToManyField(
#         Permission,
#         related_name='custom_user_permissions',
#         blank=True
#     )

#     ROLES = (
#         ('ADMINISTRADOR', 'Administrador'),
#         ('GERENTE', 'Gerente'),
#         ('SUPERVISOR', 'Supervisor'),
#         ('OPERADOR', 'Operador'),
#         ('MOTORISTA', 'Motorista'),
#     )
#     rol = models.CharField(max_length=30, choices=ROLES)

#     def __str__(self):
#         return f"{self.username} ({self.rol})"

# 1. USER EXTENDIDO CON ROL (RBAC)
class User(AbstractUser):
    # ELIMINA la redefinición de groups y user_permissions si no tienes conflicto.

    ROLES = (
        ('ADMINISTRADOR', 'Administrador'),
        ('GERENTE', 'Gerente'),
        ('SUPERVISOR', 'Supervisor'),
        ('OPERADOR', 'Operador'),
        ('MOTORISTA', 'Motorista'),
    )
    rol = models.CharField(max_length=15, choices=ROLES, default='MOTORISTA') # Max length ajustado y default
    
    # 💡 RECOMENDACIÓN: Haz el rol obligatorio, ya que todo usuario debe tener un rol.
    # rol = models.CharField(max_length=15, choices=ROLES, default='MOTORISTA', blank=False, null=False)

    def __str__(self):
        return f"{self.username} ({self.rol})"

# 2. BASE FARMACIA
class Farmacia(models.Model):
    identificador_unico = models.AutoField(primary_key=True)  # Identificador único
    nombre = models.CharField(max_length=255, default="Cruz Verde")
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
    ('REGIÓN DEL BIOBÍO', 'Biobío'),
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
    localidad = models.CharField(max_length=200)
    provincia = models.CharField(max_length=200)
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
    latitud = models.DecimalField(max_digits=9, decimal_places=6, help_text="Coordenada de latitud | ej: 40.4168")
    longitud = models.DecimalField(max_digits=9, decimal_places=6, help_text="Coordenada de longitud | ej: -3.7038")
    fecha_hora_creacion = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        # Limpieza de dias_operativos
        if self.dias_operativos and isinstance(self.dias_operativos, str):
            self.dias_operativos = ','.join([d.strip() for d in self.dias_operativos.split(',')])
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre} ({self.identificador_unico}) - {self.region}, {self.comuna}"

    imagen = models.ImageField(upload_to='farmacias/', blank=True, null=True)    # Campo para imagen

    def __str__(self):
        return f"{self.nombre} ({self.identificador_unico}) - {self.region}, {self.comuna}"

# 3. BASE MOTORISTA
class Motorista(models.Model):
    identificador_unico = models.AutoField(primary_key=True) 
    
    # 1. CAMBIO ON_DELETE: Si el User se va, el perfil Motorista se queda para auditoría.
    # 2. ELIMINACIÓN DE limit_choices_to: La validación va en el formulario.
    usuario = models.OneToOneField(
        'User',
        on_delete=models.CASCADE, related_name='motorista', null=True, blank=True
    )

    pasaporte = models.CharField(max_length=50, unique=True, blank=True, null=True, help_text="Número de Pasaporte (Opcional)")
    nombre = models.CharField(max_length=100)
    apellido_paterno = models.CharField(max_length=100)
    apellido_materno = models.CharField(max_length=100)
    rut = models.CharField(max_length=16, unique=True)
    domicilio = models.CharField(max_length=150, blank=True, null=True)
    correo = models.EmailField(blank=True, null=True)
    telefono = models.CharField(max_length=30, blank=True, null=True)
    emergencia_nombre = models.CharField(max_length=100, blank=True, null=True)
    emergencia_telefono = models.CharField(max_length=30, blank=True, null=True)
    
    # --- Datos de Licencia ---
    licencia_vigente = models.BooleanField(default=False)
    fecha_ultimo_control_licencia = models.DateField(
        help_text="Fecha del último control/emisión de la licencia de conducir",
        null=True, blank=True # 💡 Se permite nulo en caso de nueva contratación
    )
    fecha_proximo_control_licencia = models.DateField(
        help_text="Fecha de vencimiento de la licencia de conducir",
        null=True, blank=True # 💡 Se permite nulo
    )

    # --- Estado y Disponibilidad ---
    ESTADOS_DISPONIBILIDAD = (
        ('DISPONIBLE', 'Disponible'),
        ('ASIGNADO', 'Asignado'),
        ('EN_DESPACHO', 'En Despacho'),
        ('EN_DESCANSO', 'En Descanso'),
        ('CON_LICENCIA', 'Con Licencia'),
        ('INACTIVO', 'Inactivo'),
    )
    disponibilidad = models.CharField(max_length=20, choices=ESTADOS_DISPONIBILIDAD, default='DISPONIBLE')

    # 💡 Posesión de Moto: Es el estado actual de su tenencia.
    TIENE_MOTO = (
        ('SIN_MOTO', 'Sin Moto'),
        ('CON_MOTO', 'Con Moto'),
    )
    posesion_moto = models.CharField(max_length=20, choices=TIENE_MOTO, default='SIN_MOTO')

    
    licencia_tipo = models.CharField(max_length=40, blank=True, null=True, default='C')
    imagen = models.ImageField(upload_to='motoristas/', blank=True, null=True) # Foto motorista
    imagen_licencia = models.ImageField(upload_to='licencias/', blank=True, null=True)
    activo = models.BooleanField(default=True)

    # --- Documentación del Vehículo / Seguro Obligatorio ---
    # 💡 Eliminado 'tiene_seguro_obligatorio' ya que los campos de póliza lo implican.

    numero_poliza_seguro = models.CharField(max_length=100, blank=True, null=True)

    fecha_vencimiento_seguro = models.DateField(
        blank=True, null=True,
        help_text="Fecha de vencimiento del seguro obligatorio"
    )
    documento_seguro_pdf = models.FileField(upload_to='seguros_motorista/', blank=True, null=True)
    
    # def save(self, *args, **kwargs):
    # # """Calcula el estado de la licencia antes de guardar el registro."""
    #     fecha_proximo = self.fecha_proximo_control_licencia
    #     hoy = timezone.now().date()
        
    #     # Si existe una fecha y es hoy o en el futuro, es True
    #     if fecha_proximo and fecha_proximo >= hoy:
    #         self.licencia_vigente = True
    #     else:
    #         self.licencia_vigente = False
            
    #     # Llama al método save original para que se guarde en la BD
    #         super().save(*args, **kwargs)

    @property
    def nombre_completo(self):
        """Retorna el nombre completo del motorista"""
        if self.usuario:
            first = self.usuario.first_name or ''
            last = self.usuario.last_name or ''
            full = f"{first} {last}".strip()
            return full or self.usuario.username
        return f"Motorista {self.identificador_unico}"
    
    def __str__(self):
        return f"{self.nombre_completo} - {self.rut}"

    def save(self, *args, **kwargs):
        """Calcula el estado de la licencia ANTES de guardar el registro."""
        fecha_proximo = self.fecha_proximo_control_licencia
        hoy = timezone.now().date()
        
        # La lógica de cálculo DEBE MANEJAR el caso donde fecha_proximo es None
        # Tu código actual ya lo maneja bien con 'if fecha_proximo and ...'
        if fecha_proximo and fecha_proximo >= hoy:
            self.licencia_vigente = True
        else:
            # Esto incluye cuando fecha_proximo es None
            self.licencia_vigente = False
            
        # El super().save() debe estar al final.
        super().save(*args, **kwargs)

# 4. BASE MOTO
class Moto(models.Model):
    identificador_unico = models.AutoField(primary_key=True)
    patente = models.CharField(max_length=16, unique=True)              # Matrícula/placa
    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=50)
    color = models.CharField(max_length=40, blank=True, null=True)
    anio_fabricacion = models.PositiveIntegerField(blank=True, null=True)
    numero_chasis = models.CharField(max_length=60, blank=True, null=True)
    numero_motor = models.CharField(max_length=60, blank=True, null=True)

    TIPO_DUEÑO = (
    ('EMPRESA', 'Empresa'),
    ('MOTORISTA', 'Motorista'),
)

    duenio = models.CharField(max_length=20, choices=TIPO_DUEÑO, default='EMPRESA')
    motorista_asignado = models.ForeignKey(Motorista, on_delete=models.CASCADE, null=True, blank=True)

    ESTADOS_VEHICULO = (
    ('OPERATIVO', 'Operativo'),
    ('OCUPADO', 'Ocupado'),
    ('EN_TALLER', 'En Taller'),
    ('FUERA_DE_SERVICIO', 'Fuera de Servicio'),
    ('EN_MANTENIMIENTO', 'En Mantenimiento'),
)

    estado = models.CharField(max_length=20, choices=ESTADOS_VEHICULO, default='OPERATIVO')
    imagen = models.ImageField(upload_to='motos/', blank=True, null=True)

    # Datos de Rendimiento
    consumo_combustible = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text='L/100km')
    capacidad_carga = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, help_text='En Kg')
    velocidad_promedio = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text='Km/h')
    frenadas_bruscas = models.PositiveIntegerField(default=0, help_text='Por día')
    aceleraciones_rapidas = models.PositiveIntegerField(default=0, help_text='Por día')
    tiempo_inactividad_horas = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text='Horas')

    def __str__(self):
        return f"{self.patente} - {self.marca} {self.modelo}"
    
    @property
    def es_vigente(self):
        """
        Calcula la vigencia general de la moto (Permiso de Circulación y Revisión Técnica)
        """
        try:
            documentos = self.documentacionmoto # Obtener el objeto OneToOne
            hoy = timezone.now().date()
            
            # Revisión Técnica Vencida O Seguro SOAP Vencido (necesario para el PC)
            if (documentos.revision_tecnica_vencimiento and documentos.revision_tecnica_vencimiento < hoy) or \
               (documentos.seguro_soap_vencimiento and documentos.seguro_soap_vencimiento < hoy):
                return False
                
            # Si ambas fechas están en el futuro, es vigente.
            return True
        
        except DocumentacionMoto.DoesNotExist:
            return False # Si no tiene documentación registrada, no es vigente.

    # Puedes agregar properties individuales para el detalle:
    
    @property
    def tiene_permiso_circulacion_valido(self):
        # Asume que un permiso es válido si el SOAP está vigente.
        try:
            documentos = self.documentacionmoto
            hoy = timezone.now().date()
            return documentos.seguro_soap_vencimiento and documentos.seguro_soap_vencimiento >= hoy
        except DocumentacionMoto.DoesNotExist:
            return False
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

class DocumentacionMoto(models.Model):
    moto = models.OneToOneField(
        'Moto', 
        on_delete=models.CASCADE, primary_key=True, related_name='documentacion')
    revision_tecnica_vencimiento = models.DateField(blank=True, null=True)
    seguro_soap_vencimiento = models.DateField(blank=True, null=True)
    revision_tecnica_archivo = models.ImageField(upload_to='revisiones_tecnicas/', blank=True, null=True)
    seguro_soap_archivo = models.ImageField(upload_to='seguros_soap/', blank=True, null=True)
    pago_multas_comprobante = models.ImageField(upload_to='comprobantes_pagos_multas/', blank=True, null=True)

    def __str__(self):
        return f"Documen. {self.revision_tecnica_vencimiento} ({self.seguro_soap_vencimiento}) de {self.moto}"


class PermisoCirculacion(models.Model):
    moto = models.ForeignKey(Moto, on_delete=models.CASCADE, related_name='permisos')
    anio_permiso = models.PositiveIntegerField(blank=True, null=True)
    valor_tasacion_SII = models.DecimalField(max_digits=9, decimal_places=2, blank=True, null=True)
    codigo_SII = models.CharField(max_length=30, blank=True, null=True)

    COMBUSTIBLES = (
            ('BENCINA', 'Bencina'),
            ('DIESEL', 'Diésel'),
            ('GNC', 'Gas Natural Comprimido (GNC)'),
            ('GLP', 'Gas Licuado de Petróleo (GLP)'),
            ('ELECTRICO', 'Eléctrico'),
            ('HIBRIDO_BENCINA', 'Híbrido (Bencina + Eléctrico)'),
    )
    
    OCTANAJE = (
        ('93_OCTANOS', '93 octanos'),
        ('95_OCTANOS', '95 octanos'),
        ('97_OCTANOS', '97 octanos'),
    )

    tipo_combustible = models.CharField(max_length=50, choices=COMBUSTIBLES, help_text="Tipo de combustible o energía de la moto")
    tipo_octanaje = models.CharField(max_length=30, choices=OCTANAJE, help_text="Tres octanajes estándar en la mayoría de las estaciones de servicio (Copec, Shell, Petrobras, etc)")
    cilindrada = models.PositiveIntegerField(blank=True, null=True)
    valor_neto_pago = models.DecimalField(max_digits=7, decimal_places=2, blank=True, null=True)
    valor_multa_pagado = models.DecimalField(max_digits=7, decimal_places=2, blank=True, null=True)
    valor_pagado_total = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    fecha_pago = models.DateField(blank=True, null=True)
    forma_pago = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"Perm. {self.anio_permiso} ({self.get_tipo_combustible_display()}) de {self.moto.patente}"


# Historial de mantenimientos (uno a muchos)
class MantenimientoMoto(models.Model):
    moto = models.ForeignKey(Moto, on_delete=models.CASCADE, related_name='mantenimientos')
    fecha_mantenimiento = models.DateField()
    descripcion = models.TextField()

    SERVICIOS = (
        ('PREVENTIVO', 'Mantenimiento Preventivo'),
        ('CORRECTIVO', 'Mantenimiento Correctivo'),
        ('PREDICTIVO', 'Mantenimiento Predictivo'),
    )
    
    SERVICIOS_PREVENTIVOS = (
        ('MENOR', 'Servicio Menor (revisiones básicas y frecuentes)'),
        ('MAYOR', 'Servicio Mayor (revisiones profundas y menos frecuentes)'),
    )

    tipo_servicio = models.CharField(max_length=60, choices=SERVICIOS, help_text="Tipo de mantenimiento realizado")
    servicio_preventivo = models.CharField(max_length=10, choices=SERVICIOS_PREVENTIVOS, help_text="Requerido si el tipo de servicio es Preventivo")
    kilometraje = models.PositiveIntegerField(blank=True, null=True)
    proximo_mantenimiento = models.DateField(blank=True, null=True)

    def __str__(self):
        servicio = f" - {self.get_servicio_preventivo_display()}" if self.servicio_preventivo else ""
        return f"Manten. {self.get_tipo_servicio_display()}{servicio} ({self.fecha_mantenimiento}) de {self.moto.patente}"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.tipo_servicio == 'PREVENTIVO' and not self.servicio_preventivo:
            raise ValidationError({
                'servicio_preventivo': 'Debe seleccionar el tipo de servicio preventivo (Menor o Mayor)'
            })
        # Limpiar subtipo si no es preventivo
        if self.tipo_servicio != 'PREVENTIVO':
            self.servicio_preventivo = None


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
from django.db import models, transaction
from django.db.models import Q
from django.utils import timezone

class AsignacionFarmacia(models.Model):
    motorista = models.ForeignKey(Motorista, on_delete=models.CASCADE, related_name='asignaciones_farmacia')
    farmacia = models.ForeignKey(Farmacia, on_delete=models.CASCADE, related_name='asignaciones')
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    fecha_desasignacion = models.DateTimeField(null=True, blank=True)
    activa = models.BooleanField(default=True)
    observaciones = models.TextField(blank=True, help_text="Motivo de la asignación o cambio")

    class Meta:
        constraints = [
            # Un motorista solo puede tener UNA asignación activa a farmacia
            models.UniqueConstraint(
                fields=['motorista'], 
                condition=Q(activa=True), 
                name='motorista_una_asignacion_farmacia_activa'
            ),
            # NOTA: NO hay constraint en farmacia porque una farmacia puede tener muchos motoristas
        ]
        ordering = ['-fecha_asignacion']
        verbose_name = 'Asignación a Farmacia'
        verbose_name_plural = 'Asignaciones a Farmacias'

    def __str__(self):
        estado = 'Activa' if self.activa else 'Inactiva'
        return f"{self.motorista.nombre_completo} → {self.farmacia.nombre} ({estado})"

    def clean(self):
        from django.core.exceptions import ValidationError
        
        # Validar que el motorista tenga moto asignada
        if self.motorista.posesion_moto != 'CON_MOTO':
            raise ValidationError({
                'motorista': f'{self.motorista.nombre_completo} no tiene moto asignada. Debe asignarle una moto primero.'
            })

    def save(self, *args, **kwargs):
        # Validar antes de guardar
        self.clean()
        
        with transaction.atomic():
            # Guardar primero para tener pk
            super().save(*args, **kwargs)
            
            if self.activa:
                # Desactivar SOLO otras asignaciones activas del mismo motorista
                # (Un motorista no puede estar en múltiples farmacias)
                asignaciones_previas = AsignacionFarmacia.objects.filter(
                    motorista=self.motorista, 
                    activa=True
                ).exclude(pk=self.pk)
                
                if asignaciones_previas.exists():
                    asignaciones_previas.update(
                        activa=False,
                        fecha_desasignacion=timezone.now()
                    )
                
                # Actualizar disponibilidad del motorista
                self.motorista.disponibilidad = 'ASIGNADO'
                self.motorista.save(update_fields=['disponibilidad'])
                
            else:  # Desactivación
                # Registrar fecha de desasignación
                if not self.fecha_desasignacion:
                    self.fecha_desasignacion = timezone.now()
                    AsignacionFarmacia.objects.filter(pk=self.pk).update(
                        fecha_desasignacion=self.fecha_desasignacion
                    )
                
                # Liberar motorista SOLO si no tiene otra asignación activa
                tiene_otra_asignacion = AsignacionFarmacia.objects.filter(
                    motorista=self.motorista, 
                    activa=True
                ).exclude(pk=self.pk).exists()
                
                if not tiene_otra_asignacion:
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
    identificador_unico = models.AutoField(primary_key=True)
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
    paciente_edad = models.PositiveIntegerField(blank=True, null=True)
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
    TIPO_REPORTE = (
        ('GENERAL', 'General'),
        ('DIARIO', 'Diario'),
        ('MENSUAL', 'Mensual'),
        ('ANUAL', 'Anual'),
    )
    
    FORMATO = (
        ('CSV', 'CSV'),
        ('PDF', 'PDF'),
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='reportes_descargados'
    )
    fecha_descarga = models.DateTimeField(auto_now_add=True)
    tipo_reporte = models.CharField(max_length=20, choices=TIPO_REPORTE)
    formato = models.CharField(max_length=10, choices=FORMATO)
    
    # Filtros aplicados
    fecha_desde = models.DateField(null=True, blank=True)
    fecha_hasta = models.DateField(null=True, blank=True)
    motorista = models.ForeignKey(
        'Motorista', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='reportes_generados'
    )
    
    # Metadatos
    cantidad_registros = models.PositiveIntegerField(default=0)
    nombre_archivo = models.CharField(max_length=255)
    
    class Meta:
        ordering = ['-fecha_descarga']
        verbose_name = 'Historial de Reporte'
        verbose_name_plural = 'Historial de Reportes'
    
    def __str__(self):
        return f"{self.user.username} - {self.get_tipo_reporte_display()} {self.get_formato_display()} - {self.fecha_descarga.strftime('%Y-%m-%d %H:%M')}"