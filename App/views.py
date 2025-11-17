from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Farmacia, Motorista, Moto, AsignarMotorista
from .forms import RegistroForm, FarmaciaForm, MotoristaForm, MotoForm, AsignarMotoristaForm
from .auth_decorators import permiso_requerido, rol_requerido
from .roles import obtener_rol_usuario


# ===== AUTENTICACIÓN =====
def home(request):
    """Vista de home/dashboard"""
    if request.user.is_authenticated:
        context = {
            'total_farmacias': Farmacia.objects.filter(activa=1).count(),
            'total_motoristas': Motorista.objects.filter(activo=1).count(),
            'total_motos': Moto.objects.filter(activa=1).count(),
            'asignaciones_activas': AsignarMotorista.objects.filter(activa=1).count(),
        }
        return render(request, 'home.html', context)
    return redirect('admin:login')


def registro(request):
    """Registrar nuevo usuario"""
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            messages.success(request, f'Usuario "{usuario.username}" creado exitosamente. Ya puedes iniciar sesión.')
            return redirect('admin:login')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = RegistroForm()
    
    return render(request, 'registro.html', {'form': form})


@login_required(login_url='admin:login')
def perfil(request):
    """Ver perfil de usuario (solo lectura)"""
    rol = obtener_rol_usuario(request.user)
    return render(request, 'perfil.html', {'user': request.user, 'rol': rol})

@login_required(login_url='admin:login')
def editar_perfil(request):
    """Editar perfil de usuario"""
    if request.method == 'POST':
        user = request.user
        user.email = request.POST.get('email', user.email).strip()
        user.first_name = request.POST.get('first_name', user.first_name).strip()
        user.last_name = request.POST.get('last_name', user.last_name).strip()
        user.save()
        messages.success(request, 'Perfil actualizado exitosamente.')
        return redirect('perfil')
    
    rol = obtener_rol_usuario(request.user)
    
    return render(request, 'editar_perfil.html', {'user': request.user, 'rol': rol})

