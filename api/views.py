import base64
import json
from django.shortcuts import render
from django.shortcuts import HttpResponse
from django.contrib import messages
from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import  AuthenticationForm
from django.contrib.auth import login, logout
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import render, redirect
from api import models, forms
from django.urls import reverse
from django.db import IntegrityError, transaction, connection
from django.db.models import Q, Min, F, IntegerField
from decimal import Decimal
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.shortcuts import render, get_object_or_404, redirect
from django.core.mail import send_mail
import threading
import serial
import serial.tools.list_ports
from serial.tools import list_ports
from django.db.models.functions import Cast
import random
from collections import defaultdict
import string
from django.shortcuts import render
from .decorators import (
    is_administrador,
    is_supervisor,
    is_quimico_a,
    is_quimico_b,
    is_quimico_c,
    is_cliente,
    is_administrador_or_supervisor,
    is_all_quimicos,
    is_full_acceso,
    is_internal_user,
)

from django.views.decorators.csrf import csrf_exempt

from django.contrib.auth.decorators import login_required
from .models import User
from .forms import CustomUserCreationForm


@login_required(login_url='/login')
def requestAcces(request):
    return redirect("/index")


def Sitio_Web(request):
    return render(request, "Inicio.html")


def login_view(request):

    if not settings.ENABLED_LOGIN_LOCAL:
        return HttpResponseRedirect(settings.URL_REACT)

    if request.user.is_authenticated:
        return redirect('/index')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            if request.user.is_authenticated:
                return redirect('/index')
            else:
                return render(request, "login.html", {'form': form, 'error': "Error de autenticación."})
    else:
        form = AuthenticationForm()
    
    return render(request, "login.html", {'form': form})



def logout_View(request):
    try:
        # Cerrar sesión del usuario
        logout(request)
        print("Usuario deslogueado correctamente")

        # Opcional: Limpiar el token si estás manejando la autenticación basada en tokens
        if hasattr(request.user, 'token'):
            request.user.token = None
            request.user.save()
            print("Token eliminado del usuario")
        if settings.ENABLED_LOGIN_LOCAL == False: 
            return HttpResponseRedirect(settings.URL_REACT)
        else:
            return redirect(reverse('login_View'))

    except Exception as e:
        print(f"Error al desloguear usuario: {e}")
        message = f"Error al desloguear usuario: {str(e)}"
        return JsonResponse({'tipo': 'error', 'message': message}, status=500)
    


@login_required(login_url='/login')
def Main(request):
    return render(request, 'index.html')
       
    
@login_required(login_url='/login')
@is_administrador_or_supervisor
def ODT_Module(request):
    search_query = request.GET.get('search', '')
    filter_year = request.GET.get('year', '')
    filter_month = request.GET.get('month', '')

    odts = models.ODT.objects.all()

    # Si el prefijo "WSS" está en la búsqueda, eliminarlo para buscar por el ID
    if search_query.startswith("WSS"):
        search_query = search_query[3:]

    odts = odts.filter(
        Q(id__icontains=search_query) |
        Q(Proyecto__nombre__icontains=search_query) |
        Q(Prefijo__icontains=search_query) |
        Q(Cant_Muestra__icontains=search_query) |
        Q(Prioridad__icontains=search_query) |
        Q(TipoMuestra__icontains=search_query) | 
        Q(Referencia__icontains=search_query) |
        Q(Cliente__nombre_empresa__icontains=search_query) |
        Q(Proyecto__nombre__icontains=search_query) |
        Q(Responsable__icontains=search_query)
    )

    if filter_year:
        odts = odts.filter(Fec_Recep__year=filter_year)

    if filter_month:
        odts = odts.filter(Fec_Recep__month=filter_month)
    
    context = {
        'odts': odts,
        'available_years': list(models.ODT.objects.dates('Fec_Recep', 'year').values_list('Fec_Recep__year', flat=True).distinct()),
        'available_months': [
            {'value': 1, 'label': 'Enero'}, {'value': 2, 'label': 'Febrero'}, {'value': 3, 'label': 'Marzo'},
            {'value': 4, 'label': 'Abril'}, {'value': 5, 'label': 'Mayo'}, {'value': 6, 'label': 'Junio'},
            {'value': 7, 'label': 'Julio'}, {'value': 8, 'label': 'Agosto'}, {'value': 9, 'label': 'Septiembre'},
            {'value': 10, 'label': 'Octubre'}, {'value': 11, 'label': 'Noviembre'}, {'value': 12, 'label': 'Diciembre'}
        ]
    }

    return render(request, 'ODT-Site.html', context)



@login_required(login_url='/login')
@is_internal_user
def HT_Module(request):
    search_query = request.GET.get('search', '')
    estado_filter = request.GET.get('estado', '') 

    hts = (models.HojaTrabajoQuimico.objects
           .values('ID_HDT')
           .annotate(min_id=Min('HojaTrabajo__id'))
           .values('min_id'))
    
    hts = models.HojaTrabajo.objects.filter(id__in=[ht['min_id'] for ht in hts]).annotate(
        ID_HDT=F('hojas_trabajo_target__ID_HDT'),
        confirmar_balanza=F('hojas_trabajo_target__confirmar_balanza')
    )

    if estado_filter == 'Pendiente':
        hts = hts.filter(confirmar_balanza=False)
    elif estado_filter == 'Cerrado':
        hts = hts.filter(confirmar_balanza=True)

    if search_query:
        hts = hts.filter(
            Q(hojas_trabajo_target__ID_HDT__icontains=search_query) |
            Q(odt__id__icontains=search_query) |
            Q(MuestraMasificada__Prefijo__icontains=search_query) |
            Q(MetodoAnalisis__nombre__icontains=search_query)
        )
    data = []
    for ht in hts:
        data.append({
            'id': ht.id,
            'ID_HDT': ht.ID_HDT,
            'estado': 'Cerrado' if ht.confirmar_balanza else 'Pendiente',
            'odt': ht.odt.id,
            'estandar': [estandar.Nombre for estandar in ht.Estandar.all()],
            'metodo_analisis': ht.MetodoAnalisis.nombre,
            'muestra_masificada': ht.MuestraMasificada.Prefijo,
            'tipo': ht.Tipo,
            'duplicado': ht.Duplicado,
        })

    data_json = json.dumps(data)

    context = {
        'hts': hts,
        'hts_json': data_json 
    }

    return render(request, 'Hoja_Trabajo.html', context)

