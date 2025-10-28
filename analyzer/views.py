import pandas as pd
from django.shortcuts import render
from .forms import ArffUploadForm
import io

def analyze_arff_view(request):
    context = {'form': ArffUploadForm()}

    if request.method == 'POST':
        form = ArffUploadForm(request.POST, request.FILES)
        if form.is_valid():
            arff_file = request.FILES['arff_file']
            
            # Verificar la extensión del archivo
            if not arff_file.name.lower().endswith('.arff'):
                context['error'] = "El archivo debe tener extensión .arff"
                return render(request, 'analyzer/analyze.html', context)
            
            try:
                # Leer el contenido del archivo en memoria
                file_content = arff_file.read().decode('utf-8')
                
                # Extraer los nombres de las columnas de los metadatos @attribute
                attribute_names = []
                for line in file_content.split('\n'):
                    if line.lower().startswith('@attribute'):
                        # Extraer el nombre del atributo
                        attr_name = line.split()[1]
                        attribute_names.append(attr_name)
                
                # Resetear el puntero del archivo para leerlo de nuevo
                arff_file.seek(0)
                
                # Leer el archivo usando pandas
                df = pd.read_csv(
                    io.StringIO(file_content),
                    comment='@',
                    header=None,
                    na_values=['?']  # Manejar valores faltantes marcados como ?
                )
                
                # Asignar los nombres de columnas extraídos
                if len(attribute_names) == len(df.columns):
                    df.columns = attribute_names
                else:
                    # Si algo salió mal, usar nombres genéricos
                    df.columns = [f'Atributo_{i+1}' for i in range(len(df.columns))]

                # Convertir el DataFrame a HTML para mostrarlo
                df_html = df.to_html(
                    classes='table table-striped table-hover table-bordered', 
                    max_rows=100,
                    justify='left',
                    border=0,
                    na_rep='N/A',  # Representación de valores faltantes
                    float_format=lambda x: '{:.3f}'.format(x) if pd.notnull(x) else 'N/A'
                )
                
                # Agregar información al contexto
                context.update({
                    'df_html': df_html,
                    'file_name': arff_file.name,
                    'shape': df.shape,
                    'num_na': df.isna().sum().sum(),  # Total de valores faltantes
                    'memory_usage': df.memory_usage().sum() / 1024 / 1024  # Uso de memoria en MB
                })

            except UnicodeDecodeError:
                context['error'] = "Error de codificación: El archivo debe estar en formato UTF-8"
            except pd.errors.EmptyDataError:
                context['error'] = "El archivo está vacío o no contiene datos válidos"
            except Exception as e:
                context['error'] = f"Error al procesar el archivo: {str(e)}"
    
    return render(request, 'analyzer/analyze.html', context)