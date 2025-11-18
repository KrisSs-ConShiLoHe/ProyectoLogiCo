from rest_framework.routers import DefaultRouter
from django.urls import path, include
from ..api.views import (
    FarmaciaViewSet, MotoristaViewSet, MotoViewSet,
    AsignacionMotoViewSet, AsignacionFarmaciaViewSet, DespachoViewSet,
)

router = DefaultRouter()
router.register(r'farmacias', FarmaciaViewSet, basename='api-farmacia')
router.register(r'motoristas', MotoristaViewSet, basename='api-motorista')
router.register(r'motos', MotoViewSet, basename='api-moto')
router.register(r'asignaciones_moto', AsignacionMotoViewSet, basename='api-asignacion-moto')
router.register(r'asignaciones_farmacia', AsignacionFarmaciaViewSet, basename='api-asignacion-farmacia')
router.register(r'despachos', DespachoViewSet, basename='api-despacho')

urlpatterns = [
    path('', include(router.urls)),
]
