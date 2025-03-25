from django import forms
from .models import Auto, Rating, Cliente, Chofer

class AutoForm(forms.ModelForm):
    class Meta:
        model = Auto
        fields = ['patente', 'tipo', 'foto', 'anio_modelo', 'propietario', 'vtv', 'venc_patente', 'id_remiseria']


class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ['calificacion', 'comentario']
        widgets = {
            'calificacion': forms.RadioSelect(choices=[(i, f"{i} ★") for i in range(1, 6)]),
            'comentario': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Opcional: Deja un comentario sobre el chofer'}),
        }

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = [
            'nombre', 'apellido', 'username', 'telefono',
            'direccion', 'correo', 'password', 'tipo_cuenta',
            'id_localidad', 'fcm_token'
        ]
        widgets = {
            'password': forms.PasswordInput(),
        }

class ChoferForm(forms.ModelForm):
    id_cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.filter(tipo_cuenta=Cliente.CHOFER),
        label='Seleccionar Cliente',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Chofer
        fields = ['id_cliente', 'nombre', 'apellido', 'nro_tel', 'licencia', 'foto', 'mp_user_id']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
            'nro_tel': forms.TextInput(attrs={'class': 'form-control'}),
            'mp_user_id': forms.TextInput(attrs={'class': 'form-control'}),
        }

class ChoferFormAdmin(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Clientes tipo chofer
        disponibles = Cliente.objects.filter(tipo_cuenta=2)

        # Excluir los que ya están en la tabla Chofer
        usados = Chofer.objects.values_list('id_cliente', flat=True)
        self.fields['id_cliente'].queryset = disponibles.exclude(id_cliente__in=usados)

        # Mostrar nombre + apellido en el select
        self.fields['id_cliente'].label_from_instance = lambda obj: f"{obj.nombre} {obj.apellido} ({obj.telefono})"

    class Meta:
        model = Chofer
        fields = [
            'nombre', 'apellido', 'nro_tel', 'licencia', 'foto',
            'id_cliente', 'mp_user_id', 'id_remiseria'
        ]



from .models import Viaje

class ViajeForm(forms.ModelForm):
    class Meta:
        model = Viaje
        fields = [
            'id_cliente', 'dir_salida', 'dir_destino', 'hora', 'fecha',
            'id_precio', 'cod_tipo_pago', 'id_remiseria', 'inicio', 'fin',
            'patente', 'estado', 'id_chofer'
        ]


from .models import Remiseria
from django import forms

class RemiseriaForm(forms.ModelForm):
    class Meta:
        model = Remiseria
        fields = ['nombre', 'telefono', 'password', 'foto', 'esta_abierta']


from .models import Localidad
from django import forms

class LocalidadForm(forms.ModelForm):
    class Meta:
        model = Localidad
        fields = ['nombre']
