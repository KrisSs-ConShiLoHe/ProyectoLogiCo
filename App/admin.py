from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User,
    Farmacia,
    Motorista,
    Moto,
    AsignacionMoto,
    AsignacionFarmacia,
    Despacho,
    MantenimientoMoto,
    ProductoPedido,
    DocumentacionMoto,
    PermisoCirculacion,
    ReportDownloadHistory
)
from import_export import resources
from import_export.admin import ImportExportModelAdmin

# User personalizado
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "email", "rol", "is_active", "is_superuser")
    list_filter = ("rol", "is_active", "is_superuser")
    search_fields = ("username", "email", "rol")
    ordering = ("username",)
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Información personal", {"fields": ("first_name", "last_name", "email")}),
        ("Permisos", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Fechas importantes", {"fields": ("last_login", "date_joined")}),
        ("Rol personalizado", {"fields": ("rol",)}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "first_name", "last_name", "email", "password1", "password2", "rol", "is_active", "is_staff", "is_superuser", "groups", "user_permissions"),
        }),
    )
    filter_horizontal = ("groups", "user_permissions")

class FarmaciaResource(resources.ModelResource):
    class Meta:
        model = Farmacia
        import_id_fields = []  # evita duplicados si ya existe
        skip_unchanged = True
        report_skipped = True

# Farmacia
@admin.register(Farmacia)
class FarmaciaAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_class = FarmaciaResource

    list_display = ("identificador_unico", "nombre", "direccion", "provincia", "localidad", "region", "comuna", "telefono", "correo",
                    "horario_recepcion_inicio", "horario_recepcion_fin", "fecha_hora_creacion",
                    "get_dias_operativos_display", "farmacia_imagen_thumbnail")

    list_filter = ("region", "direccion", "provincia", "localidad", "comuna", "horario_recepcion_inicio", "horario_recepcion_fin")
    search_fields = ("nombre", "region", "comuna", "telefono", "correo")
    ordering = ("nombre", "-fecha_hora_creacion",)

    def get_dias_operativos_display(self, obj):
        if obj.dias_operativos:
            return ', '.join(obj.get_dias_operativos_list())
        return "-"
    get_dias_operativos_display.short_description = "Días Operativos"

    def farmacia_imagen_thumbnail(self, obj):
        if obj.imagen:
            return f'<img src="{obj.imagen.url}" style="max-width:40px;max-height:40px;" />'
        return ""
    farmacia_imagen_thumbnail.short_description = "Imagen"
    farmacia_imagen_thumbnail.allow_tags = True

class MotoristaResource(resources.ModelResource):
    class Meta:
        model = Motorista
        import_id_fields = []  # evita duplicados si ya existe
        skip_unchanged = True
        report_skipped = True

# Motorista
@admin.register(Motorista)
class MotoristaAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_class=MotoristaResource

    list_display = ("identificador_unico", "usuario", "rut", "licencia_tipo", "licencia_vigente", "disponibilidad", "posesion_moto", "activo", "motorista_imagen_thumbnail")
    list_filter = ("licencia_vigente", "disponibilidad", "posesion_moto", "activo")
    search_fields = ("usuario__username", "nombre", "apellido_paterno", "apellido_materno", "rut")
    ordering = ("usuario",)

    def motorista_imagen_thumbnail(self, obj):
        if obj.imagen:
            return f'<img src="{obj.imagen.url}" style="max-width:40px;max-height:40px;" />'
        return ""
    motorista_imagen_thumbnail.short_description = "Foto"
    motorista_imagen_thumbnail.allow_tags = True

class MotoResource(resources.ModelResource):
    class Meta:
        model = Moto
        import_id_fields = []
        skip_unchanged = True
        report_skipped = True

# Moto
@admin.register(Moto)
class MotoAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_class=MotoResource

    list_display = ("identificador_unico", "patente", "marca", "modelo", "color", "anio_fabricacion", "estado", "moto_imagen_thumbnail")
    list_filter = ("marca", "modelo", "estado", "anio_fabricacion")
    search_fields = ("patente", "marca", "modelo", "numero_chasis", "numero_motor")
    ordering = ("patente",)

    def moto_imagen_thumbnail(self, obj):
        if obj.imagen:
            return f'<img src="{obj.imagen.url}" style="max-width:40px;max-height:40px;" />'
        return ""
    moto_imagen_thumbnail.short_description = "Imagen"
    moto_imagen_thumbnail.allow_tags = True

