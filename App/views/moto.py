"""
Vistas CRUD para Motos
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.core.paginator import Paginator
from ..models import Moto, DocumentacionMoto, PermisoCirculacion
from ..forms import MotoForm, MantenimientoMotoForm, DocumentacionMotoForm, PermisoCirculacionForm, PermisoCirculacionFormSet
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

        # AÑADIR DocumentacionMotoForm
        if self.request.POST:
            context['documentacion_form'] = DocumentacionMotoForm(self.request.POST, self.request.FILES)
        else:
            context['documentacion_form'] = DocumentacionMotoForm()

        # 💡 NUEVO: Inicializar Formset de Permiso de Circulación vacío
        if self.request.POST:
            context['permiso_formset'] = PermisoCirculacionFormSet(self.request.POST)
        else:
            context['permiso_formset'] = PermisoCirculacionFormSet()

        return context


    def form_valid(self, form):
        context = self.get_context_data()
        # ... (Recuperar documentacion_form y mantenimiento_form) ...
        permiso_formset = context['permiso_formset'] # 💡 NUEVO
        mantenimiento_form = context['mantenimiento_form']
        documentacion_form = context['documentacion_form']

        if not documentacion_form.is_valid():
            messages.error(self.request, 'Error al crear la moto. Faltan datos de documentación.')
            # Retornar para mostrar errores
            return self.render_to_response(self.get_context_data(form=form))

        # VALIDAR FORMSET DE PERMISOS
        if permiso_formset.is_valid():
            
            self.object = form.save() # Guardar la Moto

        # 2. Guardar Documentación (Relación One-to-One)
        documentacion = documentacion_form.save(commit=False)
        documentacion.moto = self.object # Enlazar la documentación a la moto
        documentacion.save()

        # 💡 NUEVO: Guardar los permisos (Formset)
        permisos = permiso_formset.save(commit=False)
        for permiso in permisos:
            permiso.moto = self.object # Asignar la FK a la Moto recién creada
            permiso.save()
        
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

        # Recuperar o crear instancia de DocumentacionMoto
        doc_instance, created = DocumentacionMoto.objects.get_or_create(moto=self.object)

        if self.request.POST:
            context['mantenimiento_form'] = MantenimientoMotoForm(self.request.POST, instance=self.object.mantenimientos.first())
            context['documentacion_form'] = DocumentacionMotoForm(self.request.POST, self.request.FILES, instance=doc_instance)
        else:
            if self.object.estado == 'EN_MANTENIMIENTO':
                context['mantenimiento_form'] = MantenimientoMotoForm(instance=self.object.mantenimientos.first())
            context['documentacion_form'] = DocumentacionMotoForm(instance=doc_instance)

    # 💡 NUEVO: Inicializar Formset de Permiso de Circulación con la instancia
        if self.request.POST:
            context['permiso_formset'] = PermisoCirculacionFormSet(self.request.POST, instance=self.object)
        else:
            context['permiso_formset'] = PermisoCirculacionFormSet(instance=self.object) # Pasar la instancia de Moto

        return context

    def form_valid(self, form):
        context = self.get_context_data()
        # ... (Recuperar forms) ...
        permiso_formset = context['permiso_formset'] # 💡 NUEVO
        mantenimiento_form = context['mantenimiento_form']
        documentacion_form = context['documentacion_form']

        # 1. VALIDAR DOCUMENTACIÓN
        if not documentacion_form.is_valid():
            messages.error(self.request, 'Error al modificar la moto. Faltan datos de documentación.')
            return self.render_to_response(self.get_context_data(form=form)) 

        # VALIDAR FORMSET DE PERMISOS
        if permiso_formset.is_valid():
            
            self.object = form.save() # Guardar la Moto
        
        # 3. Guardar o actualizar Documentación
        documentacion = documentacion_form.save(commit=False)
        documentacion.moto = self.object
        documentacion.save()

        # 💡 NUEVO: Guardar y eliminar permisos (maneja los cambios, creaciones y eliminaciones)
        permiso_formset.instance = self.object # Asegurarse de que la instancia esté vinculada
        permiso_formset.save()
        
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
        else:
            # Si la moto ya no está en mantenimiento, eliminar cualquier registro de mantenimiento existente
            self.object.mantenimientos.all().delete()
            
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
        'motos': page_obj,
        'is_paginated': paginator.num_pages > 1,  # ← Añadir esto
        'puede_editar': request.user.rol in ['ADMINISTRADOR', 'SUPERVISOR']
    }
    return render(request, 'moto/moto_list.html', context)


def crear_moto(request):
    """
    Crear una nueva moto junto con mantenimiento y asignación opcional a motorista.
    """
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.user.rol not in ['ADMINISTRADOR', 'SUPERVISOR']:
        messages.error(request, 'No tienes permiso para crear motos.')
        return redirect('moto_listar')
    
    if request.method == 'POST':
        form = MotoForm(request.POST, request.FILES)
        mantenimiento_form = MantenimientoMotoForm(request.POST)
        documentacion_form = DocumentacionMotoForm(request.POST, request.FILES)
        permiso_formset = PermisoCirculacionFormSet(request.POST)
        
        if form.is_valid() and documentacion_form.is_valid() and permiso_formset.is_valid():
            moto = form.save(commit=False)
            duenio = moto.duenio
            motorista_asignado = form.cleaned_data.get('motorista_asignado')
            estado = moto.estado
            
            # Validar mantenimiento si el estado lo requiere
            if estado == 'EN_MANTENIMIENTO':
                if not mantenimiento_form.is_valid():
                    messages.error(request, 'Error: Faltan datos de mantenimiento obligatorios.')
                    return render(request, 'moto/moto_form.html', {
                        'form': form,
                        'mantenimiento_form': mantenimiento_form,
                        'documentacion_form': documentacion_form,
                        'permiso_formset': permiso_formset,
                        'titulo': 'Crear Moto'
                    })
            
            # Guardar la moto
            moto.save()
            
            # Guardar documentación
            documentacion = documentacion_form.save(commit=False)
            documentacion.moto = moto
            documentacion.save()
            
            # Guardar permisos
            permisos = permiso_formset.save(commit=False)
            for permiso in permisos:
                permiso.moto = moto
                permiso.save()
            
            # Guardar mantenimiento si corresponde
            if estado == 'EN_MANTENIMIENTO':
                mantenimiento = mantenimiento_form.save(commit=False)
                mantenimiento.moto = moto
                mantenimiento.save()
            
            messages.success(request, 'Moto creada exitosamente.')
            return redirect('moto_listar')
        else:
            messages.error(request, 'Error al crear la moto. Revise los campos.')
    else:
        form = MotoForm()
        mantenimiento_form = MantenimientoMotoForm()
        documentacion_form = DocumentacionMotoForm()
        permiso_formset = PermisoCirculacionFormSet()
    
    return render(request, 'moto/moto_form.html', {
        'form': form,
        'mantenimiento_form': mantenimiento_form,
        'documentacion_form': documentacion_form,
        'permiso_formset': permiso_formset,
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
    documentacion_instance, created = DocumentacionMoto.objects.get_or_create(moto=moto)
    
    if request.method == 'POST':
        form = MotoForm(request.POST, request.FILES, instance=moto)
        mantenimiento_form = MantenimientoMotoForm(request.POST, instance=mantenimiento_instance)
        documentacion_form = DocumentacionMotoForm(request.POST, request.FILES, instance=documentacion_instance)
        permiso_formset = PermisoCirculacionFormSet(request.POST, instance=moto)
        
        if form.is_valid() and documentacion_form.is_valid() and permiso_formset.is_valid():
            moto = form.save()
            estado = moto.estado
            
            # Guardar documentación
            documentacion = documentacion_form.save(commit=False)
            documentacion.moto = moto
            documentacion.save()
            
            # Guardar permisos
            permiso_formset.save()
            
            # Manejar mantenimiento
            if estado == 'EN_MANTENIMIENTO':
                if not mantenimiento_form.is_valid():
                    messages.error(request, 'Error: Faltan datos de mantenimiento obligatorios.')
                    return render(request, 'moto/moto_form.html', {
                        'form': form,
                        'mantenimiento_form': mantenimiento_form,
                        'documentacion_form': documentacion_form,
                        'permiso_formset': permiso_formset,
                        'titulo': 'Editar Moto',
                        'moto': moto
                    })
                
                mantenimiento = mantenimiento_form.save(commit=False)
                mantenimiento.moto = moto
                mantenimiento.save()
            else:
                # Si no está en mantenimiento, eliminar registros
                moto.mantenimientos.all().delete()
            
            messages.success(request, 'Moto modificada exitosamente.')
            return redirect('moto_listar')
        else:
            messages.error(request, 'Error al modificar la moto. Revise los campos.')
    else:
        form = MotoForm(instance=moto)
        mantenimiento_form = MantenimientoMotoForm(instance=mantenimiento_instance)
        documentacion_form = DocumentacionMotoForm(instance=documentacion_instance)
        permiso_formset = PermisoCirculacionFormSet(instance=moto)
    
    return render(request, 'moto/moto_form.html', {
        'form': form,
        'mantenimiento_form': mantenimiento_form,
        'documentacion_form': documentacion_form,
        'permiso_formset': permiso_formset,
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
