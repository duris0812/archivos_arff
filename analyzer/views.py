import pandas as pd
from django.shortcuts import render
from .forms import ArffUploadForm
import io
import requests
from urllib.parse import urlparse

def analyze_arff_view(request):
    context = {'form': ArffUploadForm()}

    if request.method == 'POST':
        form = ArffUploadForm(request.POST, request.FILES)
        if form.is_valid():
            source = form.cleaned_data.get('source')
            file_content = None
            file_name = None

            try:
                if source == 'upload':
                    arff_file = request.FILES.get('arff_file')
                    if not arff_file:
                        context['error'] = 'No se seleccionó ningún archivo.'
                        return render(request, 'analyzer/analyze.html', context)
                    if not arff_file.name.lower().endswith('.arff'):
                        context['error'] = 'El archivo debe tener extensión .arff'
                        return render(request, 'analyzer/analyze.html', context)

                    file_name = arff_file.name
                    raw = arff_file.read()
                    try:
                        file_content = raw.decode('utf-8')
                    except Exception:
                        file_content = raw.decode('latin-1')

                elif source == 'github':
                    github_url = form.cleaned_data.get('github_url')
                    if not github_url:
                        context['error'] = 'Introduce la URL del archivo en GitHub.'
                        return render(request, 'analyzer/analyze.html', context)

                    parsed = urlparse(github_url)
                    if 'github.com' in parsed.netloc and '/blob/' in parsed.path:
                        raw_url = github_url.replace('https://github.com/', 'https://raw.githubusercontent.com/')
                        raw_url = raw_url.replace('/blob/', '/')
                    else:
                        raw_url = github_url

                    resp = requests.get(raw_url, timeout=15)
                    if resp.status_code != 200:
                        context['error'] = f'No se pudo descargar el archivo desde GitHub (status {resp.status_code}).'
                        return render(request, 'analyzer/analyze.html', context)

                    file_name = raw_url.split('/')[-1]
                    file_content = resp.text

                if file_content:
                    attribute_names = []
                    for line in file_content.split('\n'):
                        if line.strip().lower().startswith('@attribute'):
                            parts = line.split()
                            if len(parts) >= 2:
                                attribute_names.append(parts[1].strip("'\""))

                    df = pd.read_csv(
                        io.StringIO(file_content),
                        comment='@',
                        header=None,
                        na_values=['?']
                    )

                    if len(attribute_names) == len(df.columns):
                        df.columns = attribute_names
                    else:
                        df.columns = [f'Columna_{i+1}' for i in range(len(df.columns))]

                    df_html = df.to_html(
                        classes='table table-hover table-striped',
                        max_rows=100,
                        justify='left',
                        border=0,
                        na_rep='-'
                    )

                    context.update({
                        'df_html': df_html,
                        'file_name': file_name,
                        'num_rows': df.shape[0],
                        'num_cols': df.shape[1]
                    })

            except requests.RequestException as re:
                context['error'] = f'Error al descargar desde GitHub: {str(re)}'
            except Exception as e:
                context['error'] = f'Error al procesar el archivo: {str(e)}'
    
    return render(request, 'analyzer/analyze.html', context)