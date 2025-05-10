import pandas as pd
import easyocr
from transformers import pipeline


reader = easyocr.Reader(['en'], gpu=False)
generador = pipeline("text-generation", model="gpt2")

def analizar_grafico(imagen_path):
    texto = reader.readtext(imagen_path, detail=0)
    return texto

def analizar_datos(csv_path):
    df = pd.read_csv(csv_path)
    # Obtener estadísticas descriptivas
    stats = df.describe(include='all')
    
    # Crear un resumen en texto plano más legible
    resumen = []
    for columna in df.columns:
        valores_unicos = df[columna].nunique()
        valor_comun = df[columna].mode()[0] if not df[columna].mode().empty else "N/A"
        frecuencia = df[columna].value_counts().iloc[0] if not df[columna].value_counts().empty else 0
        
        resumen.append(f"La columna '{columna}' tiene {df[columna].count()} valores, con {valores_unicos} valores únicos.")
        resumen.append(f"El valor más común es '{valor_comun}' que aparece {frecuencia} veces.")
    
    return "\n".join(resumen)

def generar_analisis(texto_entrada):
    salida = generador(texto_entrada, max_new_tokens=150, num_return_sequences=1, truncation=True)
    return salida[0]["generated_text"]