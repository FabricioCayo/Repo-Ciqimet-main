from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.password_validation import CommonPasswordValidator, validate_password
from .models import User, Proyecto, Cliente, Muestra, AnalisisCuTFeZn, AnalisisCuS4FeS4MoS4, AnalisisMulti, AnalisisCuS10FeS10MoS10, AnalisisCuSCuSFe, AnalisisCuTestConsH, Resultado, ODT, MuestraMasificada, Elementos, MetodoAnalisis, Parametros, Estandar, HojaTrabajo, HojaTrabajoQuimico, Novedades, Noticia
from django.utils import timezone
from django.core.exceptions import ValidationError
import random
from phonenumber_field.formfields import PhoneNumberField

class CustomUserCreationForm(UserCreationForm):
    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        help_text="La contraseña debe cumplir con los requisitos de seguridad.",
    )
    password2 = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        help_text="Ingrese la misma contraseña para confirmar.",
    )
    numero = PhoneNumberField(label="Número de Teléfono")

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'rut', 'username', 'rolname', 'turno', 'numero')


    def save(self, commit=True):
        # Obtiene el usuario pero no lo guarda todavía
        user = super().save(commit=False)

        # Asigna la contraseña encriptada
        user.set_password(self.cleaned_data["password1"])

        # Si el rol es "administrador", asigna permisos de administrador
        if user.rolname == User.Role.ADMINISTRADOR:
            user.is_staff = True
            user.is_superuser = True

        # Guarda el usuario si commit es True
        if commit:
            user.save()
        return user


    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Este correo electrónico ya está en uso.")
        return username

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        return password2

class ContactoForm(forms.Form):
    nombre = forms.CharField(
        max_length=100, 
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',  
            'placeholder': 'Ingresa tu nombre' 
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',  # Clase de Bootstrap
            'placeholder': 'Ingresa tu correo'  # Placeholder descriptivo
        })
    )
    mensaje = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={  # Cambiamos a TextInput para igualar el tamaño
            'class': 'form-control',  # Clase de Bootstrap
            'placeholder': 'Escribe tu mensaje'  # Placeholder descriptivo
        })
    )

class NoticiaForm(forms.ModelForm):
    class Meta:
        model = Noticia
        fields = ['titulo', 'descripcion', 'contenido_completo', 'imagen']
        
from django import forms
from .models import Cliente, Proyecto

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nombre_empresa', 'rut', 'direccion', 'telefono', 'email']
        widgets = {
            'nombre_empresa': forms.TextInput(attrs={'class': 'form-control'}),
            'rut': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class ProyectoForm(forms.ModelForm):
    class Meta:
        model = Proyecto
        fields = ['nombre', 'cliente', 'fecha_emision']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'cliente': forms.Select(attrs={'class': 'form-control'}),  # Lista desplegable de clientes
            'fecha_emision': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }



class MuestraForm(forms.ModelForm):
    class Meta:
        model = Muestra
        fields = '__all__'

class AnalisisCuTFeZnForm(forms.ModelForm):
    class Meta:
        model = AnalisisCuTFeZn
        fields = ['l_ppm_fe', 'l_ppm_bk_fe', 'fe', 'l_ppm_zn', 'l_ppm_bk_zn', 'zn']

class AnalisisCuS4FeS4MoS4Form(forms.ModelForm):
    class Meta:
        model = AnalisisCuS4FeS4MoS4
        fields = ['control1_cut_cus', 'l_ppm_cus_fe', 'l_ppm_bk_fes4', 'fes4', 'control2_cut_fes4']

class AnalisisMultiForm(forms.ModelForm):
    class Meta:
        model = AnalisisMulti
        fields = [
            'l_ppm_ag', 'l_ppm_ag_bk', 'ag', 'l_ppm_as', 'l_ppm_as_bk', 
            'analisis_as', 'l_ppm_mo', 'l_ppm_mo_bk', 'mo', 'l_ppm_pb', 
            'l_ppm_pb_bk', 'pb', 'l_ppm_cu', 'l_ppm_cu_bk', 'cu'
        ]

