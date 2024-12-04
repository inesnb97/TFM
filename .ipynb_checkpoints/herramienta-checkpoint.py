import pandas as pd
import folium
import streamlit as st

# Leer el dataset con los datos de precios
dataset_path = 'datos_vivienda.csv'  # Cambia esta ruta por la ubicación de tu archivo
df = pd.read_csv(dataset_path, sep=';')  # Ajustar delimitador según el formato del archivo

# Asegurarse de que las columnas de precios sean cadenas y luego convertir a float
df['Precio medio/m²'] = df['Precio medio/m²'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.').astype(float)
df['Valor medio de compra'] = df['Valor medio de compra'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.').astype(float)

# Limpiar las columnas numéricas que puedan tener valores no válidos
df['Latitud'] = df['Latitud'].astype(str).str.replace(',', '.').astype(float)
df['Longitud'] = df['Longitud'].astype(str).str.replace(',', '.').astype(float)

# Calcular la accesibilidad en función de los ingresos del usuario
ingresos = st.number_input("¿Cuáles son tus ingresos anuales (en euros)?", min_value=0, value=30000)
df['Accesibilidad'] = ingresos / df['Valor medio de compra'] * 100  # Porcentaje de accesibilidad
df['Nivel Accesibilidad'] = pd.cut(
    df['Accesibilidad'],
    bins=[0, 50, 80, 100],
    labels=['Baja', 'Media', 'Alta']
)

# Crear el mapa centrado en Sevilla
mapa = folium.Map(location=[37.3886, -5.9823], zoom_start=11)

# Añadir los puntos de cada zona con colores según la accesibilidad
for index, row in df.iterrows():
    # Definir el color según el nivel de accesibilidad
    if row['Nivel Accesibilidad'] == 'Alta':
        color = 'green'
    elif row['Nivel Accesibilidad'] == 'Media':
        color = 'yellow'
    else:
        color = 'red'
    
    # Añadir los puntos al mapa
    folium.CircleMarker(
        location=[row['Latitud'], row['Longitud']],
        radius=8,
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.6,
        popup=f"{row['Ciudad']} - {row['Nivel Accesibilidad']} (Accesibilidad: {row['Accesibilidad']:.2f}%)"
    ).add_to(mapa)

# Mostrar el mapa en Streamlit
st.write("### Mapa de accesibilidad de zonas en Sevilla")
st.components.v1.html(mapa._repr_html_(), height=600)
