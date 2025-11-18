from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User,
    Farmacia,
    Motorista,
    Moto,
    AsignacionMoto,
    AsignacionFarmacia,
    Despacho
)

# Modelo User extendido con campo rol
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "email", "rol", "is_active", "is_superuser")
    list_filter = ("rol", "is_active", "is_superuser")
    search_fields = ("username", "email", "rol")
    ordering = ("username",)

    fieldsets = (
    (None, {"fields": ("username", "password")}),
    ("Información personal", {"fields": ("first_name", "last_name", "email")}),
    ("Permisos", {"fields": ("is_active", "is_staff", "is_superuser", "groups")}),
    ("Fechas importantes", {"fields": ("last_login", "date_joined")}),
    ("Rol personalizado", {"fields": ("rol",)}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "first_name", "last_name", "email", "password1", "password2", "is_active", "is_staff", "is_superuser", "last_login", "date_joined", "groups"),
        }),
    )

    filter_horizontal = ("groups", "user_permissions")


@admin.register(Farmacia)
class FarmaciaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "region", "comuna", "codigo_externo")
    list_filter = ("region", "comuna")
    search_fields = ("nombre", "codigo_externo", "region", "comuna")
    ordering = ("nombre",)

@admin.register(Motorista)
class MotoristaAdmin(admin.ModelAdmin):
    list_display = ("usuario", "rut", "licencia_vigente", "activo")
    list_filter = ("licencia_vigente", "activo")
    search_fields = ("usuario__username", "rut")
    ordering = ("usuario",)

@admin.register(Moto)
class MotoAdmin(admin.ModelAdmin):
    list_display = ("patente", "marca", "modelo", "disponible")
    list_filter = ("marca", "modelo", "disponible")
    search_fields = ("patente", "marca", "modelo")
    ordering = ("patente",)

@admin.register(AsignacionMoto)
class AsignacionMotoAdmin(admin.ModelAdmin):
    list_display = ("motorista", "moto", "fecha_asignacion", "activa")
    list_filter = ("activa", "fecha_asignacion")
    search_fields = ("motorista__rut", "moto__patente")
    ordering = ("-fecha_asignacion",)

@admin.register(AsignacionFarmacia)
class AsignacionFarmaciaAdmin(admin.ModelAdmin):
    list_display = ("motorista", "farmacia", "fecha_asignacion", "activa")
    list_filter = ("activa", "farmacia")
    search_fields = ("motorista__rut", "farmacia__nombre")
    ordering = ("-fecha_asignacion",)

@admin.register(Despacho)
class DespachoAdmin(admin.ModelAdmin):
    list_display = (
        "id_pedido_externo",
        "tipo_movimiento",
        "farmacia_origen",
        "motorista_asignado",
        "fecha_hora_creacion",
        "estado",
        "requiere_receta",
        "tiempo_entrega_minutos"
    )
    list_filter = ("tipo_movimiento", "estado", "requiere_receta", "farmacia_origen")
    search_fields = ("id_pedido_externo", "farmacia_origen__nombre", "motorista_asignado__rut")
    ordering = ("-fecha_hora_creacion",)
    readonly_fields = ("tiempo_entrega_minutos",)

    def tiempo_entrega_minutos(self, obj):
        return obj.tiempo_entrega_minutos

