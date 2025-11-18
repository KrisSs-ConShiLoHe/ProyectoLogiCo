from django.db import models, transaction
from django.contrib.auth.models import AbstractUser, Group, Permission


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
    nombre = models.CharField(max_length=255)
    direccion = models.CharField(max_length=255)
    region = models.CharField(max_length=100)
    comuna = models.CharField(max_length=100)
    codigo_externo = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.nombre} - {self.region}, {self.comuna}"

# 3. BASE MOTORISTA
class Motorista(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, limit_choices_to={'rol': 'MOTORISTA'})
    rut = models.CharField(max_length=12, unique=True)
    licencia_vigente = models.BooleanField(default=True)
    activo = models.BooleanField(default=True)


    def __str__(self):
        return f"{self.usuario.get_full_name()} ({self.rut})"

# 4. BASE MOTO
class Moto(models.Model):
    patente = models.CharField(max_length=10, unique=True)
    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=50)
    disponible = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.marca} {self.modelo} - {self.patente}"

# 5. ASIGNACIÓN MOTO A MOTORISTA
class AsignacionMoto(models.Model):
    motorista = models.ForeignKey(Motorista, on_delete=models.CASCADE)
    moto = models.ForeignKey(Moto, on_delete=models.CASCADE)
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    activa = models.BooleanField(default=True)

    class Meta:
        unique_together = (('motorista', 'activa'), ('moto', 'activa'))

    def __str__(self):
        return f"{self.motorista} → {self.moto} ({'Activa' if self.activa else 'Inactiva'})"

    def save(self, *args, **kwargs):
        # Garantizar que exista sólo una asignación activa por motorista y por moto.
        with transaction.atomic():
            # If this assignment is going to be active, deactivate other active assignments
            if self.activa:
                AsignacionMoto.objects.filter(motorista=self.motorista, activa=True).exclude(pk=getattr(self, 'pk', None)).update(activa=False)
                AsignacionMoto.objects.filter(moto=self.moto, activa=True).exclude(pk=getattr(self, 'pk', None)).update(activa=False)
            super().save(*args, **kwargs)

            # Update moto availability after saving
            if self.moto:
                if self.activa:
                    if self.moto.disponible:
                        self.moto.disponible = False
                        self.moto.save()
                else:
                    # If this assignment was deactivated, mark moto as available
                    # Only mark disponible True if there is no other active assignment for this moto
                    other_active = AsignacionMoto.objects.filter(moto=self.moto, activa=True).exclude(pk=self.pk).exists()
                    if not other_active:
                        self.moto.disponible = True
                        self.moto.save()

# 6. ASIGNACIÓN MOTORISTA A FARMACIA
class AsignacionFarmacia(models.Model):
    motorista = models.ForeignKey(Motorista, on_delete=models.CASCADE)
    farmacia = models.ForeignKey(Farmacia, on_delete=models.CASCADE)
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    activa = models.BooleanField(default=True)

    class Meta:
        unique_together = (('motorista', 'activa'), ('farmacia', 'activa'))

    def __str__(self):
        return f"{self.motorista} → {self.farmacia} ({'Activa' if self.activa else 'Inactiva'})"

    def save(self, *args, **kwargs):
        # Garantizar que exista sólo una asignación activa por motorista y por farmacia.
        with transaction.atomic():
            if self.activa:
                AsignacionFarmacia.objects.filter(motorista=self.motorista, activa=True).exclude(pk=getattr(self, 'pk', None)).update(activa=False)
                AsignacionFarmacia.objects.filter(farmacia=self.farmacia, activa=True).exclude(pk=getattr(self, 'pk', None)).update(activa=False)
            super().save(*args, **kwargs)

# 7. DESPACHO - TRAZABILIDAD Y MOVIMIENTO
class Despacho(models.Model):
    MOVIMIENTOS = (
        ('DIRECTO', 'Directo'),
        ('RECETA', 'Receta'),
        ('TRASLADO', 'Traslado'),
        ('REENVIO', 'Reenvío'),
    )
    ESTADOS = (
        ('PENDIENTE', 'Pendiente'),
        ('EN_RUTA', 'En Ruta'),
        ('ENTREGADO', 'Entregado'),
        ('ANULADO', 'Anulado'),
        ('INCIDENCIA', 'Incidencia'),
    )
    id_pedido_externo = models.CharField(max_length=100)
    tipo_movimiento = models.CharField(max_length=20, choices=MOVIMIENTOS)
    farmacia_origen = models.ForeignKey(Farmacia, on_delete=models.CASCADE)
    motorista_asignado = models.ForeignKey(Motorista, on_delete=models.CASCADE)
    fecha_hora_creacion = models.DateTimeField(auto_now_add=True)
    fecha_hora_despacho = models.DateTimeField(null=True, blank=True)
    fecha_hora_entrega = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS)
    requiere_receta = models.BooleanField(default=False)

    # Calculado: tiempo_entrega_minutos
    @property
    def tiempo_entrega_minutos(self):
        if self.fecha_hora_entrega and self.fecha_hora_despacho:
            dif = self.fecha_hora_entrega - self.fecha_hora_despacho
            return int(dif.total_seconds() // 60)
        return None

    def save(self, *args, **kwargs):
        # Asignación automática de requiere_receta si el movimiento corresponde
        if self.tipo_movimiento == 'RECETA':
            self.requiere_receta = True
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.tipo_movimiento} - {self.farmacia_origen} ({self.estado})"
    
    class Meta:
        permissions = [
            ("can_view_dashboard_general", "Puede ver el dashboard general"),
            ("can_view_dashboard_regional", "Puede ver el dashboard regional"),
            ("can_export_csv", "Puede exportar CSV"),
            ("can_export_pdf", "Puede exportar PDF"),
        ]
