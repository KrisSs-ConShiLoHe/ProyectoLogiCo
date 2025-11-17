from django.db import models


class Farmacia(models.Model):
    idfarmacia = models.AutoField(db_column='idFarmacia', primary_key=True)
    nombre = models.CharField(max_length=255)
    direccion = models.CharField(max_length=255, blank=True, null=False, default='')
    telefono = models.CharField(max_length=50, blank=True, null=False, default='')
    email = models.CharField(max_length=100, blank=True, null=False, default='')
    horarioapertura = models.TimeField(db_column='horarioApertura', blank=True, null=True)
    horariocierre = models.TimeField(db_column='horarioCierre', blank=True, null=True)
    activa = models.IntegerField(blank=True, null=False, default=1)
    latitud = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    longitud = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)

    class Meta:
        db_table = 'farmacia'

    def __str__(self):
        return self.nombre


class Motorista(models.Model):
    idmotorista = models.AutoField(db_column='idMotorista', primary_key=True)
    dni = models.CharField(unique=True, max_length=12, blank=True, null=False, default='')
    pasaporte = models.CharField(max_length=20, blank=True, null=False, default='')
    nombre = models.CharField(max_length=100, blank=True, null=False, default='')
    apellidopaterno = models.CharField(db_column='apellidoPaterno', max_length=100, blank=True, null=False, default='')
    apellidomaterno = models.CharField(db_column='apellidoMaterno', max_length=100, blank=True, null=False, default='')
    fechanacimiento = models.DateField(db_column='fechaNacimiento', blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=False, default='')
    email = models.CharField(max_length=100, blank=True, null=False, default='')
    direccion = models.CharField(max_length=255, blank=True, null=False, default='')
    licenciaconducir = models.CharField(db_column='licenciaConducir', unique=True, max_length=20, blank=True, null=False, default='')
    licenciaarchivo = models.CharField(db_column='licenciaArchivo', max_length=255, blank=True, null=False, default='')
    fechaultimocontrol = models.DateField(db_column='fechaUltimoControl', blank=True, null=True)
    fechaproximocontrol = models.DateField(db_column='fechaProximoControl', blank=True, null=True)
    fechacontratacion = models.DateField(db_column='fechaContratacion', blank=True, null=True)
    activo = models.IntegerField(blank=True, null=False, default=1)
    idfarmacia = models.ForeignKey(Farmacia, models.DO_NOTHING, db_column='idFarmacia', blank=True, null=True)

    class Meta:
        db_table = 'motorista'

    def __str__(self):
        return f"{self.nombre} {self.apellidopaterno} {self.apellidomaterno}"


class Moto(models.Model):
    idmoto = models.AutoField(db_column='idMoto', primary_key=True)
    patente = models.CharField(unique=True, max_length=10, blank=True, null=False, default='')
    marca = models.CharField(max_length=50, blank=True, null=False, default='')
    modelo = models.CharField(max_length=50, blank=True, null=False, default='')
    color = models.CharField(max_length=30, blank=True, null=False, default='')
    anio = models.IntegerField(blank=True, null=True)
    numerochasis = models.CharField(db_column='numeroChasis', unique=True, max_length=50, blank=True, null=False, default='')
    numeromotor = models.CharField(db_column='numeroMotor', max_length=50, blank=True, null=False, default='')
    aniodocumentacion = models.IntegerField(db_column='anioDocumentacion', blank=True, null=True)
    aniopermisocirculacion = models.IntegerField(db_column='anioPermisoCirculacion', blank=True, null=True)
    seguroobligatorio = models.DateField(db_column='seguroObligatorio', blank=True, null=True)
    revisiontecnica = models.DateField(db_column='revisionTecnica', blank=True, null=True)
    propietario = models.CharField(max_length=9, blank=True, null=False, default='')
    disponible = models.IntegerField(blank=True, null=False, default=1)
    activa = models.IntegerField(blank=True, null=False, default=1)
    idmotorista = models.ForeignKey(Motorista, models.DO_NOTHING, db_column='idMotorista', blank=True, null=True)

    class Meta:
        db_table = 'moto'

    def __str__(self):
        return f"{self.marca} {self.modelo} - {self.patente}"


class AsignarMotorista(models.Model):
    idasignacion = models.AutoField(db_column='idAsignacion', primary_key=True)
    idmotorista = models.ForeignKey(Motorista, models.DO_NOTHING, db_column='idMotorista', blank=True, null=True)
    idmoto = models.ForeignKey(Moto, models.DO_NOTHING, db_column='idMoto', blank=True, null=True)
    fechaasignacion = models.DateTimeField(db_column='fechaAsignacion', blank=True, null=True)
    fechadesasignacion = models.DateTimeField(db_column='fechaDesasignacion', blank=True, null=True)
    activa = models.IntegerField(blank=True, null=False, default=1)
    observaciones = models.TextField(blank=True, null=False, default='')

    class Meta:
        db_table = 'asignar_motorista'

    def __str__(self):
        return f"Asignación {self.idasignacion} - Motorista {self.idmotorista}"