@is_internal_user
def Request_HT(request):
    if request.method == 'GET':
        id_hdt = request.GET.get('id')

        # Filtrar y ordenar hojas de trabajo químico
        hojas_trabajo_quimico = models.HojaTrabajoQuimico.objects.filter(ID_HDT=id_hdt).order_by('ID_HDT')

        data = []
        
        for hoja_quimico in hojas_trabajo_quimico:
            muestra = hoja_quimico.HojaTrabajo
            elementos_data = [
                {
                    'nombre': elemento.nombre,
                    'gramos': elemento.gramos,
                    'miligramos': elemento.miligramos
                }
                for elemento in muestra.MetodoAnalisis.elementos.all()
            ]
            muestras_filtradas = models.Muestra.objects.filter(hoja_trabajo=muestra)

            Data_Peso = 0
            for m in muestras_filtradas:
                Data_Peso = m.peso_m

            
            data.append({
                'id': muestra.id,
                'ID_HDT': hoja_quimico.ID_HDT,
                'estado': 'Cerrado' if hoja_quimico.confirmar_balanza else 'Pendiente',
                'estandar': ', '.join(estandar.Nombre for estandar in muestra.Estandar.all()),
                'metodo_analisis': muestra.MetodoAnalisis.nombre,
                'muestra_masificada': muestra.MuestraMasificada.Prefijo, 
                'tipo': muestra.Tipo,
                'duplicado': muestra.Duplicado,
                'elementos': elementos_data,
                'peso_muestra': Data_Peso
            })
        
        data = sorted(data, key=lambda x: (int(x['muestra_masificada']), x['id']))

        return JsonResponse({'muestras': data})
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)




@is_internal_user  # administrador, supervisor, quimico_A, quimico_B, quimico_C
def Balanza_Module(request):
    if request.method == 'POST':
        id_hdt = request.POST.get('id')
        print(f'ID recibido en Balanza: {id_hdt}')

        hojas_trabajo_quimico = models.HojaTrabajoQuimico.objects.filter(ID_HDT=id_hdt)

        targetHDT_Quimico = hojas_trabajo_quimico.first()

        if not hojas_trabajo_quimico.exists():
            return render(request, 'Balanza.html')


        print("Ingresando a este modulo")

        hojas_trabajo = models.HojaTrabajo.objects.filter(id__in=[htq.HojaTrabajo.id for htq in hojas_trabajo_quimico])

        primera_muestra = models.Muestra.objects.filter(hoja_trabajo__in=hojas_trabajo, indexCurv=1).first()

        if primera_muestra is None:
            return render(request, 'Balanza.html')

        tipo_elemento = primera_muestra.elemento
        muestras_balanza = models.Muestra.objects.filter(
            hoja_trabajo__in=hojas_trabajo,
            elemento=tipo_elemento,
            indexCurv=1
        ).order_by('muestraMasificada__Prefijo')
        context = {'muestras_balanza': muestras_balanza, 'id_hdt': id_hdt, 'stade': targetHDT_Quimico.confirmar_balanza}
        return render(request, 'Balanza.html', context)

    return render(request, 'Balanza.html')
    
@login_required(login_url='/login')
@is_internal_user
def Save_M(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            muestras = data.get('muestras', [])
            ID_HDT = data.get('id')

            for muestra_data in muestras:
                prefijo = muestra_data.get('prefijo')
                peso_m = muestra_data.get('peso_m')
                peso_m = Decimal(str(peso_m).replace(',', '.'))

                muestras = models.Muestra.objects.filter(
                    muestraMasificada__Prefijo=prefijo,
                    hoja_trabajo__hojas_trabajo_target__ID_HDT=ID_HDT  
                )
                for muestra in muestras:
                    muestra.peso_m = peso_m
                    muestra.save()
            models.Novedades.objects.create(
                tipo_model = 'Hoja de trabajo',
                accion="Modificar",
                modelt_id=str(ID_HDT),
                fecha=timezone.now(),
                usuario = request.user
            )
            return JsonResponse({'success': True})

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Error al procesar los datos'}, status=400)

    return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)


@login_required(login_url='/login')
@is_internal_user
def Confirm_M(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            muestras = data.get('muestras', [])
            ID_HDT = data.get('id')
            for muestra_data in muestras:
                prefijo = muestra_data.get('prefijo')
                peso_m = muestra_data.get('peso_m')

                muestras = models.Muestra.objects.filter(
                    muestraMasificada__Prefijo=prefijo,
                    hoja_trabajo__hojas_trabajo_target__ID_HDT=ID_HDT
                )

                peso_m = Decimal(str(peso_m).replace(',', '.'))
                
                for muestra in muestras:
                    muestra.peso_m = peso_m
                    muestra.save()

                    hoja_trabajo_quimico = models.HojaTrabajoQuimico.objects.filter(
                        HojaTrabajo=muestra.hoja_trabajo,
                        ID_HDT=ID_HDT
                    ).first()

                    if hoja_trabajo_quimico:
                        hoja_trabajo_quimico.confirmar_balanza = True
                        hoja_trabajo_quimico.save()

            
            models.Novedades.objects.create(
                tipo_model = 'Hoja de trabajo',
                accion="Balanza",
                modelt_id=str(ID_HDT),
                fecha=timezone.now(),
                usuario = request.user
            )
            return JsonResponse({'success': True})

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Error al procesar los datos'}, status=400)

    return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)
        


