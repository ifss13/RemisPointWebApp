from django import forms
from .models import Auto

class AutoForm(forms.ModelForm):
    class Meta:
        model = Auto
        fields = ['patente', 'tipo', 'foto', 'anio_modelo', 'propietario', 'vtv', 'venc_patente', 'id_remiseria']
