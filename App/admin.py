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
)

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

# Farmacia
@admin.register(Farmacia)
class FarmaciaAdmin(admin.ModelAdmin):
    list_display = ("identificador_unico", "nombre", "region", "comuna", "telefono", "correo", "horario_recepcion_inicio", "horario_recepcion_fin", "get_dias_operativos_display", "farmacia_imagen_thumbnail")
    list_filter = ("region", "comuna", "horario_recepcion_inicio", "horario_recepcion_fin")
    search_fields = ("identificador_unico", "nombre", "region", "comuna", "telefono", "correo")
    ordering = ("nombre",)

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

# Motorista
@admin.register(Motorista)
class MotoristaAdmin(admin.ModelAdmin):
    list_display = ("identificador_unico", "usuario", "rut", "licencia_tipo", "licencia_vigente", "disponibilidad", "posesion_moto", "activo", "motorista_imagen_thumbnail")
    list_filter = ("licencia_vigente", "disponibilidad", "posesion_moto", "activo")
    search_fields = ("identificador_unico", "usuario__username", "nombre", "apellido_paterno", "apellido_materno", "rut")
    ordering = ("usuario",)

    def motorista_imagen_thumbnail(self, obj):
        if obj.imagen:
            return f'<img src="{obj.imagen.url}" style="max-width:40px;max-height:40px;" />'
        return ""
    motorista_imagen_thumbnail.short_description = "Foto"
    motorista_imagen_thumbnail.allow_tags = True

# Moto
@admin.register(Moto)
class MotoAdmin(admin.ModelAdmin):
    list_display = ("identificador_unico", "patente", "marca", "modelo", "color", "anio_fabricacion", "estado", "moto_imagen_thumbnail")
    list_filter = ("marca", "modelo", "estado", "anio_fabricacion")
    search_fields = ("identificador_unico", "patente", "marca", "modelo", "numero_chasis", "numero_motor")
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
