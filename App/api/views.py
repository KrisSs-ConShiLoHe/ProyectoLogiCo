from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from ..models import Farmacia, Motorista, Moto, AsignacionMoto, AsignacionFarmacia, Despacho
from ..serializers import (
    FarmaciaSerializer, MotoristaSerializer, MotoSerializer,
    AsignacionMotoSerializer, AsignacionFarmaciaSerializer, DespachoSerializer
)
from .permissions import IsAdminOrSupervisorForWrite, IsSupervisorForCreate, IsMotoristaOrSupervisorOrAdminForState


class FarmaciaViewSet(viewsets.ModelViewSet):
    queryset = Farmacia.objects.all()
    serializer_class = FarmaciaSerializer
    permission_classes = [IsAdminOrSupervisorForWrite]


class MotoristaViewSet(viewsets.ModelViewSet):
    queryset = Motorista.objects.select_related('usuario').all()
    serializer_class = MotoristaSerializer
    permission_classes = [IsAdminOrSupervisorForWrite]


class MotoViewSet(viewsets.ModelViewSet):
    queryset = Moto.objects.all()
    serializer_class = MotoSerializer
    permission_classes = [IsAdminOrSupervisorForWrite]


class AsignacionMotoViewSet(viewsets.ModelViewSet):
    queryset = AsignacionMoto.objects.select_related('motorista', 'moto').all()
    serializer_class = AsignacionMotoSerializer
    # Create only for Supervisor; writes limited to Supervisor/Admin
    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [IsSupervisorForCreate]
        else:
            permission_classes = [IsAdminOrSupervisorForWrite]
        return [p() for p in permission_classes]

    @action(detail=True, methods=['post'])
    def reemplazar(self, request, pk=None):
        asignacion = self.get_object()
        motorista = asignacion.motorista
        nueva_moto_id = request.data.get('moto_id')
        if not nueva_moto_id:
            return Response({'detail': 'moto_id required'}, status=status.HTTP_400_BAD_REQUEST)
        # deactivate current
        asignacion.activa = False
        asignacion.save()
        # create new
        from ..models import Moto as MotoModel, AsignacionMoto as AsignacionMotoModel
        try:
            moto = MotoModel.objects.get(pk=nueva_moto_id, disponible=True)
        except MotoModel.DoesNotExist:
            return Response({'detail': 'Moto no disponible'}, status=status.HTTP_400_BAD_REQUEST)
        nueva = AsignacionMotoModel.objects.create(motorista=motorista, moto=moto, activa=True)
        serializer = self.get_serializer(nueva)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AsignacionFarmaciaViewSet(viewsets.ModelViewSet):
    queryset = AsignacionFarmacia.objects.select_related('motorista', 'farmacia').all()
    serializer_class = AsignacionFarmaciaSerializer

    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [IsSupervisorForCreate]
        else:
            permission_classes = [IsAdminOrSupervisorForWrite]
        return [p() for p in permission_classes]

    @action(detail=True, methods=['post'])
    def reemplazar(self, request, pk=None):
        asignacion = self.get_object()
        motorista = asignacion.motorista
        nueva_farmacia_id = request.data.get('farmacia_id')
        if not nueva_farmacia_id:
            return Response({'detail': 'farmacia_id required'}, status=status.HTTP_400_BAD_REQUEST)
        asignacion.activa = False
        asignacion.save()
        from ..models import Farmacia as FarmaciaModel, AsignacionFarmacia as AsignacionFarmaciaModel
        try:
            farmacia = FarmaciaModel.objects.get(pk=nueva_farmacia_id)
        except FarmaciaModel.DoesNotExist:
            return Response({'detail': 'Farmacia no encontrada'}, status=status.HTTP_400_BAD_REQUEST)
        nueva = AsignacionFarmaciaModel.objects.create(motorista=motorista, farmacia=farmacia, activa=True)
        serializer = self.get_serializer(nueva)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class DespachoViewSet(viewsets.ModelViewSet):
    queryset = Despacho.objects.select_related('farmacia_origen', 'motorista_asignado').all()
    serializer_class = DespachoSerializer

    def get_permissions(self):
        # For state changes we may use the custom permission; create allowed for operadores/supervisores/admin/gerente
        if self.action in ['partial_update', 'update']:
            permission_classes = [IsMotoristaOrSupervisorOrAdminForState]
        elif self.action == 'create':
            # creation allowed to operador, supervisor, admin, gerente - let backend view-level check
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated]
        return [p() for p in permission_classes]

    @action(detail=True, methods=['post'])
    def cambiar_estado(self, request, pk=None):
        despacho = self.get_object()
        nuevo_estado = request.data.get('estado')
        # validate transitions (same logic as views)
        transiciones_validas = {
            'PENDIENTE': ['EN_RUTA', 'ANULADO'],
            'EN_RUTA': ['ENTREGADO', 'INCIDENCIA', 'ANULADO'],
            'ENTREGADO': [],
            'ANULADO': [],
            'INCIDENCIA': ['EN_RUTA', 'ENTREGADO'],
        }
        if nuevo_estado not in transiciones_validas.get(despacho.estado, []):
            return Response({'detail': 'Transición no válida'}, status=status.HTTP_400_BAD_REQUEST)
        despacho.estado = nuevo_estado
        despacho.save()
        serializer = self.get_serializer(despacho)
        return Response(serializer.data)