@login_required(login_url='/login')
@is_internal_user
def PI_Module(request):
    if request.method == 'POST':
        id_hdt = request.POST.get('id') 
        id_hdt_list = request.POST.get('id_sec', '')  
        id_Batch = request.POST.get('batch')
        
        batch_mode = False  # Inicializar el indicador
        elementos_unicos = []  # Lista para almacenar elementos únicos
        resultados_map = {}  # Mapeo de resultados por muestra y elemento
        
        Creación_Batch = ""
        curvaturas = {}
        if id_Batch:
            batch_mode = True  # Activar si se accede con batch
            Contenedor = models.LotesAbsorción.objects.filter(ID_LT=id_Batch)

            lote = models.LotesAbsorción.objects.filter(ID_LT=id_Batch).first()
            curvaturas= {'curv_1': lote.curv_1 if lote else 0.0,'curv_2': lote.curv_2 if lote else 0.0,'curv_3': lote.curv_3 if lote else 0.0,'curv_4': lote.curv_4 if lote else 0.0}

            if Contenedor.exists():
                id_hdt_final = list(Contenedor.values_list('hoja_trabajo__ID_HDT', flat=True).distinct())
                Resultados_Batch = models.Resultado.objects.filter(lote_absorcion__in=Contenedor)
                
                if Resultados_Batch.exists():
                    Creación_Batch = Resultados_Batch.earliest('fecha_emision').fecha_emision
                else:
                    Creación_Batch = None
                
                # Mapear resultados (muestra + elemento)
                for resultado in Resultados_Batch:
                    resultados_map[(resultado.muestra.id, resultado.elemento.nombre)] = {
                        "resultado_id": resultado.id,
                        "dilucion": resultado.dilucion,
                        "resultadoAnalisis": resultado.resultadoAnalisis,
                        "leyAnalisis": resultado.leyAnalisis,
                    }
                    # Añadir elementos únicos
                    if resultado.elemento.nombre not in elementos_unicos:
                        elementos_unicos.append(resultado.elemento.nombre)
            else:
                id_hdt_final = []  
        else:
            id_hdt_list = id_hdt_list.split('-') if id_hdt_list else []
            id_hdt_set = set(id_hdt_list)
            if id_hdt: 
                id_hdt_set.add(id_hdt)
            id_hdt_final = list(id_hdt_set)

            prefijos_vistos = {}

            for x in list(id_hdt_final): 
                hojas_trabajo_quimico = models.HojaTrabajoQuimico.objects.filter(ID_HDT=x)
                hojas_trabajo = models.HojaTrabajo.objects.filter(id__in=[htq.HojaTrabajo.id for htq in hojas_trabajo_quimico])
                muestras_balanza = models.Muestra.objects.filter(hoja_trabajo__in=hojas_trabajo, indexCurv=1)

                for muestra in muestras_balanza:
                    prefijo = muestra.muestraMasificada.Prefijo if muestra.muestraMasificada else None

                    if prefijo in prefijos_vistos and prefijos_vistos[prefijo] != x:
                        messages.add_message(request=request, level=messages.ERROR, message=f"No se puede agregar hojas de trabajo diferentes con la misma muestra: {prefijo}")

                        id_hdt_final.remove(x)
                        break 

                    if prefijo:
                        prefijos_vistos[prefijo] = x
        
       
        Doc_Muestra = []
        for x in id_hdt_final:
            hojas_trabajo_quimico = models.HojaTrabajoQuimico.objects.filter(ID_HDT=x)
            hojas_trabajo = models.HojaTrabajo.objects.filter(id__in=[htq.HojaTrabajo.id for htq in hojas_trabajo_quimico])
            muestras_balanza = models.Muestra.objects.filter(hoja_trabajo__in=hojas_trabajo, indexCurv=1).order_by('muestraMasificada__Prefijo')

            for muestra in muestras_balanza:
                existing_muestra = next((m for m in Doc_Muestra if m["Prefijo"] == muestra.muestraMasificada.Prefijo), None)

                if not existing_muestra:
                    # Si no existe, crear la entrada inicial
                    existing_muestra = {
                        "Prefijo": muestra.muestraMasificada.Prefijo if muestra.muestraMasificada else None,
                        "Peso": muestra.peso_m,
                        "Volumen": muestra.v_ml,
                        "HojaTrabajo": {
                            "ID_HDT": x,
                            "Tipo": muestra.hoja_trabajo.Tipo if muestra.hoja_trabajo else None,
                            "Duplicado": muestra.hoja_trabajo.Duplicado if muestra.hoja_trabajo else None,
                            "Cliente": muestra.hoja_trabajo.odt.Cliente.nombre_empresa if muestra.hoja_trabajo.odt.Cliente else "Sin Cliente"
                        },
                        "Elementos": {e: None for e in elementos_unicos},  # Inicializar diccionario de elementos vacíos
                    }
                    Doc_Muestra.append(existing_muestra)

                resultado_key = (muestra.id, muestra.elemento)
                resultado_data = resultados_map.get(resultado_key, {
                    "resultado_id": None,
                    "dilucion": None,
                    "resultadoAnalisis": None,
                    "leyAnalisis": None,
                })

                # Llenar el elemento en la posición correspondiente
                existing_muestra["Elementos"][muestra.elemento] = {
                    "resultado_id": resultado_data["resultado_id"],
                    "dilucion": resultado_data["dilucion"],
                    "resultadoAnalisis": resultado_data["resultadoAnalisis"],
                    "leyAnalisis": resultado_data["leyAnalisis"],
                }

                if muestra.elemento not in elementos_unicos:
                    elementos_unicos.append(muestra.elemento)
        
        context = {
            'id_hdt': id_hdt_final,
            'Doc_Muestra': Doc_Muestra,
            'muestras_count': len(Doc_Muestra),
            'elementos_unicos': elementos_unicos,
            'Batch_ID':id_Batch,
            'Bacth_Creación':Creación_Batch,
            'batch_mode': batch_mode,
            'curvaturas':curvaturas
        }
        return render(request, 'Puesto-Absorcion.html', context)
    return render(request, 'Puesto-Absorcion.html')

@login_required(login_url='/login')
@is_internal_user
def obtener_hojas_trabajo(request):
    if request.method == 'GET':
        hojas = models.HojaTrabajoQuimico.objects.filter(confirmar_balanza=True).values_list('ID_HDT', flat=True).distinct()
        return JsonResponse({'hojas': list(hojas)}, safe=False)
    return JsonResponse({'error': 'Método no permitido'}, status=405)

