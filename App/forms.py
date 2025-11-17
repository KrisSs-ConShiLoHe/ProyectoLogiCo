from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Farmacia, Moto, Motorista, AsignarMotorista


class RegistroForm(UserCreationForm):
    """Formulario personalizado para registro de usuarios"""
    email = forms.EmailField(
        label='Correo Electrónico',
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@ejemplo.com'})
    )
    first_name = forms.CharField(
        label='Nombre',
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tu nombre'})
    )
    last_name = forms.CharField(
        label='Apellido',
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tu apellido'})
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Personalizar widgets
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Nombre de usuario'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Contraseña'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirmar contraseña'
        })
        
        # Personalizar etiquetas
        self.fields['username'].label = 'Usuario'
        self.fields['password1'].label = 'Contraseña'
        self.fields['password2'].label = 'Confirmar Contraseña'

    def clean_email(self):
        """Validar que el email sea único"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('Este correo electrónico ya está registrado.')
        return email

    def clean_username(self):
        """Validar que el usuario sea único"""
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError('Este nombre de usuario ya existe.')
        return username

    def clean(self):
        """Validaciones adicionales"""
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise ValidationError('Las contraseñas no coinciden.')
        
        return cleaned_data


class FarmaciaForm(forms.ModelForm):
    class Meta:
        model = Farmacia
        fields = ['nombre', 'direccion', 'telefono', 'email', 'horarioapertura', 'horariocierre', 'activa', 'latitud', 'longitud']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de la farmacia'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dirección'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@ejemplo.com'}),
            'horarioapertura': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'horariocierre': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'activa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'latitud': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0000001', 'placeholder': '-33.8688197'}),
            'longitud': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0000001', 'placeholder': '-151.2093280'}),
        }
        labels = {
            'nombre': 'Nombre',
            'direccion': 'Dirección',
            'telefono': 'Teléfono',
            'email': 'Correo Electrónico',
            'horarioapertura': 'Horario de Apertura',
            'horariocierre': 'Horario de Cierre',
            'activa': '¿Activa?',
            'latitud': 'Latitud',
            'longitud': 'Longitud',
        }

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre', '').strip()
        if not nombre:
            raise ValidationError('El nombre de la farmacia es requerido.')
        return nombre

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip()
        if email and '@' not in email:
            raise ValidationError('Ingresa un correo electrónico válido.')
        return email


class MotoristaForm(forms.ModelForm):
    class Meta:
        model = Motorista
        fields = [
            'dni',
            'pasaporte',
            'nombre',
            'apellidopaterno',
            'apellidomaterno',
            'fechanacimiento',
            'telefono',
            'email',
            'direccion',
            'licenciaconducir',
            'licenciaarchivo',
            'fechaultimocontrol',
            'fechaproximocontrol',
            'fechacontratacion',
            'activo',
            'idfarmacia'
        ]
        widgets = {
            'dni': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '12.345.678-9'}),
            'pasaporte': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Pasaporte'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre'}),
            'apellidopaterno': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellido Paterno'}),
            'apellidomaterno': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellido Materno'}),
            'fechanacimiento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+56912345678'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@ejemplo.com'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dirección completa'}),
            'licenciaconducir': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número de licencia'}),
            'licenciaarchivo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ruta del archivo'}),
            'fechaultimocontrol': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'fechaproximocontrol': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'fechacontratacion': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'idfarmacia': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'dni': 'RUT o DNI',
            'pasaporte': 'Pasaporte',
            'nombre': 'Nombre',
            'apellidopaterno': 'Apellido Paterno',
            'apellidomaterno': 'Apellido Materno',
            'fechanacimiento': 'Fecha de Nacimiento',
            'telefono': 'Teléfono',
            'email': 'Correo Electrónico',
            'direccion': 'Dirección',
            'licenciaconducir': 'Número de Licencia',
            'licenciaarchivo': 'Archivo de Licencia',
            'fechaultimocontrol': 'Último Control',
            'fechaproximocontrol': 'Próximo Control',
            'fechacontratacion': 'Fecha de Contratación',
            'activo': '¿Activo?',
            'idfarmacia': 'Farmacia Asignada',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['pasaporte'].required = False
        self.fields['dni'].required = False
        self.fields['licenciaarchivo'].required = False
        self.fields['direccion'].required = False
        self.fields['fechanacimiento'].required = False
        self.fields['fechaultimocontrol'].required = False
        self.fields['fechaproximocontrol'].required = False

    def clean_dni(self):
        dni = self.cleaned_data.get('dni', '').strip()
        return dni

    def clean_pasaporte(self):
        pasaporte = self.cleaned_data.get('pasaporte', '').strip()
        return pasaporte

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre', '').strip()
        if not nombre:
            raise ValidationError('El nombre es requerido.')
        return nombre

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip()
        if email and '@' not in email:
            raise ValidationError('Ingresa un correo electrónico válido.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        dni = cleaned_data.get('dni', '').strip()
        pasaporte = cleaned_data.get('pasaporte', '').strip()
        
        if not dni and not pasaporte:
            raise ValidationError('Debe ingresar al menos RUT o Pasaporte.')
        
        return cleaned_data


class MotoForm(forms.ModelForm):
    class Meta:
        model = Moto
        fields = ['patente', 'marca', 'modelo', 'color', 'anio', 'numerochasis', 'numeromotor', 
                  'aniodocumentacion', 'aniopermisocirculacion', 'seguroobligatorio', 'revisiontecnica', 
                  'propietario', 'disponible', 'activa', 'idmotorista']
        widgets = {
            'patente': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'XXXX-XX'}),
            'marca': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Honda'}),
            'modelo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Wave'}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Rojo'}),
            'anio': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '2023'}),
            'numerochasis': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número de chasis'}),
            'numeromotor': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número de motor'}),
            'aniodocumentacion': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '2023'}),
            'aniopermisocirculacion': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '2023'}),
            'seguroobligatorio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'revisiontecnica': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'propietario': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'RUT'}),
            'disponible': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'activa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'idmotorista': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'patente': 'Patente',
            'marca': 'Marca',
            'modelo': 'Modelo',
            'color': 'Color',
            'anio': 'Año de Fabricación',
            'numerochasis': 'Número de Chasis',
            'numeromotor': 'Número de Motor',
            'aniodocumentacion': 'Año Documentación',
            'aniopermisocirculacion': 'Año Permiso de Circulación',
            'seguroobligatorio': 'Seguro Obligatorio',
            'revisiontecnica': 'Revisión Técnica',
            'propietario': 'Propietario',
            'disponible': '¿Disponible?',
            'activa': '¿Activa?',
            'idmotorista': 'Motorista Asignado',
        }

    def clean_patente(self):
        patente = self.cleaned_data.get('patente', '').strip().upper()
        if not patente:
            raise ValidationError('La patente es requerida.')
        return patente

    def clean_marca(self):
        marca = self.cleaned_data.get('marca', '').strip()
        if not marca:
            raise ValidationError('La marca es requerida.')
        return marca


class AsignarMotoristaForm(forms.ModelForm):
    """
    Formulario para crear y editar asignaciones de motorista a moto
    """
    
    class Meta:
        model = AsignarMotorista
        fields = [
            'idmotorista',
            'idmoto',
            'fechaasignacion',
            'fechadesasignacion',
            'activa',
            'observaciones'
        ]
        widgets = {
            'idmotorista': forms.Select(attrs={'class': 'form-control'}),
            'idmoto': forms.Select(attrs={'class': 'form-control'}),
            'fechaasignacion': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'class': 'form-control'
                },
                format='%Y-%m-%dT%H:%M'
            ),
            'fechadesasignacion': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'class': 'form-control'
                },
                format='%Y-%m-%dT%H:%M'
            ),
            'activa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Notas adicionales sobre la asignación'
            }),
        }
        labels = {
            'idmotorista': 'Motorista',
            'idmoto': 'Moto',
            'fechaasignacion': 'Fecha de Asignación',
            'fechadesasignacion': 'Fecha de Desasignación',
            'activa': '¿Asignación Activa?',
            'observaciones': 'Observaciones'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['idmotorista'].required = True
        self.fields['idmoto'].required = True
        self.fields['fechaasignacion'].required = True
        self.fields['fechadesasignacion'].required = False
        self.fields['observaciones'].required = False

    def clean_idmotorista(self):
        motorista = self.cleaned_data.get('idmotorista')
        if not motorista:
            raise ValidationError('Debes seleccionar un motorista.')
        return motorista

    def clean_idmoto(self):
        moto = self.cleaned_data.get('idmoto')
        if not moto:
            raise ValidationError('Debes seleccionar una moto.')
        return moto

    def clean_observaciones(self):
        observaciones = self.cleaned_data.get('observaciones', '').strip()
        return observaciones

    def clean(self):
        cleaned_data = super().clean()
        fechaasignacion = cleaned_data.get('fechaasignacion')
        fechadesasignacion = cleaned_data.get('fechadesasignacion')
        
        if fechaasignacion and fechadesasignacion and fechadesasignacion < fechaasignacion:
            raise ValidationError('La fecha de desasignación no puede ser anterior a la fecha de asignación.')
        
        return cleaned_data