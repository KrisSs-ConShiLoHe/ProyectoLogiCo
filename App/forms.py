"""
Formularios para las vistas
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm as DjangoUserCreationForm
from .models import Farmacia, Motorista, Moto, AsignacionMoto, AsignacionFarmacia, Despacho, User


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
    """
    Formulario para crear/editar Farmacias.
    """
    class Meta:
        model = Farmacia
        fields = ['nombre', 'direccion', 'region', 'comuna', 'codigo_externo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de la farmacia'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dirección'}),
            'region': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Región'}),
            'comuna': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Comuna'}),
            'codigo_externo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Código externo'}),
        }


class MotoristaForm(forms.ModelForm):
    """
    Formulario para crear/editar Motoristas.
    """
    class Meta:
        model = Motorista
        fields = ['usuario', 'rut', 'licencia_vigente']
        widgets = {
            'usuario': forms.Select(attrs={'class': 'form-control'}),
            'rut': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'RUT (formato: 12345678-K)'}),
            'licencia_vigente': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class MotoForm(forms.ModelForm):
    """
    Formulario para crear/editar Motos.
    """
    class Meta:
        model = Moto
        fields = ['patente', 'marca', 'modelo', 'disponible']
        widgets = {
            'patente': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Patente (ej: ABCD-12)'}),
            'marca': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Marca'}),
            'modelo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Modelo'}),
            'disponible': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


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
        motos_disponibles = kwargs.pop('motos_disponibles', None)
        super().__init__(*args, **kwargs)
        
        if motos_disponibles:
            self.fields['moto'].queryset = motos_disponibles


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


class DespachoForm(forms.ModelForm):
    """
    Formulario para crear/editar Despachos.
    """
    class Meta:
        model = Despacho
        fields = [
            'id_pedido_externo',
            'tipo_movimiento',
            'farmacia_origen',
            'motorista_asignado',
            'requiere_receta'
        ]
        widgets = {
            'id_pedido_externo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ID Pedido'}),
            'tipo_movimiento': forms.Select(attrs={'class': 'form-control'}),
            'farmacia_origen': forms.Select(attrs={'class': 'form-control'}),
            'motorista_asignado': forms.Select(attrs={'class': 'form-control'}),
            'requiere_receta': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
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