@login_required(login_url='/login')
@is_internal_user
def Lot_Generator(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            lot_id = data.get('id', None)
            
            if not lot_id:
                return JsonResponse({'error': 'ID no proporcionado'}, status=400)
            
            lot_id_list = lot_id.split('-')
            resultados = []


            ID_Taker = random.randint(100000, 999999)

            
            for lot in lot_id_list:
                hojas_trabajo_quimico = models.HojaTrabajoQuimico.objects.filter(ID_HDT=lot)

                for hoja_quimica in hojas_trabajo_quimico:
                    hoja_trabajo = hoja_quimica.HojaTrabajo
                    modelLot = models.LotesAbsorción.objects.create(
                        ID_LT = ID_Taker,
                        hoja_trabajo = hoja_quimica,
                        curv_1 = 0,
                        curv_2 = 0,
                        curv_3 = 0,
                        curv_4 = 0
                    )
                    muestras = models.Muestra.objects.filter(
                        hoja_trabajo=hoja_trabajo
                    ).order_by('elemento')

                    resultado = {
                        "ID_HDT": lot,
                        "HojaTrabajo": hoja_trabajo.id,
                        "Muestras": []
                    }

                    for muestra_target in muestras:
                        
                        elementos = models.Elementos.objects.filter(nombre=muestra_target.elemento)
                        elementoTarget = models.Elementos.objects.get(nombre = muestra_target.elemento)
                        models.Resultado.objects.create(
                            elemento=elementoTarget,
                            muestra=muestra_target,
                            lote_absorcion=modelLot,
                            resultadoAnalisis=0.0,
                            leyAnalisis=0.0, 
                            fecha_emision=timezone.now()
                        )


                        resultado["Muestras"].append({
                            "Nombre": muestra_target.nombre,
                            "Elemento": muestra_target.elemento,
                            "Peso": muestra_target.peso_m,
                            "Volumen": muestra_target.v_ml,
                            "Elementos": [
                                {
                                    "Nombre": elemento.nombre,
                                    "Gramos": elemento.gramos,
                                    "Miligramos": elemento.miligramos
                                }
                                for elemento in elementos
                            ]
                        })

                        print(f"  - {muestra_target.nombre} ({muestra_target.elemento}): Peso={muestra_target.peso_m}, Volumen={muestra_target.v_ml}")

                    resultados.append(resultado)
                    modelLot.save()

            resultado = {
                'success': True,
                'generated_lot_id': ID_Taker,
                'message': f'Lote generado correctamente con ID {ID_Taker}',
                'detalles': resultados
            }
            return JsonResponse(resultado)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Error en el formato de los datos'}, status=400)
    else:
        return JsonResponse({'error': 'Método no permitido'}, status=405)



@login_required(login_url='/login')
@is_internal_user
def get_lotes(request):
    if request.method == 'GET':
        lotes = models.LotesAbsorción.objects.values('ID_LT').distinct()
        lotes_list = [{'id': lote['ID_LT']} for lote in lotes]
        return JsonResponse({'lotes': lotes_list}, safe=False)
    return JsonResponse({'error': 'Método no permitido'}, status=405)


@login_required(login_url='/login')
@is_internal_user
def delete_lote(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            lote_id = data.get('lote_id')
            
            if not lote_id:
                return JsonResponse({'success': False, 'error': 'ID del lote no proporcionado.'}, status=400)

            lotes = models.LotesAbsorción.objects.filter(ID_LT=lote_id)
            
            if not lotes.exists():
                return JsonResponse({'success': False, 'error': f'No se encontró ningún lote con ID {lote_id}.'}, status=404)

            resultados = models.Resultado.objects.filter(lote_absorcion__in=lotes)
            resultados_count = resultados.count() 
            resultados.delete()

            lotes_count = lotes.count() 
            lotes.delete()

            return JsonResponse({
                'success': True,
                'message': f'Lote {lote_id} y {resultados_count} resultados asociados eliminados correctamente.',
                'lotes_eliminados': lotes_count,
                'resultados_eliminados': resultados_count
            })
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Datos no válidos.'}, status=400)
    else:
        return JsonResponse({'success': False, 'error': 'Método no permitido.'}, status=405)


@login_required(login_url='/login')
@is_internal_user
def guardar_valores_absorción(request):
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            datos = body.get('datos', [])
            curvaturas = body.get('curvaturas', []) 
            contexto = body.get('contexto')

            for dato in datos:
                resultado_id = dato.get('resultado_id')
                valor = dato.get('valor')

                resultado = models.Resultado.objects.filter(id=resultado_id).first()
                if resultado:
                    if contexto == 1: 
                        resultado.dilucion = float(valor)
                    elif contexto == 2:  
                        resultado.resultadoAnalisis = float(valor)
                    elif contexto == 3:
                        resultado.leyAnalisis = float(valor)
                    resultado.save()

            lotes_actualizados = set()
            for dato in datos:
                resultado = models.Resultado.objects.filter(id=dato['resultado_id']).first()
                if resultado and resultado.lote_absorcion:
                    lote = resultado.lote_absorcion
                    if lote.id not in lotes_actualizados:
                        for curvatura in curvaturas:
                            curv_id = curvatura.get('curv_id')
                            valor = curvatura.get('valor')

                            if curv_id == '1':
                                lote.curv_1 = float(valor)
                            elif curv_id == '2':
                                lote.curv_2 = float(valor)
                            elif curv_id == '3':
                                lote.curv_3 = float(valor)
                            elif curv_id == '4':
                                lote.curv_4 = float(valor)

                        lote.save()
                        lotes_actualizados.add(lote.id)

            return JsonResponse({'success': True, 'message': 'Valores y curvaturas guardados correctamente.'})
        except Exception as e:
            print(e)
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    else:
        return JsonResponse({'success': False, 'error': 'Método no permitido.'}, status=405)


@login_required(login_url='/login')
@is_internal_user
def PT_Module(request):
    fecha_actual = timezone.now()

    acciones_registros = models.Novedades.objects.filter(
        accion__in=['Crear', 'Modificar', 'Eliminar']
    ).order_by('-fecha') 

    procesos_hojas_trabajo = models.Novedades.objects.filter(
        accion__in=['Balanza', 'Absorcion']
    ).order_by('-fecha')

    context = {
        'acciones_registros': acciones_registros,
        'procesos_hojas_trabajo': procesos_hojas_trabajo,
    }

    return render(request, 'Puesto-Trabajo.html', context)


@login_required(login_url='/login')
@is_internal_user
def ODT_Info(request):
    if request.method == 'POST':
        odt_id = request.POST.get('odt_id')
        odt = models.ODT.objects.get(id=odt_id)

        muestras_M = models.MuestraMasificada.objects.filter(odt=odt).annotate(
            prefijo_numero=Cast('Prefijo', output_field=IntegerField())
        ).order_by('prefijo_numero')

        HDT = models.HojaTrabajo.objects.filter(odt=odt).order_by('-id')  

        HDT_Quimico = models.HojaTrabajoQuimico.objects.filter(HojaTrabajo__in=HDT).values('ID_HDT').distinct().order_by('-ID_HDT')

        context = {"odt": odt, "Muestras": muestras_M, "HDT_Quimico": HDT_Quimico}

        return render(request, 'ODT-Info.html', context)
    else:
        return HttpResponse(status=405)
    
@login_required(login_url='/login')
@is_internal_user
def Elements_Section(request):
    elementos = models.Elementos.objects.all()

    tipo_filtrado = request.GET.get('tipo', '')
    if tipo_filtrado:
        elementos = elementos.filter(nombre__icontains=tipo_filtrado)

    context = {
        'elementos': elementos,
    }

    return render(request, "Elements.html", context)

@login_required(login_url='/login')
@is_internal_user
def Analysis_Section(request):
    analisis = models.MetodoAnalisis.objects.all()
    query = request.GET.get('search', '') 
    if query:
        analisis = analisis.filter(nombre__icontains=query)  

    context = {
        'analisis': analisis,
        'query': query, 
    }
    return render(request, "analysis.html", context)


@login_required(login_url='/login')
@is_internal_user
def general_form(request, token):
    try:
        decoded_data = base64.urlsafe_b64decode(token.encode()).decode()
        data = json.loads(decoded_data)

        target_ID = str(data.get('id'))
        context = data.get('context')
        action = data.get('action')
        stade = data.get('stade')

        form = None
        model = None

        # Verificar el estado
        if stade != "acces":
            return HttpResponseForbidden("Acceso no autorizado.")
        # Validar contexto y acción
        if context not in ['element', 'analytic', 'ODT', 'Read', 'curv', 'HDT', 'User']:
            return HttpResponseForbidden("Contexto no válido.")
        if action not in ['add', 'mod', 'del']:
            return HttpResponseForbidden("Acción no válida.")
        # Procesar según el contexto y la acción
        if context == 'element':
            if action == 'add':
                form = forms.ElementosForm()
                if request.method == 'POST':
                    form = forms.ElementosForm(request.POST)
                    if form.is_valid():
                        form.save()
                        return redirect(reverse('elements_manager'))
            elif action == 'mod':
                # Lógica para modificar un elemento
                model = models.Elementos.objects.get(id=target_ID)
                form = forms.ElementosForm(instance = model)
                if request.method == 'POST':
                    form = forms.ElementosForm(request.POST, instance=model)
                    if form.is_valid():
                        form = form.save()
                        return redirect(reverse('elements_manager'))
            elif action == 'del':
                model = models.Elementos.objects.get(id=target_ID)
                if request.method == "GET":
                    model.delete()
                    messages.add_message(request=request, level=messages.SUCCESS, message='Elemento eliminado con exito')
                    return redirect(reverse('elements_manager'))
                
        if context == 'ODT':
            if action == 'add':
                form = forms.ODTForm()
                if request.method == 'POST':
                    form = forms.ODTForm(request.POST)
                    if form.is_valid():
                        odt_instance = form.save()
                        models.Novedades.objects.create(
                            tipo_model='Orden de trabajo',
                            accion="Crear",
                            modelt_id=str(odt_instance.Prefijo),
                            fecha=timezone.now(),
                            usuario = request.user
                        )
                        return redirect(reverse('Main_ODT'))
            elif action == 'mod':
                model = models.ODT.objects.get(id=target_ID)
                form = forms.ODTForm(instance=model)
                model.Fec_Recep = model.Fec_Recep.strftime('%Y-%m-%d')
                model.Fec_Finalizacion = model.Fec_Finalizacion.strftime('%Y-%m-%d')
                form = forms.ODTForm(instance=model)

                if request.method == 'POST':
                    form = forms.ODTForm(request.POST, instance=model)
                    if form.is_valid():
                        try:
                            odt_instance = form.save()
                            models.Novedades.objects.create(
                                tipo_model='Orden de trabajo',
                                accion="Modificar",
                                modelt_id=str(odt_instance.Prefijo),
                                fecha=timezone.now(),
                                usuario=request.user
                            )
                            messages.add_message(request=request, level=messages.SUCCESS, message='Se ajustó la orden de trabajo con éxito.')
                            return redirect(reverse('Main_ODT'))
                        except ValidationError as e:
                            messages.add_message(request=request, level=messages.ERROR, message='La orden de trabajo ya tiene una hoja de trabajo asociada.')
                            return redirect(reverse('Main_ODT'))
                    else:
                        # Si el formulario no es válido
                        messages.add_message(request=request, level=messages.ERROR, message='Error al ajustar la orden de trabajo. Por favor, verifica los datos ingresados.')
                        return redirect(reverse('Main_ODT'))
            elif action == 'del':
                model = models.ODT.objects.get(id=target_ID)
                if request.method == "GET":
                    Muestra_M = models.MuestraMasificada.objects.filter(odt=model)
                    Muestras_HDT = models.Muestra.objects.filter(muestraMasificada__in=Muestra_M)   
                    if Muestras_HDT.exists():
                        messages.add_message(request=request, level=messages.ERROR, message='Algunas muestras estan operativas en una hoja de trabajo, eliminalas antes de aplicar esta acción')
                        return redirect(reverse('Main_ODT'))
                    else:
                        models.Novedades.objects.create(
                            tipo_model='Orden de trabajo',
                            accion="Eliminar",
                            modelt_id=str(model.Prefijo),
                            fecha=timezone.now(),
                            usuario = request.user
                        )
                        model.delete()
                        messages.add_message(request=request, level=messages.SUCCESS, message='Se eliminó la orden de trabajo con exito')
                        return redirect(reverse('Main_ODT'))

        if context == 'curv':
            if action == 'add':
                form = forms.CurvaturaForm()
                if request.method == 'POST':
                    form = forms.CurvaturaForm(request.POST)
                    if form.is_valid():
                        form.save()
                        return redirect(reverse('elements_manager'))
            elif action == 'mod':
                # Lógica para modificar un elemento
                model = models.CurvaturaElementos.objects.get(id=target_ID)
                form = forms.CurvaturaForm(instance = model)
                if request.method == 'POST':
                    form = forms.CurvaturaForm(request.POST, instance=model)
                    if form.is_valid():
                        form = form.save()
                        return redirect(reverse('elements_manager'))
                        
            elif action == 'del':
                model = models.CurvaturaElementos.objects.get(id=target_ID)
                if request.method == "GET":
                    model.delete()
                    return redirect(reverse('elements_manager'))
        
        elif context == 'analytic':
            if action == 'add':
                form = forms.MetodoAnalisisForm()
                if request.method == 'POST':
                    form = forms.MetodoAnalisisForm(request.POST)
                    if form.is_valid():
                        form.save()
                        return redirect(reverse('analisis_manager'))
            elif action == 'mod':
                # Lógica para modificar un elemento
                model = models.MetodoAnalisis.objects.get(id=target_ID)
                form = forms.MetodoAnalisisForm(instance = model)
                if request.method == 'POST':
                    form = forms.MetodoAnalisisForm(request.POST, instance=model)
                    if form.is_valid():
                        form = form.save()
                        return redirect(reverse('analisis_manager'))
                        
            elif action == 'del':
                model = models.MetodoAnalisis.objects.get(id=target_ID)
                if request.method == "GET":
                    model.delete()
                    return redirect(reverse('analisis_manager'))

        if context == 'HDT':
            if action == 'add':
                form = forms.HojaTrabajoGeneralForm()
                if request.method == 'POST':
                    form = forms.HojaTrabajoGeneralForm(request.POST)
                    if form.is_valid():
                        hdt_instance = form.save()

                        hoja_trabajo_quimico = hdt_instance.hojas_trabajo_target.first()

                        if hoja_trabajo_quimico:
                            models.Novedades.objects.create(
                                tipo_model='Hoja de trabajo',
                                accion="Crear",
                                modelt_id=hoja_trabajo_quimico.ID_HDT,  
                                fecha=timezone.now(),
                                usuario=request.user
                            )
                        return redirect(reverse('Main_ODT'))
            
            elif action == 'mod':
                hoja_trabajo_quimico = models.HojaTrabajoQuimico.objects.filter(ID_HDT=target_ID).first()
                
                if not hoja_trabajo_quimico:
                    messages.add_message(request=request, level=messages.ERROR, message='No se encontró la hoja de trabajo química.')
                    return redirect(reverse('Main_ODT'))

                hoja_trabajo = hoja_trabajo_quimico.HojaTrabajo

                form = forms.HojaTrabajoGeneralForm(instance=hoja_trabajo)
                if request.method == 'POST':
                    form = forms.HojaTrabajoGeneralForm(request.POST, instance=hoja_trabajo)
                    if form.is_valid():
                        hoja_trabajo_instance = form.save()
                        models.Novedades.objects.create(
                            tipo_model='Hoja de trabajo',
                            accion="Modificar",
                            modelt_id=hoja_trabajo_quimico.ID_HDT,  
                            fecha=timezone.now(),
                            usuario=request.user
                        )
                        messages.add_message(request=request, level=messages.SUCCESS, message='Hoja de trabajo modificada con éxito.')
                        return redirect(reverse('Main_ODT'))
                    else:
                        messages.add_message(request=request, level=messages.ERROR, message='Error al modificar la hoja de trabajo. Verifica los datos ingresados.')
                        return redirect(reverse('Main_ODT'))
    
            elif action == 'del':
                try:
                    modelos_hoja_trabajo_quimico = models.HojaTrabajoQuimico.objects.filter(ID_HDT=target_ID)
                    
                    if not modelos_hoja_trabajo_quimico.exists():
                        messages.add_message(request=request, level=messages.ERROR, message='No se encontró el registro a eliminar')
                        return redirect(reverse('Main_ODT'))

                    hojas_trabajo_relacionadas = list(set(modelo.HojaTrabajo for modelo in modelos_hoja_trabajo_quimico))
                    
                    modelos_hoja_trabajo_quimico.delete()

                    for hoja_trabajo in hojas_trabajo_relacionadas:
                        hoja_trabajo.delete()
                    
                    models.Novedades.objects.create(
                        tipo_model='Hoja de trabajo',
                        accion="Eliminar",
                        modelt_id=target_ID, 
                        fecha=timezone.now(),
                        usuario=request.user
                    )

                    messages.add_message(request=request, level=messages.SUCCESS, message='Hojas de trabajo eliminadas con éxito')
                    return redirect(reverse('Main_ODT'))

                except Exception as e:
                    print(e)
                    messages.add_message(request=request, level=messages.ERROR, message=f'Error al eliminar las hojas de trabajo: {str(e)}')
                    return redirect(reverse('Main_ODT'))


        if context == 'User':
            if action == 'add':
                form = forms.CustomUserCreationForm()
                if request.method == 'POST':
                    form = forms.CustomUserCreationForm(request.POST)
                    if form.is_valid():
                        form.save()
                        return redirect(reverse('user_list'))
            elif action == 'mod':
                # Lógica para modificar un elemento
                model = models.User.objects.get(id=target_ID)
                form = forms.CustomUserCreationForm(instance = model)
                if request.method == 'POST':
                    form = forms.CustomUserCreationForm(request.POST, instance=model)
                    if form.is_valid():
                        form = form.save()
                        return redirect(reverse('user_list'))
            elif action == 'del':
                model = models.User.objects.get(id=target_ID)
                if request.method == "GET":
                    model.delete()
                    messages.add_message(request=request, level=messages.SUCCESS, message='Usuario eliminado con exito')
                    return redirect(reverse('user_list'))




        
        elif context == 'Read':
            # Lógica para 'Read'
            result_message = f'Lectura {target_ID} procesada con éxito.'


       
        data = {'form':form, 'id':target_ID, "contexModel": context, "action": action}
        return render(request, "General_form.html", data)

    except Exception as e:
        # En caso de error, retornar una respuesta de error
        return HttpResponseForbidden(f"Error al procesar el token: {str(e)}")
    



@login_required(login_url='/login')
@is_internal_user
def Master_def(request):
    if request.method != 'POST':
        return HttpResponseForbidden("Método no permitido.")
    
    id = request.POST.get('id')
    context = request.POST.get('context')
    action = request.POST.get('action')
    stade = request.POST.get('stade')

    if stade != "acces":
        return HttpResponseForbidden("Acceso no autorizado.")

    # Crear el objeto de datos
    data = {
        'id': id,
        'context': context,
        'action': action,
        'stade': stade
    }
    print((data))
    # Codificar el objeto de datos en base64
    token = base64.urlsafe_b64encode(json.dumps(data).encode()).decode()

    print(token)  # Para depuración

    # Crear la URL de redirección
    redirect_url = f'/Action-Resource/{token}/'

    return JsonResponse({'redirect_url': redirect_url, 'message': 'Datos recibidos correctamente'})




def get_proyectos(request):
    cliente_id = request.GET.get('cliente_id')
    proyectos = models.Proyecto.objects.filter(cliente_id=cliente_id)
    data = {
        'proyectos': list(proyectos.values('id', 'nombre'))
    }
    return JsonResponse(data)


def check_db_connection(request):
    try:
        connection.ensure_connection()
        return JsonResponse({'status': 'success', 'message': 'Database is connected'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Failed to connect to the database: {str(e)}'})
    
def get_user_data(request):
    user = request.user

    URL_React = ""

    if settings.ENABLED_LOGIN_LOCAL:
       URL_React = settings.URL_LOCAL
    else:
        URL_React = settings.URL_REACT
    user_data = {
        'email': user.username,         
        'full_name': f"{user.first_name} {user.last_name}",
        'role': user.rolname,
        'URLReact':URL_React,
        'LocalURL':settings.URL_LOCAL          
    }
    return JsonResponse(user_data)



def servicios(request):
    return render(request, 'servicios.html')


def sobre_nosostros(request):
    return render(request, 'sobre_nosotros.html')


def recursos(request):
    return render(request, 'recursos.html')




def noticias(request):
    noticias = models.Noticia.objects.all()
    return render(request, 'noticias.html', {'noticias': noticias})



def is_admin(user):
    return user.is_authenticated and user.rolname == 'administrador'

#--------------------------------------------Seccion de funciones de noticias
#Funcion de modificar noticias creadas
@is_administrador
def modificar_noticia(request, noticia_id):
    noticia = models.Noticia.objects.get(id=noticia_id)
    if request.method == 'POST':
        form = forms.NoticiaForm(request.POST, request.FILES, instance=noticia)
        if form.is_valid():
            form.save()
            messages.success(request, 'La noticia ha sido modificada exitosamente.')
            return redirect('noticias') 
        else:
            messages.error(request, 'Hubo un error al intentar modificar la noticia.')
    else:
        form = forms.NoticiaForm(instance=noticia)

    return render(request, 'modificar_noticia.html', {'form': form, 'noticia': noticia})

#Funcion de agregar noticias
@login_required(login_url='/login')
@is_administrador
def agregar_noticia(request):
    if not request.user.is_authenticated or request.user.rolname != 'administrador':
        return HttpResponseForbidden("No tienes permiso para acceder a esta página.")

    if request.method == 'POST':
        form = forms.NoticiaForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('noticias') 
    else:
        form = forms.NoticiaForm()

    return render(request, 'agregar_noticia.html', {'form': form})

#Funcion de eliminar noticias
@login_required(login_url='/login')
@is_administrador
def eliminar_noticia(request, noticia_id):
    noticia = models.Noticia.objects.get(id=noticia_id)
    if request.method == 'POST':
        noticia.delete()
        messages.success(request, 'La noticia ha sido eliminada exitosamente.')
        return redirect('noticias')  
    return render(request, 'eliminar_noticia.html', {'noticia': noticia})


#Funcion para recibir correos de contacto
def contacto(request):
    enviado = False
    if request.method == 'POST':
        form = forms.ContactoForm(request.POST)
        if form.is_valid():
            nombre = form.cleaned_data['nombre']
            email = form.cleaned_data['email']
            mensaje = form.cleaned_data['mensaje']

            send_mail(
                subject=f'Contacto de {nombre}', 
                message=f'Mensaje de {nombre} <{email}>:\n\n{mensaje}',  
                from_email=email, 
                recipient_list=['tu_correo@gmail.com'], 
                fail_silently=False,
            )
            enviado = True
    else:
        form = forms.ContactoForm()

    return render(request, 'contacto.html', {'form': form, 'enviado': enviado})



#-------------------------------------------------------------------------------------------------------------------------------------------------------
# Vista para listar los usuarios con filtros
@login_required
@is_administrador_or_supervisor
def UserListView(request):
    users = User.objects.all()
    
    # Aplicar filtros si existen en la solicitud GET
    role_filter = request.GET.get('role')
    shift_filter = request.GET.get('shift')
    search_query = request.GET.get('search')

    if role_filter:
        users = users.filter(rolname=role_filter)
    if shift_filter:
        users = users.filter(turno=shift_filter)
    if search_query:
        users = users.filter(first_name__icontains=search_query)  # Busca por nombre

    user_roles = User.Role.choices  # Obtener roles para el filtro

    context = {
        'users': users,
        'user_roles': [role[1] for role in user_roles],  # Extraer solo los nombres de los roles
    }
    
    return render(request, 'Gestion_usuario.html', context)

# Vista para agregar un usuario
@login_required
@is_administrador_or_supervisor
def add_user(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Usuario agregado correctamente.")
            return redirect('Gestion_usuario')
    else:
        form = CustomUserCreationForm()

    return render(request, 'user_form.html', {'form': form, 'title': 'Agregar Usuario'})

# Vista para modificar un usuario existente
@login_required
@is_administrador_or_supervisor
def modify_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Usuario modificado correctamente.")
            return redirect('Gestion_usuario')
    else:
        form = CustomUserCreationForm(instance=user)

    return render(request, 'user_form.html', {'form': form, 'title': 'Modificar Usuario'})

# Vista para eliminar un usuario
@login_required
@is_administrador_or_supervisor
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        user.delete()
        messages.success(request, "Usuario eliminado correctamente.")
        return redirect('Gestion_usuario')

    return render(request, 'user_confirm_delete.html', {'user': user})

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from .models import User

@login_required
def perfil(request):
    """
    Carga la información del usuario autenticado en la plantilla Perfil.html.
    """
    return render(request, "Perfil.html", {"user": request.user})

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required

@login_required
@csrf_protect  # Mantiene protección CSRF
@is_full_acceso
def actualizar_perfil(request):
    """
    Permite actualizar la información del perfil del usuario autenticado.
    """
    if request.method == "POST":
        try:
            if request.content_type == "application/json":
                data = json.loads(request.body)
            else:
                data = request.POST

            user = request.user
            user.first_name = data.get("nombre", user.first_name)
            user.last_name = data.get("apellido", user.last_name)
            user.username = data.get("correo", user.username)  # Si el correo se usa como username
            user.numero = data.get("numero", user.numero)
            user.turno = data.get("turno", user.turno)
            user.rut = data.get("rut", user.rut)

            user.save()
            return JsonResponse({"status": "success", "message": "Perfil actualizado correctamente."})

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

    return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Cliente, Proyecto
from .forms import ClienteForm, ProyectoForm

@login_required
@is_administrador_or_supervisor
def agregar_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Cliente agregado exitosamente.")
            return redirect('user_list')
    else:
        form = ClienteForm()
    return render(request, 'cliente_form.html', {'form': form, 'title': 'Agregar Cliente'})

@login_required
@is_administrador_or_supervisor
def agregar_proyecto(request):
    if request.method == 'POST':
        form = ProyectoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Proyecto agregado exitosamente.")
            return redirect('user_list')
    else:
        form = ProyectoForm()
    return render(request, 'proyecto_form.html', {'form': form, 'title': 'Agregar Proyecto'})
#----------------------------------------------------------------------------------------------------------------
# views.py

from django.http import JsonResponse
from .models import Muestra
import serial
import time
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
import json
from django.http import JsonResponse
import serial

@is_internal_user
def leer_peso_balanza(request):
    try:
        # Abre el puerto de la balanza
        balanza = serial.Serial('COM3', 9600, timeout=1)

        # Envía el comando para pedir el dato (puede variar por modelo: 'P\r\n', 'SI\r\n', etc.)
        balanza.write(b'SI\r\n')  # Prueba también con b'P\r\n' si 'SI' no funciona

        tiempo_espera = time.time() + 3  # Esperar hasta 3 segundos
        while time.time() < tiempo_espera:
            if balanza.in_waiting > 0:
                datos = balanza.readline().decode('utf-8', errors='ignore').strip()
                print("Dato recibido:", datos)

                try:
                    numero = float(''.join(filter(lambda c: c.isdigit() or c == '.', datos)))
                    balanza.close()
                    return JsonResponse({'peso': numero})
                except:
                    continue  # Intenta leer otra línea si no es un número válido
            time.sleep(0.1)

        balanza.close()
        return JsonResponse({'peso': None, 'mensaje': '⏱ Tiempo de espera agotado'})

    except Exception as e:
        return JsonResponse({'peso': None, 'error': str(e)})




@csrf_exempt

def guardar_peso(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        muestra_id = data.get('id')
        peso = data.get('peso')
        print(f"Guardando peso... Muestra ID: {muestra_id}, Peso: {peso}")  # 💬
        muestra = get_object_or_404(Muestra, id=muestra_id)
        muestra.peso_m = peso
        muestra.save()
        return JsonResponse({'ok': True, 'peso': muestra.peso_m})





def verificar_balanza(request):
    try:
        balanza = serial.Serial('COM3', 9600, timeout=1)
        if balanza.is_open:
            balanza.close()
            return JsonResponse({'conectado': True, 'mensaje': '✅ Balanza conectada'})
        else:
            return JsonResponse({'conectado': False, 'mensaje': '❌ Balanza no es reconocida'})
    except Exception as e:
            return JsonResponse({'conectado': False, 'mensaje': '❌ Balanza no conectada'})


def vista_muestras(request):
    if request.method == 'POST':
        id_hdt = request.POST.get('id')

        muestras = Muestra.objects.filter(muestraMasificada__odt__hoja_trabajo_id=id_hdt)

        return render(request, 'Balanza.html', {
            'muestras': muestras,
            'id_hdt': id_hdt,
            'stade': False,  # o tu lógica real para estado de la hoja
        })


def HojaTrabajoNueva(request):
    return render(request, 'HT_nueva.html')


from django.shortcuts import render

def Main(request):
    return render(request, 'index.html')




from .models import (
    AnalisisCuTFeZn,
    AnalisisCuS4FeS4MoS4,
    AnalisisMulti,
    AnalisisCuS10FeS10MoS10,
    AnalisisCuSCuSFe,
    AnalisisCuTestConsH
)


def vista_analisis(request):
    contexto = {
        "analisis_cutfezn": AnalisisCuTFeZn.objects.all(),
        "analisis_cus4fes4mos4": AnalisisCuS4FeS4MoS4.objects.all(),
        "analisis_multi": AnalisisMulti.objects.all(),
        "analisis_cus10fes10mos10": AnalisisCuS10FeS10MoS10.objects.all(),
        "analisis_cuscusfe": AnalisisCuSCuSFe.objects.all(),
        "analisis_cutest": AnalisisCuTestConsH.objects.all(),
    }
    return render(request, "HT_nueva.html", contexto)

@login_required
def Ajustar_Muestras(request):
    return render(request, 'Ajustar-Muestras.html')




from django.http import HttpResponse
from django.contrib.auth import get_user_model

def crear_admin(request):
    User = get_user_model()

    if User.objects.filter(username='admin@example.com').exists():
        return HttpResponse("🟡 El usuario ya existe.")

    User.objects.create_user(
        firstname='Juan',
        lastname='Pérez',
        username='admin@example.com',
        password='adminsegura123',
        rut='12.345.678-9',
        rolname='administrador',
        turno='Dia',
        numero='+56912345678',
        is_staff=True,
        is_superuser=True
    )
    return HttpResponse("✅ Usuario administrador creado correctamente.")