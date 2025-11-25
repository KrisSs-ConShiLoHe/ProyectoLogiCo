"""
Vistas para Gestión de Despachos/Movimientos
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, View, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Q
from ..models import Despacho, Motorista, Farmacia, AsignacionFarmacia
from ..forms import DespachoForm, DespachoEstadoForm
from ..forms import ProductoPedido, ProductoPedidoForm
from ..decorators import RolRequiredMixin, LoginRequiredMixin
import django_filters
from django_filters.views import FilterView
from django.http import JsonResponse
import logging



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
        if self.request.POST:
            context['producto_form'] = ProductoPedidoForm(self.request.POST)
        else:
            context['producto_form'] = ProductoPedidoForm()
        return context
        # context['titulo'] = 'Crear Despacho'
        # return context

    def form_valid(self, form):
        context = self.get_context_data()
        producto_form = context['producto_form']

        # Guardar la moto primero
        self.object = form.save()
        
        # 1. Verificar el estado de la moto recién creada
        tipo_movimiento = self.object.tipo_movimiento

        if tipo_movimiento == 'DIRECTO':
            # 2. Si es 'EN_MANTENIMIENTO', validar el formulario de mantenimiento
            if not producto_form.is_valid():
                self.object.delete() # Opcional: Eliminar la moto si ya se guardó
                messages.error(self.request, 'Error al crear la moto. Faltan datos de mantenimiento.')
                return self.render_to_response(self.get_context_data(form=form, producto_form=producto_form))

            # 3. Si es válido, guardamos el mantenimiento
            producto = producto_form.save(commit=False)
            producto.despacho = self.object
            producto.save()

            # 4. Éxito
            messages.success(self.request, 'Despacho creada exitosamente.')
            return redirect(self.get_success_url())

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
        if self.request.POST:
            context['producto_form'] = ProductoPedidoForm(self.request.POST, instance=self.object.productos.first())
        else:
            context['producto_form'] = ProductoPedidoForm(instance=self.object.productos.first())
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        producto_form = context['producto_form']

        self.object = form.save() # Guardamos la instancia de Moto
        tipo_movimiento = self.object.tipo_movimiento

        # 1. Caso: El estado es EN_MANTENIMIENTO
        if tipo_movimiento == 'DIRECTO':
            if not producto_form.is_valid():
                # Si el formulario de mantenimiento falla, devolvemos error
                messages.error(self.request, 'Error al modificar el despacho. Faltan datos del producto.')
                return self.render_to_response(self.get_context_data(form=form, producto_form=producto_form))

            producto = producto_form.save(commit=False)
            producto.despacho = self.object
            producto.save()

        # 2. Caso: El estado NO es EN_MANTENIMIENTO
        elif self.object.productos.exists():
            # Si la moto ya no está en mantenimiento, pero tenía un registro previo, 
            # puedes opcionalmente eliminar el registro (o simplemente dejarlo como historial).
            # Por ahora, simplemente lo ignoramos. Si se quiere borrar, sería aquí.
            pass
            
        messages.success(self.request, 'Despacho modificada exitosamente.')
        return redirect(self.get_success_url())

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
    roles_permitidos = ['OPERADOR', 'SUPERVISOR', 'ADMINISTRADOR', 'GERENTE']

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


class DespachoDetailView(LoginRequiredMixin, DetailView):
    model = Despacho
    template_name = 'despacho/despacho_detail.html'
    context_object_name = 'despacho'
    

class DespachoFilter(django_filters.FilterSet):
    identificador_unico = django_filters.CharFilter(lookup_expr='icontains')
    farmacia_origen = django_filters.ModelChoiceFilter(queryset=Farmacia.objects.all())
    motorista_asignado = django_filters.ModelChoiceFilter(queryset=Motorista.objects.all())
    estado = django_filters.ChoiceFilter(choices=Despacho.ESTADOS)

class Meta:
    model = Despacho
    fields = ['identificador_unico', 'farmacia_origen', 'motorista_asignado', 'estado']


# ============================================
# VISTAS BASADAS EN FUNCIONES
# ============================================

def listar_despachos(request):
    """
    Listar despachos con filtros.
    """
    if not request.user.is_authenticated:
        return redirect("login")

    qs = Despacho.objects.select_related(
        "farmacia_origen", "motorista_asignado"
    ).all()

    # --- OBTENER FILTROS ---
    identificador_unico = request.GET.get("identificador_unico")
    id_farmacia = request.GET.get("id_farmacia")
    farmacia = request.GET.get("farmacia")
    id_motorista = request.GET.get("id_motorista")
    motorista = request.GET.get("motorista")
    estado = request.GET.get("estado")
    tipo_movimiento = request.GET.get("tipo_movimiento")
    fecha_desde = request.GET.get("fecha_desde")
    fecha_hasta = request.GET.get("fecha_hasta")

    # --- FILTROS ---

    # ID del despacho
    if identificador_unico:
        qs = qs.filter(identificador_unico__icontains=identificador_unico)

    if id_farmacia:
        qs = qs.filter(farmacia_origen_identificador_unico__icontains=identificador_unico)

    # Farmacia (nombre o ID único)
    if farmacia:
        qs = qs.filter(
            Q(farmacia_origen__nombre__icontains=farmacia)
        )

    if id_motorista:
        qs = qs.filter(motorista_asignado__identificador_unico__icontains=id_motorista)

    # Motorista (nombre, apellido, usuario, ID único)
    if motorista:
        qs = qs.filter(
            Q(motorista_asignado__usuario__first_name__icontains=motorista) |
            Q(motorista_asignado__usuario__last_name__icontains=motorista) |
            Q(motorista_asignado__usuario__username__icontains=motorista)
        )

    # Estado
    if estado:
        qs = qs.filter(estado=estado)

    # Tipo de movimiento
    if tipo_movimiento:
        qs = qs.filter(tipo_movimiento=tipo_movimiento)

    # Rango de fechas
    if fecha_desde:
        qs = qs.filter(fecha_hora_creacion__date__gte=fecha_desde)

    if fecha_hasta:
        qs = qs.filter(fecha_hora_creacion__date__lte=fecha_hasta)

    # --- PAGINACIÓN ---
    paginator = Paginator(qs.order_by("-fecha_hora_creacion"), 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Permisos
    puede_crear = request.user.rol in ["ADMINISTRADOR", "SUPERVISOR", "OPERADOR"]
    puede_cambiar_estado = request.user.rol in ["ADMINISTRADOR", "SUPERVISOR"]

    return render(request, "despacho/despacho_list.html", {
        "page_obj": page_obj,
        "is_paginated": page_obj.has_other_pages(),
        "puede_crear": puede_crear,
        "puede_cambiar_estado": puede_cambiar_estado,
    })


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
        form = DespachoForm(request.POST, request.FILES)
        producto_form = ProductoPedidoForm(request.POST)  # Inicializar siempre
        
        if form.is_valid():
            despacho = form.save(commit=False)
            tipo_movimiento = despacho.tipo_movimiento
            
            debe_guardar_producto = (tipo_movimiento == 'DIRECTO')
            
            if debe_guardar_producto and not producto_form.is_valid():
                messages.error(request, 'Error: Faltan datos de producto obligatorios.')
            else:
                despacho.save()
                
                if debe_guardar_producto:
                    producto = producto_form.save(commit=False)
                    producto.despacho = despacho
                    producto.save()
                
                messages.success(request, 'Despacho creado exitosamente.')
                return redirect('despacho_listar')
        else:
            messages.error(request, 'Error al crear el despacho.')
    else:
        form = DespachoForm()
        producto_form = ProductoPedidoForm()
    
    return render(request, 'despacho/despacho_form.html', {
        'form': form,
        'producto_form': producto_form,  # Pasar producto_form al template
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
    producto_instance = despacho.productos.first()  # Asumiendo uno por despacho
    
    if request.method == 'POST':
        form = DespachoForm(request.POST, request.FILES, instance=despacho)
        producto_form = ProductoPedidoForm(request.POST, instance=producto_instance)
        
        if form.is_valid():
            despacho = form.save(commit=False)
            tipo_movimiento = despacho.tipo_movimiento
            
            debe_guardar_producto = (tipo_movimiento == 'DIRECTO')
            
            if debe_guardar_producto and not producto_form.is_valid():
                messages.error(request, 'Error al modificar el producto. Faltan datos de producto obligatorios.')
            else:
                despacho.save()
                
                if debe_guardar_producto:
                    producto = producto_form.save(commit=False)
                    producto.despacho = despacho
                    producto.save()
                elif producto_instance:
                    # Si cambió a otro tipo y había producto, opcionalmente bórralo
                    producto_instance.delete()
                
                messages.success(request, 'Despacho modificado exitosamente.')
                return redirect('despacho_listar')
        else:
            messages.error(request, 'Error al modificar el despacho.')
    else:
        form = DespachoForm(instance=despacho)
        producto_form = ProductoPedidoForm(instance=producto_instance)
    
    return render(request, 'despacho/despacho_form.html', {
        'form': form,
        'producto_form': producto_form,  # Pasar producto_form al template
        'titulo': 'Editar Despacho',
        'despacho': despacho
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
    producto_instance = despacho.productos.first()
    
    if request.method == 'POST':
        form = DespachoForm(request.POST, request.FILES, instance=despacho)
        producto_form = ProductoPedidoForm(request.POST, instance=producto_instance)
        
        if form.is_valid():
            despacho = form.save()  # Guardamos la moto primero
            tipo_movimiento = despacho.tipo_movimiento
            
            debe_guardar_producto = (tipo_movimiento == 'DIRECTO')
            
            if debe_guardar_producto:
                # Si el estado es MANTENIMIENTO, el formulario secundario DEBE ser válido
                if not producto_form.is_valid():
                    messages.error(request, 'Error al modificar el producto. Faltan datos de producto obligatorios.')
                    # Renderizamos con los formularios para mostrar los errores
                    return render(request, 'despacho/despacho_form.html', {
                        'form': form,
                        'producto_form': producto_form,
                        'titulo': 'Editar Despacho',
                        'despacho': despacho
                    })

                # Si es válido, guardar/actualizar el mantenimiento
                producto = producto_form.save(commit=False)
                producto.despacho = despacho
                producto.save()
            
            # Opcional: Si el estado cambia a NO MANTENIMIENTO, puedes borrar el registro anterior.
            # else:
            #     if mantenimiento_instance:
            #         mantenimiento_instance.delete()
                    
            messages.success(request, 'Despacho modificada exitosamente.')
            return redirect('despacho_listar')
        
        else:
            # Si el MotoForm no es válido
            messages.error(request, 'Error al modificar el despacho. Revise los campos principales.')
            
    # Inicialización para GET o si la validación falla
    else:
        form = DespachoForm(instance=despacho)
        producto_form = ProductoPedidoForm(instance=producto_instance)
    
    return render(request, 'despacho/despacho_form.html', {
        'form': form,
        'producto_form': producto_form,
        'titulo': 'Editar Despacho',
        'despacho': despacho
    })
    
    # if despacho.estado != 'PENDIENTE':
    #     messages.error(request, 'Solo puedes editar despachos en estado PENDIENTE.')
    #     return redirect('despacho_listar')
    
    # if request.method == 'POST':
    #     form = DespachoForm(request.POST, request.FILES, instance=despacho)
    #     if form.is_valid():
    #         form.save()
    #         messages.success(request, 'Despacho modificado exitosamente.')
    #         return redirect('despacho_listar')
    #     else:
    #         messages.error(request, 'Error al modificar el despacho.')
    # else:
    #     form = DespachoForm(instance=despacho)
    
    # return render(request, 'despacho/despacho_form.html', {
    #     'form': form,
    #     'titulo': 'Editar Despacho',
    #     'despacho': despacho
    # })


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


logger = logging.getLogger(__name__)
def motoristas_por_farmacia(request):
    """
    Vista AJAX para obtener motoristas asignados a una farmacia específica.
    """
    logger.info(f"Request method: {request.method}, headers: {request.headers}")
    if request.method == 'GET' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        farmacia_id = request.GET.get('farmacia_id')
        logger.info(f"Farmacia ID: {farmacia_id}")
        if farmacia_id:
            try:
                asignaciones = AsignacionFarmacia.objects.filter(farmacia_id=farmacia_id, activa=True)
                logger.info(f"Asignaciones encontradas: {asignaciones.count()}")
                motoristas_ids = asignaciones.values_list('motorista_id', flat=True)
                logger.info(f"Motoristas IDs: {list(motoristas_ids)}")
                motoristas = Motorista.objects.filter(id__in=motoristas_ids).values('id', 'usuario__first_name', 'usuario__last_name', 'rut')
                logger.info(f"Motoristas data: {list(motoristas)}")
                data = [{'id': m['id'], 'text': f"{m['usuario__first_name']} {m['usuario__last_name']} - RUT: {m['rut']}"} for m in motoristas]
                return JsonResponse({'motoristas': data})
            except Exception as e:
                logger.error(f"Error en vista: {e}")
                return JsonResponse({'error': str(e)}, status=500)
        return JsonResponse({'error': 'Farmacia ID requerido'}, status=400)
    return JsonResponse({'error': 'Método no permitido'}, status=405)