# ===== FARMACIA =====
@permiso_requerido('farmacias', 'view')
def listado_farmacias(request):
    """Lista todas las farmacias con búsqueda y paginación"""
    search_query = request.GET.get('search', '').strip()
    rol = obtener_rol_usuario(request.user)
    
    farmacias = Farmacia.objects.all()
    
    # Si es farmacia, solo muestra su propia farmacia
    if rol == 'farmacia':
        farmacia_usuario = request.user.groups.first()
        if farmacia_usuario:
            farmacias = farmacias.filter(nombre__icontains=farmacia_usuario.name)
    
    if search_query:
        farmacias = farmacias.filter(
            Q(nombre__icontains=search_query) |
            Q(direccion__icontains=search_query) |
            Q(telefono__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    farmacias = farmacias.order_by('nombre')
    
    paginator = Paginator(farmacias, 10)
    page_number = request.GET.get('page')
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
    }
    
    return render(request, 'listado_farmacias.html', context)


@permiso_requerido('farmacias', 'add')
def agregar_farmacia(request):
    """Crea una nueva farmacia"""
    if request.method == 'POST':
        form = FarmaciaForm(request.POST)
        if form.is_valid():
            farmacia = form.save()
            messages.success(request, f'Farmacia "{farmacia.nombre}" creada exitosamente.')
            return redirect('detalle_farmacia', pk=farmacia.idfarmacia)
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = FarmaciaForm()
    
    return render(request, 'farmacia_form.html', {'form': form})


@permiso_requerido('farmacias', 'change')
def actualizar_farmacia(request, pk):
    """Actualiza datos de una farmacia existente"""
    farmacia = get_object_or_404(Farmacia, idfarmacia=pk)
    
    if request.method == 'POST':
        form = FarmaciaForm(request.POST, instance=farmacia)
        if form.is_valid():
            form.save()
            messages.success(request, 'Farmacia actualizada exitosamente.')
            return redirect('detalle_farmacia', pk=farmacia.idfarmacia)
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = FarmaciaForm(instance=farmacia)
    
    return render(request, 'actualizar_farmacia.html', {'form': form, 'farmacia': farmacia})


@permiso_requerido('farmacias', 'delete')
def remover_farmacia(request, pk):
    """Elimina una farmacia"""
    farmacia = get_object_or_404(Farmacia, idfarmacia=pk)
    
    if request.method == 'POST':
        nombre_farmacia = farmacia.nombre
        try:
            farmacia.delete()
            messages.success(request, f'Farmacia "{nombre_farmacia}" eliminada exitosamente.')
        except Exception as e:
            messages.error(request, f'Error al eliminar: {str(e)}')
        return redirect('listado_farmacia')
    
    return render(request, 'remover_farmacia.html', {'farmacia': farmacia})


@permiso_requerido('farmacias', 'view')
def detalle_farmacia(request, pk):
    """Ver detalles de una farmacia"""
    rol = obtener_rol_usuario(request.user)
    
    farmacia = get_object_or_404(Farmacia, idfarmacia=pk)
    
    # Si es farmacia, solo puede ver su propia farmacia
    if rol == 'farmacia':
        farmacia_usuario = Farmacia.objects.filter(nombre__icontains=request.user.groups.first().name).first() if request.user.groups.exists() else None
        if not farmacia_usuario or farmacia != farmacia_usuario:
            messages.error(request, 'No puedes ver otras farmacias.')
            return redirect('listado_farmacia')
    
    motoristas = Motorista.objects.filter(idfarmacia=farmacia, activo=1)
    
    context = {
        'farmacia': farmacia,
        'motoristas': motoristas,
    }
    
    return render(request, 'detalle_farmacia.html', context)


# ===== MOTORISTA =====
@permiso_requerido('motoristas', 'view')
def listado_motoristas(request):
    """Lista todos los motoristas con búsqueda y paginación"""
    search_query = request.GET.get('search', '').strip()
    rol = obtener_rol_usuario(request.user)
    
    motoristas = Motorista.objects.select_related('idfarmacia')
    
    # Si es motorista, solo ve su perfil
    if rol == 'motorista':
        messages.info(request, 'Solo puedes ver tu perfil.')
        return redirect('detalle_motorista', pk=request.user.id)
    
    # Si es farmacia, solo ve motoristas de su farmacia
    if rol == 'farmacia':
        # Buscar farmacia del usuario
        farmacia = Farmacia.objects.filter(nombre__icontains=request.user.groups.first().name).first()
        if farmacia:
            motoristas = motoristas.filter(idfarmacia=farmacia)
    
    if search_query:
        motoristas = motoristas.filter(
            Q(nombre__icontains=search_query) |
            Q(apellidopaterno__icontains=search_query) |
            Q(apellidomaterno__icontains=search_query) |
            Q(dni__icontains=search_query) |
            Q(telefono__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    motoristas = motoristas.order_by('nombre')
    
    paginator = Paginator(motoristas, 10)
    page_number = request.GET.get('page')
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
    }
    
    return render(request, 'listado_motoristas.html', context)


@permiso_requerido('motoristas', 'add')
def agregar_motorista(request):
    """Crea un nuevo motorista"""
    if request.method == 'POST':
        form = MotoristaForm(request.POST)
        if form.is_valid():
            motorista = form.save()
            messages.success(request, f'Motorista "{motorista.nombre}" creado exitosamente.')
            return redirect('detalle_motorista', pk=motorista.idmotorista)
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = MotoristaForm()
    
    return render(request, 'agregar_motorista.html', {'form': form})


@permiso_requerido('motoristas', 'change')
def actualizar_motorista(request, pk):
    """Actualiza datos de un motorista existente"""
    motorista = get_object_or_404(Motorista, idmotorista=pk)
    
    if request.method == 'POST':
        form = MotoristaForm(request.POST, instance=motorista)
        if form.is_valid():
            form.save()
            messages.success(request, 'Motorista actualizado exitosamente.')
            return redirect('detalle_motorista', pk=motorista.idmotorista)
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = MotoristaForm(instance=motorista)
    
    return render(request, 'actualizar_motorista.html', {'form': form, 'motorista': motorista})


@permiso_requerido('motoristas', 'delete')
def remover_motorista(request, pk):
    """Elimina un motorista"""
    motorista = get_object_or_404(Motorista, idmotorista=pk)
    
    if request.method == 'POST':
        nombre_motorista = f"{motorista.nombre} {motorista.apellidopaterno}"
        try:
            motorista.delete()
            messages.success(request, f'Motorista "{nombre_motorista}" eliminado exitosamente.')
        except Exception as e:
            messages.error(request, f'Error al eliminar: {str(e)}')
        return redirect('listado_motoristas')
    
    return render(request, 'remover_motorista.html', {'motorista': motorista})


@login_required(login_url='admin:login')
def detalle_motorista(request, pk):
    """Ver detalles de un motorista"""
    rol = obtener_rol_usuario(request.user)
    
    # Si es motorista, solo puede ver su propio perfil
    if rol == 'motorista' and request.user.id != pk:
        messages.error(request, 'No puedes ver el perfil de otro motorista.')
        return redirect('home')
    
    motorista = get_object_or_404(Motorista, idmotorista=pk)
    asignaciones = AsignarMotorista.objects.filter(idmotorista=motorista).select_related('idmoto')
    asignaciones_activas = asignaciones.filter(activa=1)
    
    context = {
        'motorista': motorista,
        'asignaciones': asignaciones,
        'asignaciones_activas': asignaciones_activas,
    }
    
    return render(request, 'detalle_motorista.html', context)


# ===== MOTO =====
@permiso_requerido('motos', 'view')
def listado_motos(request):
    """Lista todas las motos con búsqueda y paginación"""
    search_query = request.GET.get('search', '').strip()
    rol = obtener_rol_usuario(request.user)
    
    motos = Moto.objects.select_related('idmotorista')
    
    # Si es motorista, solo ve su moto asignada
    if rol == 'motorista':
        motorista = Motorista.objects.filter(idmotorista=request.user.id).first()
        if motorista:
            motos = motos.filter(idmotorista=motorista)
    
    if search_query:
        motos = motos.filter(
            Q(patente__icontains=search_query) |
            Q(marca__icontains=search_query) |
            Q(modelo__icontains=search_query) |
            Q(numerochasis__icontains=search_query) |
            Q(propietario__icontains=search_query)
        )
    
    motos = motos.order_by('patente')
    
    paginator = Paginator(motos, 10)
    page_number = request.GET.get('page')
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
    }
    
    return render(request, 'listado_motos.html', context)


@permiso_requerido('motos', 'add')
def agregar_moto(request):
    """Crea una nueva moto"""
    if request.method == 'POST':
        form = MotoForm(request.POST)
        if form.is_valid():
            moto = form.save()
            messages.success(request, f'Moto "{moto.patente}" creada exitosamente.')
            return redirect('detalle_moto', pk=moto.idmoto)
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = MotoForm()
    
    return render(request, 'agregar_moto.html', {'form': form})


@permiso_requerido('motos', 'change')
def actualizar_moto(request, pk):
    """Actualiza datos de una moto existente"""
    moto = get_object_or_404(Moto, idmoto=pk)
    
    if request.method == 'POST':
        form = MotoForm(request.POST, instance=moto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Moto actualizada exitosamente.')
            return redirect('detalle_moto', pk=moto.idmoto)
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = MotoForm(instance=moto)
    
    return render(request, 'actualizar_moto.html', {'form': form, 'moto': moto})


@permiso_requerido('motos', 'delete')
def remover_moto(request, pk):
    """Elimina una moto"""
    moto = get_object_or_404(Moto, idmoto=pk)
    
    if request.method == 'POST':
        patente = moto.patente
        try:
            moto.delete()
            messages.success(request, f'Moto "{patente}" eliminada exitosamente.')
        except Exception as e:
            messages.error(request, f'Error al eliminar: {str(e)}')
        return redirect('listado_moto')
    
    return render(request, 'remover_moto.html', {'moto': moto})


@permiso_requerido('motos', 'view')
def detalle_moto(request, pk):
    """Ver detalles de una moto"""
    rol = obtener_rol_usuario(request.user)
    
    moto = get_object_or_404(Moto, idmoto=pk)
    
    # Si es motorista, solo puede ver su moto asignada
    if rol == 'motorista':
        try:
            motorista_usuario = Motorista.objects.get(idmotorista=request.user.id)
            if moto.idmotorista != motorista_usuario:
                messages.error(request, 'No puedes ver motos que no te están asignadas.')
                return redirect('listado_moto')
        except Motorista.DoesNotExist:
            messages.error(request, 'No tienes un perfil de motorista asociado.')
            return redirect('home')
    
    # Si es farmacia, solo puede ver motos de su farmacia
    if rol == 'farmacia':
        if moto.idmotorista and moto.idmotorista.idfarmacia:
            farmacia_usuario = Farmacia.objects.filter(nombre__icontains=request.user.groups.first().name).first() if request.user.groups.exists() else None
            if not farmacia_usuario or moto.idmotorista.idfarmacia != farmacia_usuario:
                messages.error(request, 'No puedes ver motos de otras farmacias.')
                return redirect('listado_moto')
    
    asignaciones = AsignarMotorista.objects.filter(idmoto=moto).select_related('idmotorista')
    
    context = {
        'moto': moto,
        'asignaciones': asignaciones,
    }
    
    return render(request, 'detalle_moto.html', context)


# ===== ASIGNACIONES =====
@permiso_requerido('asignaciones', 'view')
def listado_asignaciones(request):
    """Lista todas las asignaciones de motoristas con búsqueda y paginación"""
    search_query = request.GET.get('search', '').strip()
    filtro_estado = request.GET.get('estado', '')
    rol = obtener_rol_usuario(request.user)
    
    asignaciones = AsignarMotorista.objects.all().select_related('idmotorista', 'idmoto')
    
    # Si es motorista, solo ve sus asignaciones
    if rol == 'motorista':
        motorista = Motorista.objects.filter(idmotorista=request.user.id).first()
        if motorista:
            asignaciones = asignaciones.filter(idmotorista=motorista)
    
    if search_query:
        asignaciones = asignaciones.filter(
            Q(idmotorista__nombre__icontains=search_query) |
            Q(idmotorista__apellidopaterno__icontains=search_query) |
            Q(idmoto__patente__icontains=search_query) |
            Q(observaciones__icontains=search_query)
        )
    
    if filtro_estado == 'activa':
        asignaciones = asignaciones.filter(activa=1)
    elif filtro_estado == 'inactiva':
        asignaciones = asignaciones.filter(activa=0)
    
    asignaciones = asignaciones.order_by('-fechaasignacion')
    
    paginator = Paginator(asignaciones, 10)
    page_number = request.GET.get('page')
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'filtro_estado': filtro_estado,
    }
    
    return render(request, 'listado_asignaciones.html', context)


@permiso_requerido('asignaciones', 'view')
def detalle_asignacion(request, pk):
    """Ver detalles de una asignación"""
    rol = obtener_rol_usuario(request.user)
    
    asignacion = get_object_or_404(AsignarMotorista, idasignacion=pk)
    
    # Si es motorista, solo puede ver sus propias asignaciones
    if rol == 'motorista':
        try:
            motorista_usuario = Motorista.objects.get(idmotorista=request.user.id)
            if asignacion.idmotorista != motorista_usuario:
                messages.error(request, 'No puedes ver asignaciones de otros motoristas.')
                return redirect('listado_asignaciones')
        except Motorista.DoesNotExist:
            messages.error(request, 'No tienes un perfil de motorista asociado.')
            return redirect('home')
    
    # Si es farmacia, solo puede ver asignaciones de su farmacia
    if rol == 'farmacia':
        farmacia_usuario = Farmacia.objects.filter(nombre__icontains=request.user.groups.first().name).first() if request.user.groups.exists() else None
        if not farmacia_usuario or asignacion.idmotorista.idfarmacia != farmacia_usuario:
            messages.error(request, 'No puedes ver asignaciones de otras farmacias.')
            return redirect('listado_asignaciones')
    
    context = {
        'asignacion': asignacion,
    }
    
    return render(request, 'asignaciones/detalle_asignacion.html', context)


@permiso_requerido('asignaciones', 'add')
def agregar_asignacion(request):
    """Crea una nueva asignación de motorista a moto"""
    if request.method == 'POST':
        form = AsignarMotoristaForm(request.POST)
        if form.is_valid():
            asignacion = form.save()
            messages.success(request, 'Asignación creada exitosamente.')
            return redirect('detalle_asignacion', pk=asignacion.idasignacion)
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = AsignarMotoristaForm()
    
    context = {
        'form': form,
        'titulo': 'Nueva Asignación',
        'boton_texto': 'Crear Asignación'
    }
    
    return render(request, 'agregar_asignacion.html', context)

def modificar_asignacion(request, pk):
    """Edita una asignación existente"""
    asignacion = get_object_or_404(AsignarMotorista, idasignacion=pk)
    
    if request.method == 'POST':
        form = AsignarMotoristaForm(request.POST, instance=asignacion)
        if form.is_valid():
            form.save()
            messages.success(request, 'Asignación actualizada exitosamente.')
            return redirect('detalle_asignacion', pk=asignacion.idasignacion)
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = AsignarMotoristaForm(instance=asignacion)
    
    context = {
        'form': form,
        'asignacion': asignacion,
        'titulo': 'Modificar Asignación',
        'boton_texto': 'Guardar Cambios'
    }
    
    return render(request, 'modificar_asignacion.html', context)


def remover_asignacion(request, pk):
    """Activa o desactiva una asignación"""
    asignacion = get_object_or_404(AsignarMotorista, idasignacion=pk)
    
    if request.method == 'POST':
        try:
            asignacion.activa = 1 if asignacion.activa == 0 else 0
            asignacion.save()
            
            estado = "activada" if asignacion.activa == 1 else "desactivada"
            messages.success(request, f'Asignación {estado} exitosamente.')
        except Exception as e:
            messages.error(request, f'Error al actualizar: {str(e)}')
        return redirect('detalle_asignacion', pk=asignacion.idasignacion)
    
    return render(request, 'remover_asignacion.html', {'asignacion': asignacion})