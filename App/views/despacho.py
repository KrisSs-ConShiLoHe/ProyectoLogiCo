"""
Vistas para Gestión de Despachos/Movimientos
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, View
from django.urls import reverse_lazy
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Q
from ..models import Despacho, Motorista
from ..forms import DespachoForm, DespachoEstadoForm
from ..decorators import RolRequiredMixin, LoginRequiredMixin


# ============================================
# VISTAS BASADAS EN CLASES
# ============================================

class ListarDespachosView(LoginRequiredMixin, ListView):
    """
    Lista de Despachos con filtros por estado, tipo, fechas, farmacia, motorista.
    Acceso según rol.
    """
    model = Despacho
    template_name = 'despacho/despacho_list.html'
    context_object_name = 'despachos'
    paginate_by = 30

    def get_queryset(self):
        queryset = Despacho.objects.all()
        
        # Filtros
        estado = self.request.GET.get('estado')
        tipo = self.request.GET.get('tipo')
        farmacia = self.request.GET.get('farmacia')
        motorista = self.request.GET.get('motorista')
        fecha_desde = self.request.GET.get('fecha_desde')
        fecha_hasta = self.request.GET.get('fecha_hasta')
        
        if estado:
            queryset = queryset.filter(estado=estado)
        if tipo:
            queryset = queryset.filter(tipo_movimiento=tipo)
        if farmacia:
            queryset = queryset.filter(farmacia_origen_id=farmacia)
        if motorista:
            queryset = queryset.filter(motorista_asignado_id=motorista)
        if fecha_desde:
            queryset = queryset.filter(fecha_hora_creacion__gte=fecha_desde)
        if fecha_hasta:
            queryset = queryset.filter(fecha_hora_creacion__lte=fecha_hasta)
        
        # Si es motorista, solo ve sus despachos
        if self.request.user.rol == 'MOTORISTA':
            try:
                motorista_obj = Motorista.objects.get(usuario=self.request.user)
                queryset = queryset.filter(motorista_asignado=motorista_obj)
            except Motorista.DoesNotExist:
                queryset = queryset.none()
        
        return queryset.order_by('-fecha_hora_creacion')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['estados'] = Despacho.ESTADOS
        context['tipos'] = Despacho.MOVIMIENTOS
        context['puede_crear'] = self.request.user.rol in ['OPERADOR', 'SUPERVISOR', 'ADMINISTRADOR', 'GERENTE']
        context['puede_cambiar_estado'] = self.request.user.rol in ['MOTORISTA', 'SUPERVISOR', 'ADMINISTRADOR', 'GERENTE']
        return context


class CrearDespachoView(RolRequiredMixin, CreateView):
    """
    Crear Despacho - roles: Operador, Supervisor, Admin, Gerente.
    Tipo predefinido según shortcut.
    """
    model = Despacho
    form_class = DespachoForm
    template_name = 'despacho/despacho_form.html'
    success_url = reverse_lazy('despacho_listar')
    roles_permitidos = ['OPERADOR', 'SUPERVISOR', 'ADMINISTRADOR', 'GERENTE']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Despacho'
        return context

    def form_valid(self, form):
        despacho = form.save(commit=False)
        despacho.estado = 'PENDIENTE'
        despacho.save()
        messages.success(self.request, 'Despacho creado exitosamente.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Error al crear el despacho.')
        return super().form_invalid(form)


class ModificarDespachoView(RolRequiredMixin, UpdateView):
    """
    Modificar Despacho - solo si está PENDIENTE.
    Roles: Supervisor, Admin, Gerente.
    """
    model = Despacho
    form_class = DespachoForm
    template_name = 'despacho/despacho_form.html'
    success_url = reverse_lazy('despacho_listar')
    roles_permitidos = ['SUPERVISOR', 'ADMINISTRADOR', 'GERENTE']

    def dispatch(self, request, *args, **kwargs):
        despacho = self.get_object()
        if despacho.estado != 'PENDIENTE':
            messages.error(request, 'Solo puedes editar despachos en estado PENDIENTE.')
            return redirect('despacho_listar')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar Despacho'
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Despacho modificado exitosamente.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Error al modificar el despacho.')
        return super().form_invalid(form)


class AnularDespachoView(RolRequiredMixin, View):
    """
    Anular Despacho - solo si está PENDIENTE o EN_RUTA.
    Roles: Supervisor, Admin, Gerente.
    """
    roles_permitidos = ['SUPERVISOR', 'ADMINISTRADOR', 'GERENTE']

    def dispatch(self, request, *args, **kwargs):
        despacho = get_object_or_404(Despacho, pk=kwargs['pk'])
        if despacho.estado not in ['PENDIENTE', 'EN_RUTA']:
            messages.error(request, 'Solo puedes anular despachos en estado PENDIENTE o EN_RUTA.')
            return redirect('despacho_listar')
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, pk):
        despacho = get_object_or_404(Despacho, pk=pk)
        despacho.estado = 'ANULADO'
        despacho.save()
        messages.success(request, 'Despacho anulado exitosamente.')
        return redirect('despacho_listar')


class CambiarEstadoDespachoView(RolRequiredMixin, View):
    """
    Cambiar estado de Despacho.
    Roles: Motorista, Supervisor, Admin, Gerente.
    """
    roles_permitidos = ['MOTORISTA', 'SUPERVISOR', 'ADMINISTRADOR', 'GERENTE']

    def post(self, request, pk):
        despacho = get_object_or_404(Despacho, pk=pk)
        nuevo_estado = request.POST.get('estado')
        
        # Validar transiciones válidas
        transiciones_validas = {
            'PENDIENTE': ['EN_RUTA', 'ANULADO'],
            'EN_RUTA': ['ENTREGADO', 'INCIDENCIA', 'ANULADO'],
            'ENTREGADO': [],
            'ANULADO': [],
            'INCIDENCIA': ['EN_RUTA', 'ENTREGADO'],
        }
        
        if nuevo_estado not in transiciones_validas.get(despacho.estado, []):
            messages.error(request, 'Transición de estado no válida.')
            return redirect('despacho_listar')
        
        # Actualizar fechas según el estado
        if nuevo_estado == 'EN_RUTA' and not despacho.fecha_hora_despacho:
            despacho.fecha_hora_despacho = timezone.now()
        elif nuevo_estado == 'ENTREGADO' and not despacho.fecha_hora_entrega:
            despacho.fecha_hora_entrega = timezone.now()
        
        despacho.estado = nuevo_estado
        despacho.save()
        
        messages.success(request, f'Estado del despacho actualizado a {nuevo_estado}.')
        return redirect('despacho_listar')


# ============================================
# VISTAS BASADAS EN FUNCIONES
# ============================================

def listar_despachos(request):
    """
    Listar despachos con filtros.
    """
    if not request.user.is_authenticated:
        return redirect('login')
    
    queryset = Despacho.objects.all()
    
    # Filtros
    estado = request.GET.get('estado')
    tipo = request.GET.get('tipo')
    farmacia = request.GET.get('farmacia')
    motorista = request.GET.get('motorista')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    if estado:
        queryset = queryset.filter(estado=estado)
    if tipo:
        queryset = queryset.filter(tipo_movimiento=tipo)
    if farmacia:
        queryset = queryset.filter(farmacia_origen_id=farmacia)
    if motorista:
        queryset = queryset.filter(motorista_asignado_id=motorista)
    if fecha_desde:
        queryset = queryset.filter(fecha_hora_creacion__gte=fecha_desde)
    if fecha_hasta:
        queryset = queryset.filter(fecha_hora_creacion__lte=fecha_hasta)
    
    # Si es motorista, solo ve sus despachos
    if request.user.rol == 'MOTORISTA':
        try:
            motorista_obj = Motorista.objects.get(usuario=request.user)
            queryset = queryset.filter(motorista_asignado=motorista_obj)
        except Motorista.DoesNotExist:
            queryset = queryset.none()
    
    paginator = Paginator(queryset, 30)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'despachos': page_obj,
        'estados': Despacho.ESTADOS,
        'tipos': Despacho.MOVIMIENTOS,
        'puede_crear': request.user.rol in ['OPERADOR', 'SUPERVISOR', 'ADMINISTRADOR', 'GERENTE'],
        'puede_cambiar_estado': request.user.rol in ['MOTORISTA', 'SUPERVISOR', 'ADMINISTRADOR', 'GERENTE']
    }
    return render(request, 'despacho/despacho_list.html', context)


def crear_despacho(request):
    """
    Crear un nuevo despacho.
    """
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.user.rol not in ['OPERADOR', 'SUPERVISOR', 'ADMINISTRADOR', 'GERENTE']:
        messages.error(request, 'No tienes permiso para crear despachos.')
        return redirect('despacho_listar')
    
    if request.method == 'POST':
        form = DespachoForm(request.POST)
        if form.is_valid():
            despacho = form.save(commit=False)
            despacho.estado = 'PENDIENTE'
            despacho.save()
            messages.success(request, 'Despacho creado exitosamente.')
            return redirect('despacho_listar')
        else:
            messages.error(request, 'Error al crear el despacho.')
    else:
        form = DespachoForm()
    
    return render(request, 'despacho/despacho_form.html', {
        'form': form,
        'titulo': 'Crear Despacho'
    })


def editar_despacho(request, pk):
    """
    Editar un despacho existente (solo si está PENDIENTE).
    """
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.user.rol not in ['SUPERVISOR', 'ADMINISTRADOR', 'GERENTE']:
        messages.error(request, 'No tienes permiso para editar despachos.')
        return redirect('despacho_listar')
    
    despacho = get_object_or_404(Despacho, pk=pk)
    
    if despacho.estado != 'PENDIENTE':
        messages.error(request, 'Solo puedes editar despachos en estado PENDIENTE.')
        return redirect('despacho_listar')
    
    if request.method == 'POST':
        form = DespachoForm(request.POST, instance=despacho)
        if form.is_valid():
            form.save()
            messages.success(request, 'Despacho modificado exitosamente.')
            return redirect('despacho_listar')
        else:
            messages.error(request, 'Error al modificar el despacho.')
    else:
        form = DespachoForm(instance=despacho)
    
    return render(request, 'despacho/despacho_form.html', {
        'form': form,
        'titulo': 'Editar Despacho',
        'despacho': despacho
    })


def anular_despacho(request, pk):
    """
    Anular un despacho (solo si está PENDIENTE o EN_RUTA).
    """
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.user.rol not in ['SUPERVISOR', 'ADMINISTRADOR', 'GERENTE']:
        messages.error(request, 'No tienes permiso para anular despachos.')
        return redirect('despacho_listar')
    
    despacho = get_object_or_404(Despacho, pk=pk)
    
    if despacho.estado not in ['PENDIENTE', 'EN_RUTA']:
        messages.error(request, 'Solo puedes anular despachos en estado PENDIENTE o EN_RUTA.')
        return redirect('despacho_listar')
    
    if request.method == 'POST':
        despacho.estado = 'ANULADO'
        despacho.save()
        messages.success(request, 'Despacho anulado exitosamente.')
        return redirect('despacho_listar')
    
    return render(request, 'despacho/despacho_confirm_delete.html', {'despacho': despacho})


def cambiar_estado_despacho(request, pk):
    """
    Cambiar el estado de un despacho.
    """
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.user.rol not in ['MOTORISTA', 'SUPERVISOR', 'ADMINISTRADOR', 'GERENTE']:
        messages.error(request, 'No tienes permiso para cambiar estados de despachos.')
        return redirect('despacho_listar')
    
    despacho = get_object_or_404(Despacho, pk=pk)
    nuevo_estado = request.POST.get('estado')
    
    # Validar transiciones válidas
    transiciones_validas = {
        'PENDIENTE': ['EN_RUTA', 'ANULADO'],
        'EN_RUTA': ['ENTREGADO', 'INCIDENCIA', 'ANULADO'],
        'ENTREGADO': [],
        'ANULADO': [],
        'INCIDENCIA': ['EN_RUTA', 'ENTREGADO'],
    }
    
    if nuevo_estado not in transiciones_validas.get(despacho.estado, []):
        messages.error(request, 'Transición de estado no válida.')
        return redirect('despacho_listar')
    
    # Actualizar fechas según el estado
    if nuevo_estado == 'EN_RUTA' and not despacho.fecha_hora_despacho:
        despacho.fecha_hora_despacho = timezone.now()
    elif nuevo_estado == 'ENTREGADO' and not despacho.fecha_hora_entrega:
        despacho.fecha_hora_entrega = timezone.now()
    
    despacho.estado = nuevo_estado
    despacho.save()
    
    messages.success(request, f'Estado del despacho actualizado a {nuevo_estado}.')
    return redirect('despacho_listar')
