"""
Formularios para las vistas
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm as DjangoUserCreationForm
from .models import Farmacia, Motorista, Moto, MantenimientoMoto, AsignacionMoto, AsignacionFarmacia, Despacho, User, ProductoPedido, DocumentacionMoto, PermisoCirculacion
from django.utils import timezone
from django.forms import inlineformset_factory


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
    
    def clean_latitud(self):
        latitud = self.cleaned_data.get('latitud')
        if latitud is not None and not (-90 <= latitud <= 90):
            raise forms.ValidationError("La latitud debe estar entre -90 y 90.")
        return latitud
    
    def clean_longitud(self):
        longitud = self.cleaned_data.get('longitud')
        if longitud is not None and not (-180 <= longitud <= 180):
            raise forms.ValidationError("La longitud debe estar entre -180 y 180.")
        return longitud
    
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
            'direccion', 'region', 'comuna', 'provincia', 'localidad',
            'horario_recepcion_inicio', 'horario_recepcion_fin', 'dias_operativos', 'telefono', 'correo',
            'latitud', 'longitud', 'imagen', 'activa'
        ]
        widgets = {
            'direccion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dirección'}),
            'comuna': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Comuna'}),
            'provincia': forms.TextInput(attrs={'class': 'form-control'}),
            'localidad': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono'}),
            'correo': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Correo electrónico'}),
            'latitud': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001', 'min': '-90', 'max': '90'}),
            'longitud': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001', 'min': '-180', 'max': '180'}),
            # Imagen usualmente manejada en template
        }


class MotoristaForm(forms.ModelForm):
    class Meta:
        model = Motorista
        fields = [
            'usuario', 'pasaporte', 'nombre', 'apellido_paterno', 'apellido_materno', 'rut',
            'domicilio', 'correo', 'telefono', 'emergencia_nombre', 'emergencia_telefono',
            'licencia_tipo', 'fecha_ultimo_control_licencia', 'fecha_proximo_control_licencia', 'disponibilidad', "posesion_moto", 'imagen', 'imagen_licencia', 'activo',
            'numero_poliza_seguro', 'fecha_vencimiento_seguro', 'documento_seguro_pdf'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre'}),
            'pasaporte': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido_paterno': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellido Paterno'}),
            'apellido_materno': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellido Materno'}),
            'rut': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'RUT'}),
            'domicilio': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Domicilio'}),
            'correo': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Correo electrónico'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número de teléfono'}),
            'emergencia_nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre Emergencia'}),
            'emergencia_telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono Emergencia'}),
            'licencia_tipo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tipo de licencia'}),
            'fecha_ultimo_control_licencia': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_proximo_control_licencia': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'disponibilidad': forms.Select(attrs={'class': 'form-select'}),
            "posesion_moto": forms.Select(attrs={'class': 'form-select'}),
            'imagen': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'imagen_licencia': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'numero_poliza_seguro': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_vencimiento_seguro': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'documento_seguro_pdf': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
    

    def clean_fecha_proximo_control_licencia(self):
        fecha_proximo = self.cleaned_data.get('fecha_proximo_control_licencia')
        # 💡 Se permite que la fecha sea NULL, pero si se ingresa, no puede ser pasado
        if fecha_proximo and fecha_proximo < timezone.now().date():
            raise forms.ValidationError("La fecha de próximo control no puede ser en el pasado.")
        return fecha_proximo
    
    def clean_fecha_vencimiento_seguro(self):
        fecha_vencimiento = self.cleaned_data.get('fecha_vencimiento_seguro')
        # 💡 Se permite que la fecha sea NULL, pero si se ingresa, no puede ser pasado
        if fecha_vencimiento and fecha_vencimiento < timezone.now().date():
            raise forms.ValidationError("La fecha de vencimiento del seguro no puede ser en el pasado.")
        return fecha_vencimiento
    
    # def save(self, commit=True):
    #     instance = super().save(commit=False)
        
    #     # Lógica para actualizar licencia_vigente
    #     fecha_proximo = instance.fecha_proximo_control_licencia
    #     if fecha_proximo and fecha_proximo >= timezone.now().date():
    #         instance.licencia_vigente = True
    #     else:
    #         instance.licencia_vigente = False
            
    #     if commit:
    #         instance.save()
    #     return instance


class MotoForm(forms.ModelForm):

    motorista_asignado = forms.ModelChoiceField(
        queryset=Motorista.objects.filter(posesion_moto='SIN_MOTO', activo=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Motorista Asignado"
    )

    class Meta:
        model = Moto
        fields = [
            'patente', 'marca', 'modelo', 'color', 'anio_fabricacion',
            'numero_chasis', 'numero_motor', 'duenio', 'motorista_asignado',
            'estado', 'consumo_combustible', 'capacidad_carga', 'velocidad_promedio', 
            'frenadas_bruscas', 'aceleraciones_rapidas', 'tiempo_inactividad_horas', 'imagen'
        ]
        widgets = {
            'patente': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Patente/placa'}),
            'marca': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Kawasaki'}),
            'modelo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ZX-4RR'}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Verde'}),
            'anio_fabricacion': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '2022', 'min': '1970'}),
            'numero_chasis': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '1HFJH77F7H7123456'}),
            'numero_motor': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'G7852A012345'}),
            'duenio': forms.Select(attrs={'class': 'form-select'}),
            'consumo_combustible': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Consumo promedio de combustible en litros por cada 100 km | Ej: 2.8', 'min': '0'}),
            'capacidad_carga': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Peso máximo de carga permitido por el fabricante en kilogramos (incluyendo conductor) | Ej: 180.5', 'min': '0'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'velocidad_promedio': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Velocidad promedio registrada en operaciones (dato de telemática) | Ej: 45.2', 'min': '0'}),
            'frenadas_bruscas': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Número promedio de eventos de frenada brusca por día (dato de telemática) | Ej: 5'}),
            'aceleraciones_rapidas': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Número promedio de aceleraciones rápidas/agresivas por día (dato de telemática) | Ej: 7', 'min': '0'}),
            'tiempo_inactividad_horas': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Horas promedio de motor encendido sin movimiento por día | Ej: 1', 'min': '0'}),
            'imagen': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Si editando y dueño es MOTORISTA, incluir el motorista actual en el queryset
        if self.instance.pk and self.instance.duenio == 'MOTORISTA' and self.instance.motorista_asignado:
            self.fields['motorista_asignado'].queryset = (
                Motorista.objects.filter(posesion_moto='SIN_MOTO', activo=True) | 
                Motorista.objects.filter(pk=self.instance.motorista_asignado.pk)
            ).distinct()
            self.fields['motorista_asignado'].initial = self.instance.motorista_asignado

    def clean(self):
        cleaned_data = super().clean()
        duenio = cleaned_data.get('duenio')
        motorista_asignado = cleaned_data.get('motorista_asignado')
        
        if duenio == 'MOTORISTA' and not motorista_asignado:
            raise forms.ValidationError("Debe seleccionar un motorista cuando el dueño es 'MOTORISTA'.")
        
        # Limpiar motorista si dueño es EMPRESA
        if duenio == 'EMPRESA':
            cleaned_data['motorista_asignado'] = None
            
        return cleaned_data


class MantenimientoMotoForm(forms.ModelForm):
    class Meta:
        model = MantenimientoMoto
        fields = ['fecha_mantenimiento', 'descripcion', 'tipo_servicio', 'servicio_preventivo', 'kilometraje', 'proximo_mantenimiento']
        widgets = {
            'fecha_mantenimiento': forms.DateInput(attrs={'class': 'form-control extra-mantenimiento', 'type': 'date'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control extra-mantenimiento', 'rows': '3'}),
            'tipo_servicio': forms.Select(attrs={'class': 'form-select extra-mantenimiento', 'id': 'id_tipo_servicio'}),
            'servicio_preventivo': forms.Select(attrs={'class': 'form-select extra-mantenimiento', 'id': 'id_servicio_preventivo'}),
            'kilometraje': forms.NumberInput(attrs={'class': 'form-control extra-mantenimiento', 'min': '0'}),
            'proximo_mantenimiento': forms.DateInput(attrs={'class': 'form-control extra-mantenimiento', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer que subtipo_preventivo no sea requerido inicialmente
        self.fields['servicio_preventivo'].required = False

    def clean(self):
        cleaned_data = super().clean()
        tipo_servicio = cleaned_data.get('tipo_servicio')
        servicio_preventivo = cleaned_data.get('servicio_preventivo')
        
        # Validar que si es PREVENTIVO, debe tener subtipo
        if tipo_servicio == 'PREVENTIVO' and not servicio_preventivo:
            self.add_error('servicio_preventivo', 'Debe seleccionar el tipo de servicio preventivo')
        
        # Limpiar subtipo si no es preventivo
        if tipo_servicio != 'PREVENTIVO':
            cleaned_data['servicio_preventivo'] = None
        
        return cleaned_data
    

class DocumentacionMotoForm(forms.ModelForm):
    class Meta:
        model = DocumentacionMoto
        fields = ['revision_tecnica_vencimiento', 'seguro_soap_vencimiento', 'revision_tecnica_archivo', 'seguro_soap_archivo', 'pago_multas_comprobante']
        widgets = {
            'revision_tecnica_vencimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'seguro_soap_vencimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'revision_tecnica_archivo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'seguro_soap_archivo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'pago_multas_comprobante': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

class PermisoCirculacionForm(forms.ModelForm):
    class Meta:
        model = PermisoCirculacion
        fields = ['anio_permiso', 'valor_tasacion_SII', 'codigo_SII', 'tipo_combustible', 'tipo_octanaje', 'cilindrada', 'valor_neto_pago', 'valor_multa_pagado', 'valor_pagado_total', 'fecha_pago', 'forma_pago']
        widgets = {
            'anio_permiso': forms.NumberInput(attrs={'class': 'form-control', 'min': '2000'}),
            'valor_tasacion_SII': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'codigo_SII': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Codigo SII'}),
            'tipo_combustible': forms.Select(attrs={'class': 'form-select', 'id': 'id_tipo_combustible'}),
            'tipo_octanaje': forms.Select(attrs={'class': 'form-select', 'id': 'id_tipo_octanaje'}),
            'cilindrada': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'valor_neto_pago': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'valor_multa_pagado': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'valor_pagado_total': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'fecha_pago': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'forma_pago': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Forma de Pago'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer que subtipo_preventivo no sea requerido inicialmente
        self.fields['tipo_octanaje'].required = False

    def clean(self):
        cleaned_data = super().clean()
        tipo_combustible = cleaned_data.get('tipo_combustible')
        tipo_octanaje = cleaned_data.get('tipo_octanaje')
        
        # Validar que si es PREVENTIVO, debe tener subtipo
        if tipo_combustible == 'BENCINA' and not tipo_octanaje:
            self.add_error('tipo_octanaje', 'Debe seleccionar el tipo de combustible (octanos)')
        
        # Limpiar subtipo si no es preventivo
        if tipo_combustible != 'BENCINA':
            cleaned_data['tipo_octanaje'] = None
        
        return cleaned_data

PermisoCirculacionFormSet = inlineformset_factory(
    Moto, 
    PermisoCirculacion, 
    form=PermisoCirculacionForm, 
    extra=1, 
    can_delete=True
)

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
    class Meta:
        model = AsignacionFarmacia
        fields = ['motorista', 'farmacia', 'observaciones']
        widgets = {
            'motorista': forms.Select(attrs={'class': 'form-select'}),
            'farmacia': forms.Select(attrs={'class': 'form-select'}),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': '3',
                'placeholder': 'Motivo de la asignación (opcional)'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Determinar si estamos editando
        editando = self.instance and self.instance.pk
        
        if editando:
            motorista_actual = self.instance.motorista
            
            # Motoristas: Deben tener moto Y (estar disponibles O ser el actual)
            motoristas_disponibles = Motorista.objects.filter(
                posesion_moto='CON_MOTO',  # ← CRÍTICO: Solo con moto
                disponibilidad='DISPONIBLE',
                activo=True
            ).exclude(asignaciones_farmacia__activa=True)
            
            motoristas = (
                Motorista.objects.filter(pk=motorista_actual.pk) | 
                motoristas_disponibles
            ).distinct()
            
            self.fields['motorista'].queryset = motoristas
            self.fields['farmacia'].queryset = Farmacia.objects.all()
            
        else:  # Creación
            # CRÍTICO: Solo motoristas con moto Y disponibles
            self.fields['motorista'].queryset = Motorista.objects.filter(
                posesion_moto='CON_MOTO',  # ← Debe tener moto
                disponibilidad='DISPONIBLE',
                activo=True
            ).exclude(asignaciones_farmacia__activa=True)
            
            # Todas las farmacias disponibles (una farmacia puede tener muchos motoristas)
            self.fields['farmacia'].queryset = Farmacia.objects.all()
        
        # Mejorar presentación
        self.fields['farmacia'].label_from_instance = lambda obj: (
            f"{obj.identificador_unico} - {obj.nombre} ({obj.comuna}, {obj.region})"
        )
        self.fields['motorista'].label_from_instance = lambda obj: (
            f"{obj.identificador_unico} - {obj.nombre_completo} - "
            f"{'✓ Con moto' if obj.posesion_moto == 'CON_MOTO' else '✗ Sin moto'}"
        )
    
    def clean_motorista(self):
        """Validación adicional del motorista"""
        motorista = self.cleaned_data.get('motorista')
        
        if motorista and motorista.posesion_moto != 'CON_MOTO':
            raise forms.ValidationError(
                f'{motorista.nombre_completo} no tiene moto asignada. '
                f'Debe asignarle una moto antes de asignarlo a una farmacia.'
            )
        
        return motorista

class DespachoForm(forms.ModelForm):
    class Meta:
        model = Despacho
        fields = [
            'farmacia_origen', 'motorista_asignado', 'direccion_entrega',
            'estado', 'tipo_movimiento',
            'fecha_hora_toma_pedido', 'fecha_hora_salida_farmacia', 'fecha_hora_estimada_llegada',
            'numero_receta', 'fecha_emision_receta', 'medico_prescribiente', 'paciente_nombre', 'paciente_edad', 'tipo_establecimiento_traslado',
            'motivo_reenvio', 
            'incidencia_motivo', 'incidencia_fecha_hora', 'imagen',
        ]
        widgets = {
            # Personaliza widgets según convenga, por ejemplo fechas, selects y inputs
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
            'paciente_edad': forms.NumberInput(attrs={'class': 'form-control extra-con-receta', 'min': '0'}),
            'tipo_establecimiento_traslado': forms.TextInput(attrs={'class': 'form-control extra-con-traslado'}),
            'motivo_reenvio': forms.Textarea(attrs={'class': 'form-control extra-reenvio', 'rows': '2'}),
            'incidencia_motivo': forms.Textarea(attrs={'class': 'form-control extra-incidencia', 'rows': '2'}),
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
                self.fields['motorista_asignado'].queryset = Motorista.objects.filter(identificador_unico__in=motoristas_ids)
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
            self.fields['motorista_asignado'].queryset = Motorista.objects.filter(identificador_unico__in=motoristas_ids).distinct()


class ProductoPedidoForm(forms.ModelForm):
    """
    Formulario para informacion de los productos que contiene el Despacho
    """
    class Meta:
        model = ProductoPedido
        fields = ['codigo_producto', 'nombre_producto', 'cantidad', 'numero_lote', 'numero_serie']
        widgets = {
            'codigo_producto': forms.TextInput(attrs={'class': 'form-control extra-producto'}),
            'nombre_producto': forms.TextInput(attrs={'class': 'form-control extra-producto'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control extra-producto', 'min': '0'}),
            'numero_lote': forms.TextInput(attrs={'class': 'form-control extra-producto'}),
            'numero_serie': forms.TextInput(attrs={'class': 'form-control extra-producto'}),
        }

# Agrega un pequeño formset para productos si quieres cargarlos en el mismo template al editar/crear.
