from django import forms

class ArffUploadForm(forms.Form):
    arff_file = forms.FileField(
        label="Selecciona tu archivo ARFF",
        help_text="Archivos .arff en formato Weka",
        widget=forms.ClearableFileInput(
            attrs={
                'class': 'form-control',
                'accept': '.arff',
                'data-bs-toggle': 'tooltip',
                'title': 'Selecciona un archivo con extensión .arff'
            }
        )
    )