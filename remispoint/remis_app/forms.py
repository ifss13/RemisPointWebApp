from django import forms
from .models import Auto, Rating

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