class AnalisisCuS10FeS10MoS10Form(forms.ModelForm):
    class Meta:
        model = AnalisisCuS10FeS10MoS10
        fields = ['control_cut_cus', 'cut', 'cus10']

class AnalisisCuSCuSFeForm(forms.ModelForm):
    class Meta:
        model = AnalisisCuSCuSFe
        fields = [
            'l_ppm_cus_fe', 'l_ppm_bk_cus_fe', 'cus_fe', 
            'control2_cut_cus_fe', 'cut', 'cus_c', 'cus_fe_2'
        ]

class AnalisisCuTestConsHForm(forms.ModelForm):
    class Meta:
        model = AnalisisCuTestConsH
        fields = [
            'control1_cut_cutest', 'cut', 'cut_test', 'gaston_ml', 
            'gasto_bk_ml', 'n_naco3', 'alicuota', 'consumo_h'
        ]

class ResultadoForm(forms.ModelForm):
    class Meta:
        model = Resultado
        fields = '__all__'



class ODTForm(forms.ModelForm):
    class Meta:
        model = ODT
        fields = [
            'Fec_Recep', 'Fec_Finalizacion', 'id', 'Prefijo', 'Cliente', 'Proyecto', 
            'Responsable', 'Prioridad', 'TipoMuestra', 'Referencia', 'Comentarios', 'Cant_Muestra'
        ]
        widgets = {
            'Fec_Recep': forms.DateInput(attrs={'type': 'date'}),
            'Fec_Finalizacion': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['Fec_Recep'].input_formats = ['%Y-%m-%d']
        self.fields['Fec_Finalizacion'].input_formats = ['%Y-%m-%d']

    def save(self, commit=True):
        if self.instance.pk: 
            hoja_trabajo_existe = HojaTrabajo.objects.filter(odt=self.instance).exists()
            if hoja_trabajo_existe:
                raise ValidationError("Este ODT tiene hojas de trabajo asociadas. Modificación no permitida.")

        # Continuar con la lógica de guardado
        odt_instance = super().save(commit=commit)
        muestras_generadas = []
        if odt_instance.Prefijo and odt_instance.Cant_Muestra:
            base_prefijo = int(odt_instance.Prefijo)

            for i in range(odt_instance.Cant_Muestra):
                nuevo_prefijo = str(base_prefijo + i)
                muestra_existente = MuestraMasificada.objects.filter(odt=odt_instance, Prefijo=nuevo_prefijo).first()
                if muestra_existente:
                    muestras_generadas.append(muestra_existente)
                else:
                    nueva_muestra = MuestraMasificada.objects.create(
                        odt=odt_instance,
                        Prefijo=nuevo_prefijo,
                        tipoMuestra=odt_instance.TipoMuestra or 'M'
                    )
                    muestras_generadas.append(nueva_muestra)

        todas_muestras_odt = set(MuestraMasificada.objects.filter(odt=odt_instance))
        muestras_sobrantes = todas_muestras_odt - set(muestras_generadas)
        muestras_en_uso = []
        for muestra in muestras_sobrantes:
            if Muestra.objects.filter(muestraMasificada=muestra).exists():
                muestras_en_uso.append(muestra)
        if muestras_en_uso:
            raise ValidationError("Hay muestras que están en hojas de trabajo, primero elimínelas para continuar.")
        muestras_a_eliminar = muestras_sobrantes - set(muestras_en_uso)
        for muestra in muestras_a_eliminar:
            muestra.delete()

        return odt_instance

class MuestraMasificadaForm(forms.ModelForm):
    class Meta:
        model = MuestraMasificada
        fields = ['odt', 'Prefijo', 'tipoMuestra']
        widgets = {
            'fecha_creacion': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class ElementosForm(forms.ModelForm):
    class Meta:
        model = Elementos
        fields = ['nombre', 'gramos', 'miligramos']

class MetodoAnalisisForm(forms.ModelForm):
    class Meta:
        model = MetodoAnalisis
        fields = ['cliente', 'nombre', 'metodologia', 'elementos']
        widgets = {
            'metodologia': forms.Textarea(attrs={'rows': 4}),
        }

class ParametrosForm(forms.ModelForm):
    class Meta:
        model = Parametros
        fields = ['Elementos', 'Unidad', 'VA', 'DS', 'Min', 'Max']
        widgets = {
            'Elementos': forms.CheckboxSelectMultiple,
        }

class EstandarForm(forms.ModelForm):
    class Meta:
        model = Estandar
        fields = ['Nombre', 'cliente', 'parametros']
        widgets = {
            'parametros': forms.CheckboxSelectMultiple,
        }

class HojaTrabajoForm(forms.ModelForm):
    class Meta:
        model = HojaTrabajo
        fields = ['odt', 'Estandar', 'MetodoAnalisis', 'MuestraMasificada', 'Tipo', 'Duplicado']
        widgets = {
            'Estandar': forms.CheckboxSelectMultiple,
            'Tipo': forms.Select(choices=[('M', 'Muestra'), ('S', 'Estandar'), ('D', 'Duplicado'), ('B', 'Blanco')]),
        }


class HojaTrabajoGeneralForm(forms.ModelForm):
    class Meta:
        model = HojaTrabajo
        fields = ['odt', 'Estandar', 'MetodoAnalisis', 'Tipo', 'Duplicado']
        widgets = {
            'Estandar': forms.CheckboxSelectMultiple,
            'Tipo': forms.Select(choices=[('M', 'Muestra'), ('S', 'Estandar'), ('D', 'Duplicado'), ('B', 'Blanco')]),
        }

    def save(self, commit=True):
        id_hdt_value = ''

        if self.instance.pk:
            muestra_quimico_id = HojaTrabajoQuimico.objects.filter(HojaTrabajo=self.instance).first()
            if not muestra_quimico_id:
                return super().save(commit=commit)

            id_hdt_value = muestra_quimico_id.ID_HDT
            metodo_analisis = self.instance.MetodoAnalisis
            elementos = metodo_analisis.elementos.all()

            if muestra_quimico_id:
                hojas_quimicos = HojaTrabajoQuimico.objects.filter(ID_HDT=id_hdt_value)

                instance = super().save(commit=False)
                hojas_trabajo = [hq.HojaTrabajo for hq in hojas_quimicos]

                odt = self.cleaned_data['odt']
                muestras_masificadas = list(MuestraMasificada.objects.filter(odt=odt))  
                muestras = list(Muestra.objects.filter(hoja_trabajo__in=hojas_trabajo))  
                resultados = list(Resultado.objects.filter(hoja_trabajo__in=hojas_trabajo))

                for hoja_trabajo in hojas_trabajo:
                    hoja_trabajo.odt = self.instance.odt
                    hoja_trabajo.Estandar.set(self.instance.Estandar.all())
                    hoja_trabajo.MetodoAnalisis = self.instance.MetodoAnalisis
                    hoja_trabajo.Tipo = self.instance.Tipo
                    hoja_trabajo.Duplicado = self.instance.Duplicado
                    hoja_trabajo.save()

                for muestra_masificada in muestras_masificadas:
                    muestras_existentes = [m for m in muestras if m.elemento == elemento.nombre and m.muestraMasificada == muestra_masificada]
                    muestras_existentes.sort(key=lambda x: x.indexCurv)

                    for i, muestra in enumerate(muestras_existentes, start=1):
                        if muestra.indexCurv != i:
                            muestra.indexCurv = i
                            muestra.save()
                            print(f"Reordenado índice de muestra: {muestra.nombre} a {i}")

                    if len(muestras_existentes) > 0:
                        exceso = muestras_existentes[1:] 
                        for muestra_exceso in exceso:
                            muestra_exceso.delete()
                        print(f"Eliminadas muestras fuera del rango.")

                    if len(muestras_existentes) < len(elementos):
                        falta = len(elementos) - len(muestras_existentes)
                        for i in range(len(muestras_existentes) + 1, len(muestras_existentes) + falta + 1):
                            nueva_muestra = Muestra.objects.create(
                                nombre=f"{elemento.nombre} - Muestra {i}",
                                proyecto=odt.Proyecto,
                                fecha_emision=timezone.now(),
                                elemento=elemento.nombre,
                                nbo=f"NBO-{i}",
                                ident=f"ID-{i}",
                                indexCurv=i,
                                hoja_trabajo=hojas_trabajo[0], 
                                muestraMasificada=muestra_masificada,
                                t="M",
                                peso_m=0.0,
                                v_ml=0.0,
                                l_ppm=0.0,
                                l_ppm_bk=0.0,
                                porcentaje=0.0
                            )
                            print(f"Creada nueva muestra: {nueva_muestra.nombre}")

                for muestra in muestras:
                    for elemento in elementos:
                        resultado_existente = next(
                            (r for r in resultados if r.muestra == muestra.muestraMasificada and r.elemento == elemento and r.hoja_trabajo == muestra.hoja_trabajo),
                            None
                        )

                        if not resultado_existente:
                            nuevo_resultado = Resultado.objects.create(
                                elemento=elemento,
                                muestra=muestra.muestraMasificada,
                                hoja_trabajo=muestra.hoja_trabajo,
                                resultadoAnalisis=0.0,
                                fecha_emision=timezone.now()
                            )
                            print(f"Creado nuevo resultado para {muestra.nombre} con elemento {elemento.nombre}")

                return instance

        else:
            id_hdt_value = ''.join(random.choices('0123456789', k=5))
            instance = super().save(commit=False)
            odt = self.cleaned_data['odt']
            metodo_analisis = instance.MetodoAnalisis
            muestras = MuestraMasificada.objects.filter(odt=odt)
            
            hojas_trabajo = []
            count = 0
            
            elementos = metodo_analisis.elementos.all()
            
            for muestra in muestras:
                if count == 0:
                    hoja_trabajo = instance
                    hoja_trabajo.MuestraMasificada = muestra
                    hoja_trabajo.save() 
                else:
                    hoja_trabajo = HojaTrabajo(
                        odt=odt,
                        MetodoAnalisis=instance.MetodoAnalisis,
                        Tipo=instance.Tipo,
                        Duplicado=instance.Duplicado,
                        MuestraMasificada=muestra
                    )
                    hoja_trabajo.save()  
                hoja_trabajo.Estandar.set(self.cleaned_data['Estandar']) 
                hojas_trabajo.append(hoja_trabajo)
                count += 1

                hoja_trabajo_quimico = HojaTrabajoQuimico(
                    ID_HDT=id_hdt_value,
                    confirmar_balanza=False,
                    confirmar_Absorcion=False,
                    HojaTrabajo=hoja_trabajo
                )
                hoja_trabajo_quimico.save()

                for elemento in elementos:
                    muestra_instance = Muestra(
                        nombre=f"{elemento.nombre} - Muestra {1}",
                        proyecto=odt.Proyecto,
                        fecha_emision=timezone.now(),
                        elemento=elemento.nombre,
                        nbo=f"NBO-{1}", 
                        ident=f"ID-{1}",
                        indexCurv=1,
                        hoja_trabajo=hoja_trabajo,  
                        muestraMasificada=muestra,
                        t="M", 
                        peso_m=0.0, 
                        v_ml=0.0, 
                        l_ppm=0.0, 
                        l_ppm_bk=0.0,  
                        porcentaje=0.0  
                    )
                    muestra_instance.save() 

        if commit:
            instance.save()
        
        return instance
    

class HojaTrabajoQuimicoForm(forms.ModelForm):
    class Meta:
        model = HojaTrabajoQuimico
        fields = '__all__'

