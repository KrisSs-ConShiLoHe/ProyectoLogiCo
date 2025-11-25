"""
Formularios para las vistas
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm as DjangoUserCreationForm
from .models import Farmacia, Motorista, Moto, MantenimientoMoto, AsignacionMoto, AsignacionFarmacia, Despacho, User, ProductoPedido


# ============================================
# FORMULARIOS DE AUTENTICACIÓN
# ============================================

class LoginForm(forms.Form):
    """
    Formulario de inicio de sesión personalizado.
    """
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Usuario',
            'required': True
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contraseña',
            'required': True
        })
    )


class UserCreationForm(DjangoUserCreationForm):
    """
    Formulario de creación de usuario.
    """
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    rol = forms.ChoiceField(choices=User.ROLES, widget=forms.Select(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'rol', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if 'class' not in self.fields[field].widget.attrs:
                self.fields[field].widget.attrs['class'] = 'form-control'


# ============================================
# FORMULARIOS DE MODELOS
# ============================================

class FarmaciaForm(forms.ModelForm):

    dias_operativos = forms.MultipleChoiceField(
        choices=Farmacia.DIAS_SEMANA,
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Día Operativo"
    )
    
    region = forms.ChoiceField(
        choices=Farmacia.LAS_REGIONES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True,
        label="Regiones"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.dias_operativos:
            self.fields['region'].initial = self.instance.get_region_list()
            # Convertir el string separado por comas a lista
            dias_list = self.instance.get_dias_operativos_list()
            self.fields['dias_operativos'].initial = dias_list
        # if self.instance and self.instance.pk:
        #     self.fields['region'].initial = self.instance.get_region_list()
        #     self.fields['dias_operativos'].initial = self.instance.get_dias_operativos_list()

    def clean_dias_operativos(self):
        """Validación personalizada para días operativos"""
        dias = self.cleaned_data.get('dias_operativos')

        # Verificar que sea una lista
        if not isinstance(dias, list):
            raise forms.ValidationError("Debe seleccionar al menos un día")
        
        # Verificar que todos los valores sean válidos
        dias_validos = [codigo for codigo, _ in Farmacia.DIAS_SEMANA]
        for dia in dias:
            if dia not in dias_validos:
                raise forms.ValidationError(f"Día inválido: {dia}")
        
        return dias
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Obtener los días operativos como lista
        dias_operativos_list = self.cleaned_data.get('dias_operativos')
        
        # Guardar como string separado por comas
        if isinstance(dias_operativos_list, list):
            instance.dias_operativos = ','.join(dias_operativos_list)
        
        if commit:
            instance.save()
        
        return instance

    horario_recepcion_inicio = forms.TimeField(
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        required=True,
        label="Horario de Recepción (Inicio)"
    )

    horario_recepcion_fin = forms.TimeField(
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        required=True,
        label="Horario de Recepción (Fin)"
    )

    class Meta:
        model = Farmacia
        fields = [
            'identificador_unico', 'direccion', 'region', 'comuna',
            'horario_recepcion_inicio', 'horario_recepcion_fin', 'dias_operativos', 'telefono', 'correo', 'imagen', 'activa'
        ]
        widgets = {
            'identificador_unico': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ID'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dirección'}),
            'comuna': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Comuna'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono'}),
            'correo': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Correo electrónico'}),
            # Imagen usualmente manejada en template
        }


class MotoristaForm(forms.ModelForm):
    class Meta:
        model = Motorista
        fields = [
            'usuario', 'identificador_unico', 'nombre', 'apellido_paterno', 'apellido_materno', 'rut',
            'domicilio', 'correo', 'telefono', 'emergencia_nombre', 'emergencia_telefono',
            'licencia_tipo', 'licencia_vigente', 'disponibilidad', "posesion_moto", 'imagen', 'activo'
        ]
        widgets = {
            'usuario': forms.Select(attrs={'class': 'form-control'}),
            'identificador_unico': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ID único'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre'}),
            'apellido_paterno': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellido Paterno'}),
            'apellido_materno': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellido Materno'}),
            'rut': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'RUT'}),
            'domicilio': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Domicilio'}),
            'correo': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Correo electrónico'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número de teléfono'}),
            'emergencia_nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre Emergencia'}),
            'emergencia_telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono Emergencia'}),
            'licencia_tipo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tipo de licencia'}),
            'licencia_vigente': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'disponibilidad': forms.Select(attrs={'class': 'form-select'}),
            "posesion_moto": forms.Select(attrs={'class': 'form-select'}),
            'imagen': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class MotoForm(forms.ModelForm):
    class Meta:
        model = Moto
        fields = [
            'identificador_unico', 'patente', 'marca', 'modelo', 'color', 'anio_fabricacion',
            'numero_chasis', 'numero_motor',
            'permiso_circulacion_vigente', 'revision_tecnica_vigente',
            'consumo_combustible', 'capacidad_carga', 'estado',
            'velocidad_promedio', 'frenadas_bruscas', 'aceleraciones_rapidas', 'tiempo_inactividad_horas', 'imagen'
        ]
        widgets = {
            'identificador_unico': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ID único'}),
            'patente': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Patente/placa'}),
            'marca': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Kawasaki'}),
            'modelo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ZX-4RR'}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Verde'}),
            'anio_fabricacion': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '2022', 'min': '1970'}),
            'numero_chasis': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '1HFJH77F7H7123456'}),
            'numero_motor': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'G7852A012345'}),
            'permiso_circulacion_vigente': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'revision_tecnica_vigente': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'consumo_combustible': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Consumo promedio de combustible en litros por cada 100 km | Ej: 2.8', 'min': '0'}),
            'capacidad_carga': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Peso máximo de carga permitido por el fabricante en kilogramos (incluyendo conductor) | Ej: 180.5', 'min': '0'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'velocidad_promedio': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Velocidad promedio registrada en operaciones (dato de telemática) | Ej: 45.2', 'min': '0'}),
            'frenadas_bruscas': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Número promedio de eventos de frenada brusca por día (dato de telemática) | Ej: 5'}),
            'aceleraciones_rapidas': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Número promedio de aceleraciones rápidas/agresivas por día (dato de telemática) | Ej: 7'}),
            'tiempo_inactividad_horas': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Horas promedio de motor encendido sin movimiento por día | Ej: 1', 'min': '0'}),
            'imagen': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

class MantenimientoMotoForm(forms.ModelForm):
    class Meta:
        model = MantenimientoMoto
        fields = ['fecha_mantenimiento', 'descripcion', 'tipo_servicio', 'kilometraje', 'proximo_mantenimiento']
        widgets = {
            'fecha_mantenimiento': forms.DateInput(attrs={'class': 'form-control extra-mantenimiento', 'type': 'date'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control extra-mantenimiento', 'rows': 3}),
            'tipo_servicio': forms.TextInput(attrs={'class': 'form-control extra-mantenimiento'}),
            'kilometraje': forms.NumberInput(attrs={'class': 'form-control extra-mantenimiento'}),
            'proximo_mantenimiento': forms.DateInput(attrs={'class': 'form-control extra-mantenimiento', 'type': 'date'}),
        }

    # Puedes sobrescribir __init__ para mostrar/ocultar campos según tipo_movimiento
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove widget replacement with HiddenInput to preserve CSS classes for JS control of visibility.
        # Let JS and CSS control dynamic visibility client-side.
        # To handle initial display, users can rely on JS initialization or server-rendered CSS classes if needed.
        # So do not replace widgets here.
        # This is to avoid elements disappearing from the DOM visually breaking JS selectors.
        # If needed, validation logic should be handled separately.
        pass


class AsignacionMotoForm(forms.ModelForm):
    """
    Formulario para crear/editar Asignaciones de Moto.
    """
    class Meta:
        model = AsignacionMoto
        fields = ['motorista', 'moto']
        widgets = {
            'motorista': forms.Select(attrs={'class': 'form-control'}),
            'moto': forms.Select(attrs={'class': 'form-control'}),
        }
    def __init__(self, *args, **kwargs):
        asignacion_actual = kwargs.pop('asignacion_actual', None)
        super().__init__(*args, **kwargs)
        editing = asignacion_actual and asignacion_actual.pk  # Determina editing basado en asignacion_actual
        if editing:
            moto_actual = asignacion_actual.moto
            motorista_actual = asignacion_actual.motorista
            motos_disponibles = Moto.objects.filter(estado='OPERATIVO').exclude(asignacionmoto__activa=True)
            motoristas_disponibles = Motorista.objects.filter(posesion_moto='SIN_MOTO').exclude(asignacionmoto__activa=True)
            # Añade el recurso actual aunque esté ocupado
            motos = Moto.objects.filter(pk=moto_actual.pk) | motos_disponibles
            motoristas = Motorista.objects.filter(pk=motorista_actual.pk) | motoristas_disponibles
            self.fields['moto'].queryset = motos.distinct()
            self.fields['motorista'].queryset = motoristas.distinct()
        else:
            self.fields['moto'].queryset = Moto.objects.filter(estado='OPERATIVO').exclude(asignacionmoto__activa=True)
            self.fields['motorista'].queryset = Motorista.objects.filter(posesion_moto='SIN_MOTO').exclude(asignacionmoto__activa=True)
        # Presentación
        self.fields['moto'].label_from_instance = lambda obj: f"{obj.patente} - {obj.marca} {obj.modelo}"
        self.fields['motorista'].label_from_instance = lambda obj: f"{obj.nombre} - RUT: {obj.rut}"


class AsignacionFarmaciaForm(forms.ModelForm):
    """
    Formulario para crear/editar Asignaciones de Farmacia.
    """
    class Meta:
        model = AsignacionFarmacia
        fields = ['motorista', 'farmacia']
        widgets = {
            'motorista': forms.Select(attrs={'class': 'form-control'}),
            'farmacia': forms.Select(attrs={'class': 'form-control'}),
        }
    def __init__(self, *args, **kwargs):
        asignacion_actual = kwargs.pop('asignacion_actual', None)
        super().__init__(*args, **kwargs)
        editing = asignacion_actual and asignacion_actual.pk  # Determina editing basado en asignacion_actual
        if editing:
            # farmacia_actual = asignacion_actual.farmacia
            motorista_actual = asignacion_actual.motorista

            farmacias = Farmacia.objects.all()
            # self.fields['farmacia'].queryset = Farmacia.objects.all()
            motoristas_disponibles = Motorista.objects.filter(disponibilidad='DISPONIBLE').exclude(asignacionfarmacia__activa=True)

            # Añade el recurso actual aunque esté ocupado
            # farmacias = Farmacia.objects.filter(pk=farmacia_actual.pk) | farmacias_disponibles
            motoristas = Motorista.objects.filter(pk=motorista_actual.pk) | motoristas_disponibles
            self.fields['farmacia'].queryset = farmacias.distinct()
            self.fields['motorista'].queryset = motoristas.distinct()
        else:
            # self.fields['farmacia'].queryset = Farmacia.objects.filter().exclude(asignacionfarmacia__activa=True)
            self.fields['farmacia'].queryset = Farmacia.objects.all()
            self.fields['motorista'].queryset = Motorista.objects.filter(disponibilidad='DISPONIBLE').exclude(asignacionfarmacia__activa=True)
        # Presentación (ajusta según tus campos)
        self.fields['farmacia'].label_from_instance = lambda obj: f"{obj.nombre} - {obj.direccion}"  # Asumiendo campos como nombre y direccion
        self.fields['motorista'].label_from_instance = lambda obj: f"{obj.nombre} - RUT: {obj.rut}"

class DespachoForm(forms.ModelForm):
    class Meta:
        model = Despacho
        fields = [
            'identificador_unico', 'farmacia_origen', 'motorista_asignado', 'direccion_entrega',
            'estado', 'tipo_movimiento',
            'fecha_hora_toma_pedido', 'fecha_hora_salida_farmacia', 'fecha_hora_estimada_llegada',
            'numero_receta', 'fecha_emision_receta', 'medico_prescribiente', 'paciente_nombre', 'paciente_edad', 'tipo_establecimiento_traslado',
            'motivo_reenvio', 
            'incidencia_motivo', 'incidencia_fecha_hora', 'imagen',
        ]
        widgets = {
            # Personaliza widgets según convenga, por ejemplo fechas, selects y inputs
            'identificador_unico': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ID único'}),
            'farmacia_origen': forms.Select(attrs={'class': 'form-select'}),
            'motorista_asignado': forms.Select(attrs={'class': 'form-select'}),
            'direccion_entrega': forms.TextInput(attrs={'class': 'form-control'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'tipo_movimiento': forms.Select(attrs={'class': 'form-select', 'id': 'id_tipo_movimiento'}),
            'fecha_hora_toma_pedido': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'fecha_hora_salida_farmacia': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'fecha_hora_estimada_llegada': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'numero_receta': forms.TextInput(attrs={'class': 'form-control extra-con-receta'}),
            'fecha_emision_receta': forms.DateInput(attrs={'class': 'form-control extra-con-receta', 'type': 'date'}),
            'medico_prescribiente': forms.TextInput(attrs={'class': 'form-control extra-con-receta'}),
            'paciente_nombre': forms.TextInput(attrs={'class': 'form-control extra-con-receta'}),
            'paciente_edad': forms.NumberInput(attrs={'class': 'form-control extra-con-receta'}),
            'tipo_establecimiento_traslado': forms.TextInput(attrs={'class': 'form-control extra-con-traslado'}),
            'motivo_reenvio': forms.Textarea(attrs={'class': 'form-control extra-reenvio', 'rows':2}),
            'incidencia_motivo': forms.Textarea(attrs={'class': 'form-control extra-incidencia', 'rows':2}),
            'incidencia_fecha_hora': forms.DateTimeInput(attrs={'class': 'form-control extra-incidencia', 'type': 'datetime-local'}),
            'imagen': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Inicialmente, mostrar ningún motorista (se filtra dinámicamente)
        self.fields['motorista_asignado'].queryset = Motorista.objects.none()
        
        if 'farmacia_origen' in self.data:
            try:
                farmacia_id = int(self.data.get('farmacia_origen'))
                # Filtrar motoristas asignados activamente a esa farmacia
                asignaciones = AsignacionFarmacia.objects.filter(farmacia_id=farmacia_id, activa=True)
                motoristas_ids = asignaciones.values_list('motorista_id', flat=True)
                self.fields['motorista_asignado'].queryset = Motorista.objects.filter(id__in=motoristas_ids)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk:
            # Si editando, incluir el motorista actual en el queryset (además de los asignados a la farmacia actual)
            farmacia_id = self.instance.farmacia_origen_id
            asignaciones = AsignacionFarmacia.objects.filter(farmacia_id=farmacia_id, activa=True)
            # motoristas_ids = asignaciones.values_list('motorista_id', flat=True)
            # motoristas_ids = list(motoristas_ids) + [self.instance.motorista_asignado_id]
            motoristas_ids = set(asignaciones.values_list('motorista_id', flat=True))
            motoristas_ids.add(self.instance.motorista_asignado_id)
            self.fields['motorista_asignado'].queryset = Motorista.objects.filter(id__in=motoristas_ids).distinct()


class ProductoPedidoForm(forms.ModelForm):
    """
    Formulario para informacion de los productos que contiene el Despacho
    """
    class Meta:
        model = ProductoPedido
        fields = ['nombre_producto', 'cantidad', 'numero_lote', 'numero_serie']
        widgets = {
            'nombre_producto': forms.TextInput(attrs={'class': 'form-control extra-producto'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control extra-producto'}),
            'numero_lote': forms.TextInput(attrs={'class': 'form-control extra-producto'}),
            'numero_serie': forms.TextInput(attrs={'class': 'form-control extra-producto'}),
        }

class DespachoEstadoForm(forms.ModelForm):
    """
    Formulario para cambiar el estado de un Despacho.
    """
    class Meta:
        model = Despacho
        fields = ['estado']
        widgets = {
            'estado': forms.Select(attrs={'class': 'form-control'}),
        }


    # Puedes sobrescribir __init__ para mostrar/ocultar campos según tipo_movimiento
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        pass

# Agrega un pequeño formset para productos si quieres cargarlos en el mismo template al editar/crear.
