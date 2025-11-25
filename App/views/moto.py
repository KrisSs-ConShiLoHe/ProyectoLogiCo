"""
Vistas CRUD para Motos
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.core.paginator import Paginator
from ..models import Moto
from ..forms import MotoForm, MantenimientoMotoForm
from ..decorators import SupervisorOAdminMixin, LoginRequiredMixin
import django_filters
from django_filters.views import FilterView


# ============================================
# VISTAS BASADAS EN CLASES
# ============================================

class ListarMotosView(LoginRequiredMixin, ListView):
    """
    Lista de Motos - acceso a todos, pero solo Admin/Supervisor pueden editar.
    """
    model = Moto
    template_name = 'moto/moto_list.html'
    context_object_name = 'motos'
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['puede_editar'] = self.request.user.rol in ['ADMINISTRADOR', 'SUPERVISOR']
        return context


class CrearMotoView(SupervisorOAdminMixin, CreateView):
    """
    Crear Moto - solo Supervisor o Administrador.
    """
    model = Moto
    form_class = MotoForm
    template_name = 'moto/moto_form.html'
    success_url = reverse_lazy('moto_listar')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['mantenimiento_form'] = MantenimientoMotoForm(self.request.POST)
        else:
            context['mantenimiento_form'] = MantenimientoMotoForm()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        mantenimiento_form = context['mantenimiento_form']

        # Guardar la moto primero
        self.object = form.save()
        
        # 1. Verificar el estado de la moto recién creada
        estado = self.object.estado

        if estado == 'EN_MANTENIMIENTO':
            # 2. Si es 'EN_MANTENIMIENTO', validar el formulario de mantenimiento
            if not mantenimiento_form.is_valid():
                # Si el mantenimiento no es válido, regresamos el formulario de la Moto como inválido
                # para que se muestren los errores de ambos formularios
                self.object.delete() # Opcional: Eliminar la moto si ya se guardó
                messages.error(self.request, 'Error al crear la moto. Faltan datos de mantenimiento.')
                return self.render_to_response(self.get_context_data(form=form, mantenimiento_form=mantenimiento_form))

            # 3. Si es válido, guardamos el mantenimiento
            mantenimiento = mantenimiento_form.save(commit=False)
            mantenimiento.moto = self.object
            mantenimiento.save()

            # 4. Éxito
            messages.success(self.request, 'Moto creada exitosamente.')
            return redirect(self.get_success_url())


    def form_invalid(self, form):
        messages.error(self.request, 'Error al crear la moto.')
        return super().form_invalid(form)


class ModificarMotoView(SupervisorOAdminMixin, UpdateView):
    """
    Modificar Moto - solo Supervisor o Administrador.
    """
    model = Moto
    form_class = MotoForm
    template_name = 'moto/moto_form.html'
    success_url = reverse_lazy('moto_listar')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['mantenimiento_form'] = MantenimientoMotoForm(self.request.POST, instance=self.object.mantenimientos.first())
        else:
            context['mantenimiento_form'] = MantenimientoMotoForm(instance=self.object.mantenimientos.first())
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        mantenimiento_form = context['mantenimiento_form']

        self.object = form.save() # Guardamos la instancia de Moto
        estado = self.object.estado

        # 1. Caso: El estado es EN_MANTENIMIENTO
        if estado == 'EN_MANTENIMIENTO':
            if not mantenimiento_form.is_valid():
                # Si el formulario de mantenimiento falla, devolvemos error
                messages.error(self.request, 'Error al modificar la moto. Faltan datos de mantenimiento.')
                return self.render_to_response(self.get_context_data(form=form, mantenimiento_form=mantenimiento_form))

            mantenimiento = mantenimiento_form.save(commit=False)
            mantenimiento.moto = self.object
            mantenimiento.save()

        # 2. Caso: El estado NO es EN_MANTENIMIENTO
        elif self.object.mantenimientos.exists():
            # Si la moto ya no está en mantenimiento, pero tenía un registro previo, 
            # puedes opcionalmente eliminar el registro (o simplemente dejarlo como historial).
            # Por ahora, simplemente lo ignoramos. Si se quiere borrar, sería aquí.
            pass
            
        messages.success(self.request, 'Moto modificada exitosamente.')
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        messages.error(self.request, 'Error al modificar la moto.')
        return super().form_invalid(form)


class EliminarMotoView(SupervisorOAdminMixin, DeleteView):
    """
    Eliminar Moto - solo Supervisor o Administrador.
    """
    model = Moto
    template_name = 'moto/moto_confirm_delete.html'
    success_url = reverse_lazy('moto_listar')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Moto eliminada exitosamente.')
        return super().delete(request, *args, **kwargs)
    

class MotoDetailView(LoginRequiredMixin, DetailView):
    model = Moto
    template_name = 'moto/moto_detail.html'
    context_object_name = 'moto'


class MotoFilter(django_filters.FilterSet):
    identificador_unico = django_filters.CharFilter(lookup_expr='icontains')
    patente = django_filters.CharFilter(lookup_expr='icontains')
    estado = django_filters.ChoiceFilter(choices=Moto.ESTADOS_VEHICULO)
    modelo = django_filters.CharFilter(lookup_expr='icontains')
    marca = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Moto
        fields = ['identificador_unico', 'patente', 'estado', 'modelo', 'marca']


# ============================================
# VISTAS BASADAS EN FUNCIONES
# ============================================

def listar_motos(request):
    """
    Listar todas las motos con paginación.
    """
    query_id = request.GET.get('identificador_unico')
    query_patente = request.GET.get('patente')
    query_estado = request.GET.get('estado')
    query_modelo = request.GET.get('modelo')
    query_marca = request.GET.get('marca')

    if not request.user.is_authenticated:
        return redirect('login')

    qs = Moto.objects.all()
    if query_id: qs = qs.filter(identificador_unico__icontains=query_id)
    if query_patente: qs = qs.filter(patente__icontains=query_patente)
    if query_estado: qs = qs.filter(estado__icontains=query_estado)
    if query_modelo: qs = qs.filter(modelo__icontains=query_modelo)
    if query_marca: qs = qs.filter(marca__icontains=query_marca)

    paginator = Paginator(qs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'motos': page_obj,
        'puede_editar': request.user.rol in ['ADMINISTRADOR', 'SUPERVISOR']
    }
    return render(request, 'moto/moto_list.html', context)


def crear_moto(request):
    """
    Crear una nueva moto junto con mantenimiento.
    """
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.user.rol not in ['ADMINISTRADOR', 'SUPERVISOR']:
        messages.error(request, 'No tienes permiso para crear motos.')
        return redirect('moto_listar')
    
    if request.method == 'POST':
        form = MotoForm(request.POST, request.FILES)
        mantenimiento_form = MantenimientoMotoForm(request.POST) # Formulario de mantenimiento siempre inicializado
        
        if form.is_valid():
            moto = form.save(commit=False) # No guardar aún, necesitamos verificar el estado
            estado = moto.estado
            
            debe_guardar_mantenimiento = (estado == 'EN_MANTENIMIENTO')
            
            if debe_guardar_mantenimiento and not mantenimiento_form.is_valid():
                # Caso 1: Se eligió 'EN_MANTENIMIENTO', pero faltan datos del formulario secundario.
                messages.error(request, 'Error: Faltan datos de mantenimiento obligatorios.')
                # Caeremos al render final con los errores del formulario de mantenimiento
            else:
                # Caso 2: El formulario principal es válido.
                moto.save() # Guardamos la moto
                
                if debe_guardar_mantenimiento:
                    # Caso 2a: Guardamos el mantenimiento si es necesario
                    mantenimiento = mantenimiento_form.save(commit=False)
                    mantenimiento.moto = moto
                    mantenimiento.save()
                    
                messages.success(request, 'Moto creada exitosamente.')
                return redirect('moto_listar')
        else:
            # Si el MotoForm no es válido
            messages.error(request, 'Error al crear la moto. Revise los campos principales.')

    # Inicialización para GET o si la validación falla
    else:
        form = MotoForm()
        mantenimiento_form = MantenimientoMotoForm()
    
    return render(request, 'moto/moto_form.html', {
        'form': form,
        'mantenimiento_form': mantenimiento_form,
        'titulo': 'Crear Moto'
    })


def editar_moto(request, pk):
    """
    Editar una moto existente junto con mantenimiento.
    """
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.user.rol not in ['ADMINISTRADOR', 'SUPERVISOR']:
        messages.error(request, 'No tienes permiso para editar motos.')
        return redirect('moto_listar')
    
    moto = get_object_or_404(Moto, pk=pk)
    mantenimiento_instance = moto.mantenimientos.first()
    
    if request.method == 'POST':
        form = MotoForm(request.POST, request.FILES, instance=moto)
        mantenimiento_form = MantenimientoMotoForm(request.POST, instance=mantenimiento_instance)
        
        if form.is_valid():
            moto = form.save()  # Guardamos la moto primero
            estado = moto.estado
            
            debe_guardar_mantenimiento = (estado == 'EN_MANTENIMIENTO')
            
            if debe_guardar_mantenimiento:
                # Si el estado es MANTENIMIENTO, el formulario secundario DEBE ser válido
                if not mantenimiento_form.is_valid():
                    messages.error(request, 'Error al modificar la moto. Faltan datos de mantenimiento obligatorios.')
                    # Renderizamos con los formularios para mostrar los errores
                    return render(request, 'moto/moto_form.html', {
                        'form': form,
                        'mantenimiento_form': mantenimiento_form,
                        'titulo': 'Editar Moto',
                        'moto': moto
                    })

                # Si es válido, guardar/actualizar el mantenimiento
                mantenimiento = mantenimiento_form.save(commit=False)
                mantenimiento.moto = moto
                mantenimiento.save()
            
            # Opcional: Si el estado cambia a NO MANTENIMIENTO, puedes borrar el registro anterior.
            # else:
            #     if mantenimiento_instance:
            #         mantenimiento_instance.delete()
                    
            messages.success(request, 'Moto modificada exitosamente.')
            return redirect('moto_listar')
        
        else:
            # Si el MotoForm no es válido
            messages.error(request, 'Error al modificar la moto. Revise los campos principales.')
            
    # Inicialización para GET o si la validación falla
    else:
        form = MotoForm(instance=moto)
        mantenimiento_form = MantenimientoMotoForm(instance=mantenimiento_instance)
    
    return render(request, 'moto/moto_form.html', {
        'form': form,
        'mantenimiento_form': mantenimiento_form,
        'titulo': 'Editar Moto',
        'moto': moto
    })


def eliminar_moto(request, pk):
    """
    Eliminar una moto.
    """
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.user.rol not in ['ADMINISTRADOR', 'SUPERVISOR']:
        messages.error(request, 'No tienes permiso para eliminar motos.')
        return redirect('moto_listar')
    
    moto = get_object_or_404(Moto, pk=pk)
    
    if request.method == 'POST':
        moto.delete()
        messages.success(request, 'Moto eliminada exitosamente.')
        return redirect('moto_listar')
    
    return render(request, 'moto/moto_confirm_delete.html', {'moto': moto})
