from django.urls import path, include
from . import views
from .views import auth, farmacia, motorista, moto, asignacion_moto, asignacion_farmacia, despacho, dashboard

urlpatterns = [
    # ============================================
    # HOME Y AUTENTICACIÓN
    # ============================================
    path('', auth.home, name='home'),
    path('login/', auth.LoginView.as_view(), name='login'),
    path('logout/', auth.LogoutView.as_view(), name='logout'),
    path('cambiar_contrasena/', auth.PasswordChangeView.as_view(), name='cambiar_contrasena'),
    path('resetear_contrasena/', auth.PasswordResetView.as_view(), name='resetear_contrasena'),
    path('resetear_contrasena/confirmar/', auth.PasswordResetConfirmView.as_view(), name='resetear_contrasena_confirmar'),
    path('expiracion/', auth.SessionInfoView.as_view(), name='session_info'),

    # ============================================
    # FARMACIAS
    # ============================================
    path('farmacias/', farmacia.listar_farmacias, name='farmacia_listar'),
    path('farmacias/crear/', farmacia.crear_farmacia, name='farmacia_crear'),
    path('farmacias/<int:pk>/editar/', farmacia.editar_farmacia, name='farmacia_editar'),
    path('farmacias/<int:pk>/eliminar/', farmacia.eliminar_farmacia, name='farmacia_eliminar'),

    # ============================================
    # MOTORISTAS
    # ============================================
    path('motoristas/', motorista.listar_motoristas, name='motorista_listar'),
    path('motoristas/crear/', motorista.crear_motorista, name='motorista_crear'),
    path('motoristas/<int:pk>/editar/', motorista.editar_motorista, name='motorista_editar'),
    path('motoristas/<int:pk>/eliminar/', motorista.eliminar_motorista, name='motorista_eliminar'),

    # ============================================
    # MOTOS
    # ============================================
    path('motos/', moto.listar_motos, name='moto_listar'),
    path('motos/crear/', moto.crear_moto, name='moto_crear'),
    path('motos/<int:pk>/editar/', moto.editar_moto, name='moto_editar'),
    path('motos/<int:pk>/eliminar/', moto.eliminar_moto, name='moto_eliminar'),

    # ============================================
    # ASIGNACIÓN MOTO
    # ============================================
    path('asignaciones_moto/', asignacion_moto.listar_asignaciones_moto, name='asignacion_moto_listar'),
    path('asignaciones_moto/crear/', asignacion_moto.crear_asignacion_moto, name='asignacion_moto_crear'),
    path('asignaciones_moto/<int:pk>/reemplazar/', asignacion_moto.reemplazar_asignacion_moto, name='asignacion_moto_reemplazar'),

    # ============================================
    # ASIGNACIÓN FARMACIA
    # ============================================
    path('asignaciones_farmacia/', asignacion_farmacia.listar_asignaciones_farmacia, name='asignacion_farmacia_listar'),
    path('asignaciones_farmacia/crear/', asignacion_farmacia.crear_asignacion_farmacia, name='asignacion_farmacia_crear'),
    path('asignaciones_farmacia/<int:pk>/reemplazar/', asignacion_farmacia.reemplazar_asignacion_farmacia, name='asignacion_farmacia_reemplazar'),

    # ============================================
    # DESPACHOS
    # ============================================
    path('despachos/', despacho.listar_despachos, name='despacho_listar'),
    path('despachos/crear/', despacho.crear_despacho, name='despacho_crear'),
    path('despachos/<int:pk>/editar/', despacho.editar_despacho, name='despacho_editar'),
    path('despachos/<int:pk>/anular/', despacho.anular_despacho, name='despacho_anular'),
    path('despachos/<int:pk>/cambiar_estado/', despacho.cambiar_estado_despacho, name='despacho_cambiar_estado'),

    # ============================================
    # DASHBOARD Y REPORTES
    # ============================================
    path('dashboard/', dashboard.dashboard_general, name='dashboard_general'),
    path('dashboard/regional/', dashboard.dashboard_regional, name='dashboard_regional'),
    path('reportes/csv/', dashboard.reporte_csv, name='reporte_csv'),
    path('reportes/pdf/', dashboard.reporte_pdf, name='reporte_pdf'),
    # API
    path('api/', include('App.api.urls')),
]