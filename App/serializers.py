from rest_framework import serializers
from .models import User, Farmacia, Motorista, Moto, AsignacionMoto, AsignacionFarmacia, Despacho, ProductoPedido, MantenimientoMoto

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'rol']
        read_only_fields = ['id']

class FarmaciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Farmacia
        fields = [
            'id', 'identificador_unico', 'nombre', 'direccion', 'region', 'comuna',
            'horario_recepcion_inicio', 'horario_recepcion_fin', 'dias_operativos', 'telefono', 'correo', 'imagen'
        ]
        read_only_fields = ['id']

class MotoristaSerializer(serializers.ModelSerializer):
    usuario = UserSerializer(read_only=True)
    usuario_id = serializers.PrimaryKeyRelatedField(
        write_only=True, source='usuario', queryset=User.objects.filter(rol='MOTORISTA')
    )
    class Meta:
        model = Motorista
        fields = [
            'id', 'identificador_unico', 'usuario', 'usuario_id', 'nombre', 'apellido_paterno', 'apellido_materno',
            'rut', 'domicilio', 'correo', 'telefono', 'emergencia_nombre', 'emergencia_telefono',
            'licencia_tipo', 'licencia_vigente', 'disponibilidad', 'posesion_moto', 'activo', 'imagen'
        ]
        read_only_fields = ['id']

class MotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Moto
        fields = [
            'id', 'identificador_unico', 'patente', 'marca', 'modelo', 'color', 'anio_fabricacion',
            'numero_chasis', 'numero_motor', 'permiso_circulacion_vigente', 'revision_tecnica_vigente',
            'consumo_combustible', 'capacidad_carga', 'estado', 'imagen',
            'velocidad_promedio', 'frenadas_bruscas', 'aceleraciones_rapidas', 'tiempo_inactividad_horas',
        ]
        read_only_fields = ['id']

class AsignacionMotoSerializer(serializers.ModelSerializer):
    motorista = MotoristaSerializer(read_only=True)
    motorista_id = serializers.PrimaryKeyRelatedField(write_only=True, source='motorista', queryset=Motorista.objects.all())
    moto = MotoSerializer(read_only=True)
    moto_id = serializers.PrimaryKeyRelatedField(write_only=True, source='moto', queryset=Moto.objects.all())

    class Meta:
        model = AsignacionMoto
        fields = ['id', 'motorista', 'motorista_id', 'moto', 'moto_id', 'fecha_asignacion', "fecha_desasignacion", 'activa']
        read_only_fields = ['id', 'fecha_asignacion', "fecha_desasignacion",]
        
class AsignacionFarmaciaSerializer(serializers.ModelSerializer):
    motorista = MotoristaSerializer(read_only=True)
    motorista_id = serializers.PrimaryKeyRelatedField(write_only=True, source='motorista', queryset=Motorista.objects.all())
    farmacia = FarmaciaSerializer(read_only=True)
    farmacia_id = serializers.PrimaryKeyRelatedField(write_only=True, source='farmacia', queryset=Farmacia.objects.all())

    class Meta:
        model = AsignacionFarmacia
        fields = ['id', 'motorista', 'motorista_id', 'farmacia', 'farmacia_id', 'fecha_asignacion', "fecha_desasignacion", 'activa']
        read_only_fields = ['id', 'fecha_asignacion', "fecha_desasignacion"]
    

class DespachoSerializer(serializers.ModelSerializer):
    farmacia_origen = FarmaciaSerializer(read_only=True)
    farmacia_origen_id = serializers.PrimaryKeyRelatedField(write_only=True, source='farmacia_origen', queryset=Farmacia.objects.all())
    motorista_asignado = MotoristaSerializer(read_only=True)
    motorista_asignado_id = serializers.PrimaryKeyRelatedField(write_only=True, source='motorista_asignado', queryset=Motorista.objects.all())

    class Meta:
        model = Despacho
        fields = [
            'id', 'identificador_unico', 'farmacia_origen', 'farmacia_origen_id', 'motorista_asignado', 'motorista_asignado_id',
            'fecha_hora_creacion', 'fecha_hora_toma_pedido', 'fecha_hora_salida_farmacia', 'fecha_hora_despacho',
            'fecha_hora_estimada_llegada', 'direccion_entrega', 'imagen',
            'estado', 'incidencia_motivo', 'incidencia_fecha_hora', 'motivo_reenvio',
            'tipo_movimiento', 'numero_receta', 'fecha_emision_receta', 'medico_prescribiente',
            'paciente_nombre', 'paciente_edad', 'tipo_establecimiento_traslado', 'productos'
        ]
        read_only_fields = ['id', 'fecha_hora_creacion']


class MantenimientoMotoSerializer(serializers.ModelSerializer):
    moto = MotoSerializer(read_only=True)
    moto_id = serializers.PrimaryKeyRelatedField(write_only=True, source='moto', queryset=Moto.objects.all())

    class Meta:
        model = MantenimientoMoto
        fields = ['id', 'moto', 'moto_id', 'fecha_mantenimiento', 'descripcion', 'tipo_servicio', 'kilometraje', 'proximo_mantenimiento']
        read_only_fields = ['id']


class ProductoPedidoSerializer(serializers.ModelSerializer):
    despacho = DespachoSerializer(read_only=True)
    despacho_id = serializers.PrimaryKeyRelatedField(write_only=True, source='despacho', queryset=Despacho.objects.all())
    class Meta:
        model = ProductoPedido
        fields = [
            'id', 'codigo_producto', 'nombre_producto', 'cantidad', 'numero_lote', 'numero_serie'
        ]
        read_only_fields = ['id']