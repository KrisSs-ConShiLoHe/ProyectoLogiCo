from rest_framework import serializers
from .models import User, Farmacia, Motorista, Moto, AsignacionMoto, AsignacionFarmacia, Despacho


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'rol']
        read_only_fields = ['id']


class FarmaciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Farmacia
        fields = ['id', 'nombre', 'direccion', 'region', 'comuna', 'codigo_externo']
        read_only_fields = ['id']


class MotoristaSerializer(serializers.ModelSerializer):
    usuario = UserSerializer(read_only=True)
    usuario_id = serializers.PrimaryKeyRelatedField(
        write_only=True, source='usuario', queryset=User.objects.filter(rol='MOTORISTA')
    )

    class Meta:
        model = Motorista
        fields = ['id', 'usuario', 'usuario_id', 'rut', 'licencia_vigente']
        read_only_fields = ['id']


class MotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Moto
        fields = ['id', 'patente', 'marca', 'modelo', 'disponible']
        read_only_fields = ['id']


class AsignacionMotoSerializer(serializers.ModelSerializer):
    motorista = MotoristaSerializer(read_only=True)
    motorista_id = serializers.PrimaryKeyRelatedField(write_only=True, source='motorista', queryset=Motorista.objects.all())
    moto = MotoSerializer(read_only=True)
    moto_id = serializers.PrimaryKeyRelatedField(write_only=True, source='moto', queryset=Moto.objects.filter(disponible=True))

    class Meta:
        model = AsignacionMoto
        fields = ['id', 'motorista', 'motorista_id', 'moto', 'moto_id', 'fecha_asignacion', 'activa']
        read_only_fields = ['id', 'fecha_asignacion']


class AsignacionFarmaciaSerializer(serializers.ModelSerializer):
    motorista = MotoristaSerializer(read_only=True)
    motorista_id = serializers.PrimaryKeyRelatedField(write_only=True, source='motorista', queryset=Motorista.objects.all())
    farmacia = FarmaciaSerializer(read_only=True)
    farmacia_id = serializers.PrimaryKeyRelatedField(write_only=True, source='farmacia', queryset=Farmacia.objects.all())

    class Meta:
        model = AsignacionFarmacia
        fields = ['id', 'motorista', 'motorista_id', 'farmacia', 'farmacia_id', 'fecha_asignacion', 'activa']
        read_only_fields = ['id', 'fecha_asignacion']


class DespachoSerializer(serializers.ModelSerializer):
    farmacia_origen = FarmaciaSerializer(read_only=True)
    farmacia_origen_id = serializers.PrimaryKeyRelatedField(write_only=True, source='farmacia_origen', queryset=Farmacia.objects.all())
    motorista_asignado = MotoristaSerializer(read_only=True)
    motorista_asignado_id = serializers.PrimaryKeyRelatedField(write_only=True, source='motorista_asignado', queryset=Motorista.objects.all())

    class Meta:
        model = Despacho
        fields = [
            'id', 'id_pedido_externo', 'tipo_movimiento', 'farmacia_origen', 'farmacia_origen_id',
            'motorista_asignado', 'motorista_asignado_id', 'fecha_hora_creacion', 'fecha_hora_despacho',
            'fecha_hora_entrega', 'estado', 'requiere_receta',
        ]
        read_only_fields = ['id', 'fecha_hora_creacion', 'fecha_hora_despacho', 'fecha_hora_entrega']