# Historial de mantenimientos (puedes agregarlo en línea para Moto si quieres)
@admin.register(MantenimientoMoto)
class MantenimientoMotoAdmin(admin.ModelAdmin):
    list_display = ("moto", "fecha_mantenimiento", "tipo_servicio", "descripcion", "kilometraje", "proximo_mantenimiento")
    list_filter = ("tipo_servicio", "fecha_mantenimiento")
    search_fields = ("moto__patente", "moto__identificador_unico", "tipo_servicio", "descripcion")
    ordering = ("-fecha_mantenimiento",)

@admin.register(DocumentacionMoto)
class DocumentacionMotoAdmin(admin.ModelAdmin):
    list_display = ("moto", "revision_tecnica_vencimiento", "seguro_soap_vencimiento", "revision_tecnica_archivo", "seguro_soap_archivo", "pago_multas_comprobante")
    list_filter = ("revision_tecnica_vencimiento", "seguro_soap_vencimiento")
    search_fields = ("moto__patente", "moto__identificador_unico", "revision_tecnica_vencimiento", "seguro_soap_vencimiento")
    ordering = ("-revision_tecnica_vencimiento",)

@admin.register(PermisoCirculacion)
class PermisoCirculacionAdmin(admin.ModelAdmin):
    list_display = ("moto", "anio_permiso", "valor_tasacion_SII", "codigo_SII", "tipo_combustible", "cilindrada", "valor_neto_pago", "valor_multa_pagado", "valor_pagado_total", "fecha_pago", "forma_pago")
    list_filter = ("anio_permiso", "codigo_SII")
    search_fields = ("moto__patente", "moto__identificador_unico", "anio_permiso", "codigo_SII")
    ordering = ("-fecha_pago",)

# Asignación Moto
@admin.register(AsignacionMoto)
class AsignacionMotoAdmin(admin.ModelAdmin):
    list_display = ("motorista", "moto", "fecha_asignacion", "fecha_desasignacion", "activa")
    list_filter = ("activa", "fecha_asignacion", "fecha_desasignacion", "motorista", "moto")
    search_fields = ("motorista__rut", "motorista__identificador_unico", "moto__patente", "moto__identificador_unico")
    ordering = ("-fecha_asignacion", "-fecha_desasignacion",)

# Asignación Farmacia
@admin.register(AsignacionFarmacia)
class AsignacionFarmaciaAdmin(admin.ModelAdmin):
    list_display = ("motorista", "farmacia", "fecha_asignacion", "fecha_desasignacion", "activa")
    list_filter = ("activa", "fecha_asignacion", "fecha_desasignacion", "farmacia", "motorista")
    search_fields = ("motorista__rut", "farmacia__nombre", "farmacia__identificador_unico", "motorista__identificador_unico")
    ordering = ("-fecha_asignacion", "-fecha_desasignacion",)

# ProductoPedido para inspección manual de productos por despacho
@admin.register(ProductoPedido)
class ProductoPedidoAdmin(admin.ModelAdmin):
    list_display = ("despacho", "codigo_producto", "nombre_producto", "cantidad", "numero_lote", "numero_serie")
    list_filter = ("despacho", )
    search_fields = ("codigo_producto", "nombre_producto", "despacho__identificador_unico")
    ordering = ("despacho", )

# Despacho
@admin.register(Despacho)
class DespachoAdmin(admin.ModelAdmin):
    list_display = (
        "identificador_unico", "tipo_movimiento", "farmacia_origen", "motorista_asignado",
        "fecha_hora_creacion", "estado", "despacho_imagen_thumbnail"
    )
    list_filter = ("tipo_movimiento", "estado", "farmacia_origen")
    search_fields = ("identificador_unico", "farmacia_origen__nombre", "motorista_asignado__rut")
    ordering = ("-fecha_hora_creacion",)

    def despacho_imagen_thumbnail(self, obj):
        if obj.imagen:
            return f'<img src="{obj.imagen.url}" style="max-width:40px;max-height:40px;" />'
        return ""
    despacho_imagen_thumbnail.short_description = "Imagen"
    despacho_imagen_thumbnail.allow_tags = True

@admin.register(ReportDownloadHistory)
class ReportDownloadHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'tipo_reporte', 'formato', 'fecha_descarga', 'cantidad_registros']
    list_filter = ['tipo_reporte', 'formato', 'fecha_descarga']
    search_fields = ['user__username', 'user__email', 'nombre_archivo']
    readonly_fields = ['fecha_descarga']
    date_hierarchy = 'fecha_descarga'