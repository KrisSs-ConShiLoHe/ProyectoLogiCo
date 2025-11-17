from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count
from django.utils import timezone
from .models import Farmacia, Motorista, Moto, AsignarMotorista

# Register your models here.
@admin.register(Farmacia)
class FarmaciaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'telefono', 'email', 'estado_badge', 'motoristas_count', 'horarios')
    list_filter = ('activa', 'nombre')
    search_fields = ('nombre', 'direccion', 'telefono', 'email')
    readonly_fields = ('idfarmacia', 'latitud_display', 'longitud_display')
    
    fieldsets = (
        ('Información General', {
            'fields': ('idfarmacia', 'nombre', 'activa')
        }),
        ('Contacto', {
            'fields': ('telefono', 'email', 'direccion')
        }),
        ('Horarios', {
            'fields': ('horarioapertura', 'horariocierre')
        }),
        ('Ubicación', {
            'fields': ('latitud_display', 'longitud_display', 'latitud', 'longitud'),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ('nombre',)
    list_per_page = 20

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(motoristas=Count('motorista'))

    def motoristas_count(self, obj):
        count = obj.motorista_set.filter(activo=1).count()
        return format_html(
            '<span style="background-color: #e3f2fd; padding: 3px 8px; border-radius: 3px;">{}</span>',
            count
        )
    motoristas_count.short_description = 'Motoristas Activos'

    def estado_badge(self, obj):
        if obj.activa:
            return format_html(
                '<span style="background-color: #4caf50; color: white; padding: 3px 8px; border-radius: 3px;">Activa</span>'
            )
        return format_html(
            '<span style="background-color: #f44336; color: white; padding: 3px 8px; border-radius: 3px;">Inactiva</span>'
        )
    estado_badge.short_description = 'Estado'

    def horarios(self, obj):
        if obj.horarioapertura and obj.horariocierre:
            return f"{obj.horarioapertura} - {obj.horariocierre}"
        return "-"
    horarios.short_description = 'Horarios'

    def latitud_display(self, obj):
        return obj.latitud if obj.latitud else "-"
    latitud_display.short_description = 'Latitud'

    def longitud_display(self, obj):
        return obj.longitud if obj.longitud else "-"
    longitud_display.short_description = 'Longitud'


@admin.register(Motorista)
class MotoristaAdmin(admin.ModelAdmin):
    list_display = ('nombre_completo', 'dni', 'telefono', 'email', 'farmacia_link', 'estado_badge', 'licencia_estado')
    list_filter = ('activo', 'idfarmacia', 'fechacontratacion')
    search_fields = ('nombre', 'apellidopaterno', 'apellidomaterno', 'dni', 'telefono', 'email')
    readonly_fields = ('idmotorista', 'nombre_completo')
    
    fieldsets = (
        ('Identificación', {
            'fields': ('idmotorista', 'dni', 'pasaporte', 'nombre_completo', 'nombre', 'apellidopaterno', 'apellidomaterno')
        }),
        ('Contacto', {
            'fields': ('telefono', 'email', 'direccion')
        }),
        ('Información Personal', {
            'fields': ('fechanacimiento', 'idfarmacia')
        }),
        ('Licencia de Conducir', {
            'fields': ('licenciaconducir', 'licenciaarchivo', 'fechaultimocontrol', 'fechaproximocontrol'),
            'classes': ('collapse',)
        }),
        ('Empleo', {
            'fields': ('fechacontratacion', 'activo'),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ('nombre',)
    list_per_page = 20

    def nombre_completo(self, obj):
        return f"{obj.nombre} {obj.apellidopaterno} {obj.apellidomaterno}".strip()
    nombre_completo.short_description = 'Nombre Completo'

    def estado_badge(self, obj):
        if obj.activo:
            return format_html(
                '<span style="background-color: #4caf50; color: white; padding: 3px 8px; border-radius: 3px;">Activo</span>'
            )
        return format_html(
            '<span style="background-color: #f44336; color: white; padding: 3px 8px; border-radius: 3px;">Inactivo</span>'
        )
    estado_badge.short_description = 'Estado'

    def farmacia_link(self, obj):
        if obj.idfarmacia:
            related = obj.idfarmacia
            url = reverse(f'admin:{related._meta.app_label}_{related._meta.model_name}_change', args=[related.pk])
            return format_html('<a href="{}">{}</a>', url, related.nombre)
        return "-"
    farmacia_link.short_description = 'Farmacia'

    def licencia_estado(self, obj):
        if obj.fechaproximocontrol:
            from datetime import date
            if obj.fechaproximocontrol < date.today():
                return format_html(
                    '<span style="background-color: #f44336; color: white; padding: 3px 8px; border-radius: 3px;">Vencida</span>'
                )
            return format_html(
                '<span style="background-color: #4caf50; color: white; padding: 3px 8px; border-radius: 3px;">Vigente</span>'
            )
        return "-"
    licencia_estado.short_description = 'Licencia'


@admin.register(Moto)
class MotoAdmin(admin.ModelAdmin):
    list_display = ('patente', 'marca_modelo', 'color', 'estado_badge', 'disponibilidad_badge', 'motorista_asignado', 'revision_estado')
    list_filter = ('activa', 'disponible', 'marca', 'anio')
    search_fields = ('patente', 'marca', 'modelo', 'numerochasis', 'propietario')
    readonly_fields = ('idmoto',)
    
    fieldsets = (
        ('Información General', {
            'fields': ('idmoto', 'patente', 'marca', 'modelo', 'color', 'anio')
        }),
        ('Identificadores', {
            'fields': ('numerochasis', 'numeromotor', 'propietario'),
            'classes': ('collapse',)
        }),
        ('Documentación', {
            'fields': ('aniodocumentacion', 'aniopermisocirculacion', 'seguroobligatorio', 'revisiontecnica'),
            'classes': ('collapse',)
        }),
        ('Asignación', {
            'fields': ('idmotorista',)
        }),
        ('Estado', {
            'fields': ('disponible', 'activa')
        }),
    )
    
    ordering = ('patente',)
    list_per_page = 20

    def marca_modelo(self, obj):
        return f"{obj.marca} {obj.modelo}".strip()
    marca_modelo.short_description = 'Marca/Modelo'

    def estado_badge(self, obj):
        if obj.activa:
            return format_html(
                '<span style="background-color: #4caf50; color: white; padding: 3px 8px; border-radius: 3px;">Activa</span>'
            )
        return format_html(
            '<span style="background-color: #f44336; color: white; padding: 3px 8px; border-radius: 3px;">Inactiva</span>'
        )
    estado_badge.short_description = 'Estado'

    def disponibilidad_badge(self, obj):
        if obj.disponible:
            return format_html(
                '<span style="background-color: #2196f3; color: white; padding: 3px 8px; border-radius: 3px;">Disponible</span>'
            )
        return format_html(
            '<span style="background-color: #ff9800; color: white; padding: 3px 8px; border-radius: 3px;">Ocupada</span>'
        )
    disponibilidad_badge.short_description = 'Disponibilidad'

    def motorista_asignado(self, obj):
        if obj.idmotorista:
            related = obj.idmotorista
            url = reverse(f'admin:{related._meta.app_label}_{related._meta.model_name}_change', args=[related.pk])
            return format_html(
                '<a href="{}">{}</a>',
                url,
                f"{related.nombre} {related.apellidopaterno}"
            )
        return "-"
    motorista_asignado.short_description = 'Motorista Asignado'

    def revision_estado(self, obj):
        if obj.revisiontecnica:
            from datetime import date
            if obj.revisiontecnica < date.today():
                return format_html(
                    '<span style="background-color: #f44336; color: white; padding: 3px 8px; border-radius: 3px;">Vencida</span>'
                )
            return format_html(
                '<span style="background-color: #4caf50; color: white; padding: 3px 8px; border-radius: 3px;">Vigente</span>'
            )
        return "-"
    revision_estado.short_description = 'Revisión Técnica'


class AsignarMotoristaInline(admin.TabularInline):
    model = AsignarMotorista
    extra = 0
    fields = ('idmotorista', 'idmoto', 'fechaasignacion', 'activa')
    readonly_fields = ('fechaasignacion',)


@admin.register(AsignarMotorista)
class AsignarMotoristaAdmin(admin.ModelAdmin):
    list_display = ('idasignacion', 'motorista_link', 'moto_link', 'fechaasignacion', 'estado_badge', 'duracion')
    list_filter = ('activa', 'fechaasignacion')
    search_fields = ('idmotorista__nombre', 'idmotorista__apellidopaterno', 'idmoto__patente', 'observaciones')
    readonly_fields = ('idasignacion', 'duracion_display')
    
    fieldsets = (
        ('Asignación', {
            'fields': ('idasignacion', 'idmotorista', 'idmoto')
        }),
        ('Fechas', {
            'fields': ('fechaasignacion', 'fechadesasignacion', 'duracion_display')
        }),
        ('Estado', {
            'fields': ('activa',)
        }),
        ('Observaciones', {
            'fields': ('observaciones',),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ('-fechaasignacion',)
    list_per_page = 20
    date_hierarchy = 'fechaasignacion'

    def motorista_link(self, obj):
        if obj.idmotorista:
            related = obj.idmotorista
            url = reverse(f'admin:{related._meta.app_label}_{related._meta.model_name}_change', args=[related.pk])
            nombre = f"{related.nombre} {related.apellidopaterno}"
            return format_html('<a href="{}">{}</a>', url, nombre)
        return "-"
    motorista_link.short_description = 'Motorista'

    def moto_link(self, obj):
        if obj.idmoto:
            related = obj.idmoto
            url = reverse(f'admin:{related._meta.app_label}_{related._meta.model_name}_change', args=[related.pk])
            return format_html('<a href="{}">{}</a>', url, related.patente)
        return "-"
    moto_link.short_description = 'Moto'

    def estado_badge(self, obj):
        if obj.activa:
            return format_html(
                '<span style="background-color: #4caf50; color: white; padding: 3px 8px; border-radius: 3px;">Activa</span>'
            )
        return format_html(
            '<span style="background-color: #f44336; color: white; padding: 3px 8px; border-radius: 3px;">Inactiva</span>'
        )
    estado_badge.short_description = 'Estado'

    def duracion(self, obj):
        if obj.fechaasignacion and obj.fechadesasignacion:
            duracion = obj.fechadesasignacion - obj.fechaasignacion
            dias = duracion.days
            horas = duracion.seconds // 3600
            return f"{dias}d {horas}h"
        elif obj.fechaasignacion:
            duracion = timezone.now() - obj.fechaasignacion
            dias = duracion.days
            horas = duracion.seconds // 3600
            return f"{dias}d {horas}h (en curso)"
        return "-"
    duracion.short_description = 'Duración'

    def duracion_display(self, obj):
        if obj.fechaasignacion and obj.fechadesasignacion:
            duracion = obj.fechadesasignacion - obj.fechaasignacion
            return str(duracion)
        return "-"
    duracion_display.short_description = 'Duración'