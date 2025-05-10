from flask import Flask, request, jsonify
import os
import pandas as pd
import numpy as np
from models.analist import analizar_grafico, analizar_datos, generar_analisis
from utils.appResponse import format_response

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/analizar', methods=['POST'])
def analizar():
    imagen = request.files.get('imagen')
    datos_csv = request.files.get('datos')
    datos_json = request.get_json(silent=True)
    
    # Obtener el prompt personalizado si existe
    prompt_personalizado = None
    if datos_json and 'prompt' in datos_json:
        prompt_personalizado = datos_json.pop('prompt')  # Extraer el prompt y eliminarlo de los datos
    
    # Guardar los datos de entrada para incluirlos en la respuesta
    input_data = {
        "tiene_imagen": imagen is not None,
        "tiene_csv": datos_csv is not None,
        "tiene_json": datos_json is not None,
        "tiene_prompt_personalizado": prompt_personalizado is not None
    }
    
    if datos_json:
        input_data["datos_json"] = datos_json

    texto_grafico = []
    resumen_datos = ""
    analisis_avanzado = ""

    # Procesar gráfico si se incluye
    if imagen:
        imagen_path = os.path.join(app.config['UPLOAD_FOLDER'], imagen.filename)
        imagen.save(imagen_path)
        texto_grafico = analizar_grafico(imagen_path)

    # Procesar datos CSV si se incluye
    if datos_csv:
        datos_path = os.path.join(app.config['UPLOAD_FOLDER'], datos_csv.filename)
        datos_csv.save(datos_path)
        resumen_datos = analizar_datos(datos_path)
        
        # Análisis más profundo del CSV
        df = pd.read_csv(datos_path)
        analisis_avanzado = realizar_analisis_avanzado(df)

    # Procesar datos JSON si se incluye
    # Procesar datos JSON si se incluye
    if datos_json and not datos_csv:
        df = pd.DataFrame(datos_json)
        
        # Crear resumen en formato de texto, no en tabla
        resumen = []
        for columna in df.columns:
            try:
                # Verificar si la columna contiene diccionarios o listas
                if df[columna].apply(lambda x: isinstance(x, (dict, list))).any():
                    resumen.append(f"La columna '{columna}' contiene valores complejos (diccionarios o listas).")
                    muestra = str(df[columna].iloc[0])[:50] + "..." if len(str(df[columna].iloc[0])) > 50 else str(df[columna].iloc[0])
                    resumen.append(f"Ejemplo de valor: {muestra}")
                else:
                    # Procesamiento normal para tipos simples
                    valores_unicos = df[columna].nunique()
                    valor_comun = df[columna].mode()[0] if not df[columna].mode().empty else "N/A"
                    frecuencia = df[columna].value_counts().iloc[0] if not df[columna].value_counts().empty else 0
                    
                    resumen.append(f"La columna '{columna}' tiene {df[columna].count()} valores, con {valores_unicos} valores únicos.")
                    resumen.append(f"El valor más común es '{valor_comun}' que aparece {frecuencia} veces.")
            except TypeError:
                # Capturar cualquier otro error de tipo relacionado
                resumen.append(f"La columna '{columna}' contiene datos que no pueden ser analizados de forma estándar.")
        
        resumen_datos = "\n".join(resumen)
        
        # Realizar análisis más profundo de los datos JSON
        analisis_avanzado = realizar_analisis_avanzado(df)

    if not imagen and not (datos_csv or datos_json):
        return format_response(
            status_code=400,
            status="error",
            message="Se requiere al menos una imagen o datos",
            input_data=input_data
        )

    # Construir el prompt para el análisis
    if prompt_personalizado:
        # Usar el prompt personalizado del usuario
        entrada = prompt_personalizado
    else:
        # Usar el prompt predeterminado mejorado
        entrada = f"Análisis de gráfico: {', '.join(texto_grafico)}.\n" if texto_grafico else ""
        entrada += f"Análisis básico de datos: {resumen_datos}\n"
        entrada += f"Análisis avanzado: {analisis_avanzado}\n\n"
        entrada += "Basándote en estos datos, proporciona una conclusión clara, concisa y significativa, destacando patrones importantes y posibles recomendaciones:"
    
    analisis_completo = generar_analisis(entrada)
    
    # Extraer solo la parte relevante para una respuesta más limpia
    try:
        if prompt_personalizado:
            analisis_final = analisis_completo
        else:
            indice = analisis_completo.find("Basándote en estos datos")
            if indice > -1:
                pos_fin = analisis_completo.find(":", indice) + 1
                analisis_final = analisis_completo[pos_fin:]
            else:
                analisis_final = analisis_completo
    except:
        analisis_final = analisis_completo

    resultado = {
        "grafico_texto": texto_grafico,
        "resumen_datos": resumen_datos,
        "analisis_avanzado": analisis_avanzado,
        "prompt_utilizado": prompt_personalizado if prompt_personalizado else "Prompt predeterminado",
        "analisis_ia": analisis_final.strip()
    }

    return format_response(
        data=resultado,
        input_data=input_data,
        message="Análisis completado exitosamente"
    )
    
def realizar_analisis_avanzado(df):
    """Realiza un análisis más profundo de los datos proporcionados"""
    analisis = []
    
    # Total de registros
    analisis.append(f"Total de registros analizados: {len(df)}")
    
    # Análisis por columna con tipos de datos
    for columna in df.columns:
        # Detectar tipo de datos real de la columna (incluyendo tipos complejos)
        if df[columna].apply(lambda x: isinstance(x, dict)).any():
            tipo_dato = "diccionario"
        elif df[columna].apply(lambda x: isinstance(x, list)).any():
            tipo_dato = "lista"
        else:
            tipo_dato = str(df[columna].dtype)
        
        analisis.append(f"La columna '{columna}' es de tipo {tipo_dato}")
    
    # El resto del análisis solo para columnas de tipos simples
    # Análisis de valores faltantes
    try:
        valores_faltantes = df.isnull().sum()
        columnas_con_nulos = valores_faltantes[valores_faltantes > 0]
        if not columnas_con_nulos.empty:
            for col, nulos in columnas_con_nulos.items():
                porcentaje = (nulos / len(df)) * 100
                analisis.append(f"La columna '{col}' tiene {nulos} valores faltantes ({porcentaje:.1f}%)")
        else:
            analisis.append("No hay valores faltantes en los datos")
    except:
        analisis.append("No se pudieron analizar valores faltantes por la presencia de tipos de datos complejos")
    
    # Intentar análisis de correlaciones para datos numéricos
    try:
        columnas_numericas = df.select_dtypes(include=['number']).columns
        if len(columnas_numericas) >= 2:
            analisis.append("\nCorrelaciones entre columnas numéricas:")
            corr = df[columnas_numericas].corr()
            for i in range(len(columnas_numericas)):
                for j in range(i+1, len(columnas_numericas)):
                    col1, col2 = columnas_numericas[i], columnas_numericas[j]
                    correlacion = corr.loc[col1, col2]
                    if abs(correlacion) > 0.5:  # Solo mostrar correlaciones significativas
                        fuerza = "fuerte" if abs(correlacion) > 0.7 else "moderada"
                        direccion = "positiva" if correlacion > 0 else "negativa"
                        analisis.append(f"Hay una correlación {fuerza} {direccion} ({correlacion:.2f}) entre '{col1}' y '{col2}'")
    except:
        pass  # Si falla el análisis de correlación, simplemente lo omitimos
    
    return "\n".join(analisis)
if __name__ == '__main__':
    app.run(debug=True)