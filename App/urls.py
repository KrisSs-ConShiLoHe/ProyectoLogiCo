from django.urls import path
from . import views
from . import views_auth
from . import views_configuracion

urlpatterns = [
    # Home
    path('', views.home, name='home'),
    path('perfil/', views.perfil, name='perfil'),
    path('perfil/editar/', views.editar_perfil, name='editar_perfil'),

    # Autenticación
    path('login/', views_auth.login_view, name='login'),
    path('registro/', views_auth.registro_view, name='registro'),
    path('logout/', views_auth.logout_view, name='logout'),
    path('acceso-denegado/', views_auth.acceso_denegado, name='acceso_denegado'),
    
    # Configuración
    path('configuracion/', views_configuracion.configuracion, name='panel_configuracion'),
    path('configuracion/mis-permisos/', views_configuracion.mis_permisos, name='mis_permisos'),
    path('configuracion/gestionar-usuarios/', views_configuracion.gestionar_usuarios, name='gestionar_usuarios'),
    path('configuracion/asignar-rol/<int:user_id>/', views_configuracion.asignar_rol, name='asignar_rol'),
    path('configuracion/cambiar-contrasena/', views_configuracion.cambiar_contrasena, name='cambiar_contrasena'),
    path('configuracion/preferencias/', views_configuracion.preferencias, name='preferencias'),
    
    # Rutas Farmacia
    path('farmacias/', views.listado_farmacias, name='listado_farmacias'),
    path('farmacias/agregar/', views.agregar_farmacia, name='agregar_farmacia'),
    path('farmacias/<int:pk>/', views.detalle_farmacia, name='detalle_farmacia'),
    path('farmacias/<int:pk>/actualizar/', views.actualizar_farmacia, name='actualizar_farmacia'),
    path('farmacias/<int:pk>/remover/', views.remover_farmacia, name='remover_farmacia'),
    
    # Rutas Motorista
    path('motoristas/', views.listado_motoristas, name='listado_motoristas'),
    path('motoristas/agregar/', views.agregar_motorista, name='agregar_motorista'),
    path('motoristas/<int:pk>/', views.detalle_motorista, name='detalle_motorista'),
    path('motoristas/<int:pk>/actualizar/', views.actualizar_motorista, name='actualizar_motorista'),
    path('motoristas/<int:pk>/remover/', views.remover_motorista, name='remover_motorista'),
    
    # Rutas Moto
    path('motos/', views.listado_motos, name='listado_motos'),
    path('motos/agregar/', views.agregar_moto, name='agregar_moto'),
    path('motos/<int:pk>/', views.detalle_moto, name='detalle_moto'),
    path('motos/<int:pk>/actualizar/', views.actualizar_moto, name='actualizar_moto'),
    path('motos/<int:pk>/remover/', views.remover_moto, name='remover_moto'),
    
    # Rutas Asignaciones
    path('asignaciones/', views.listado_asignaciones, name='listado_asignaciones'),
    path('asignaciones/agregar/', views.agregar_asignacion, name='agregar_asignacion'),
    path('asignaciones/<int:pk>/', views.detalle_asignacion, name='detalle_asignacion'),
    path('asignaciones/<int:pk>/modificar/', views.modificar_asignacion, name='modificar_asignacion'),
    path('asignaciones/<int:pk>/remover/', views.remover_asignacion, name='remover_asignacion'),
]