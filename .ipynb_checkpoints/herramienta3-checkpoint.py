import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import plotly.express as px

# Cargar el dataset
df = pd.read_csv('datos_vivienda.csv', sep=';')

# Limpiar los nombres de las columnas
df.columns = df.columns.str.strip()

# Convertir columnas numéricas relevantes (manejar errores y comas como separador decimal)
df['Precio medio/m²'] = pd.to_numeric(df['Precio medio/m²'], errors='coerce')
df['Valor medio de compra'] = pd.to_numeric(df['Valor medio de compra'], errors='coerce')
df['Variación anual (%)'] = pd.to_numeric(df['Variación anual (%)'], errors='coerce')
df['Proyección 5 años (%)'] = pd.to_numeric(df['Proyección 5 años (%)'], errors='coerce')
df['Latitud'] = df['Latitud'].astype(str).str.replace(',', '.').astype(float)
df['Longitud'] = df['Longitud'].astype(str).str.replace(',', '.').astype(float)

# Verificar columnas necesarias
required_columns = ['Ciudad', 'Año', 'Precio medio/m²', 'Valor medio de compra', 
                    'Variación anual (%)', 'Proyección 5 años (%)', 'Tipo de vivienda', 'Latitud', 'Longitud']
for column in required_columns:
    if column not in df.columns:
        st.error(f"El dataset no contiene la columna requerida: {column}. Por favor, verifica el archivo.")
        st.stop()

# Título de la herramienta
st.title("Herramienta de Análisis de Vivienda Asequible")

# Solicitar datos del usuario
edad = st.number_input("¿Cuál es tu edad?", min_value=18, max_value=100, step=1)
ingresos = st.number_input("¿Cuáles son tus ingresos anuales (en euros)?", min_value=1000, step=100)
zona_preferencia = st.selectbox("Selecciona tu zona o localidad preferida:", df['Ciudad'].unique())

# Filtrar los datos según la zona seleccionada
zona_df = df[df['Ciudad'] == zona_preferencia]

if not zona_df.empty:
    # Mostrar información general
    st.subheader(f"Datos generales para {zona_preferencia}")

    # Agrupación por tipo de vivienda
    for tipo in zona_df['Tipo de vivienda'].unique():
        tipo_df = zona_df[zona_df['Tipo de vivienda'] == tipo]

        precio_m2 = tipo_df['Precio medio/m²'].mean()
        valor_compra = tipo_df['Valor medio de compra'].mean()
        variacion_anual = tipo_df['Variación anual (%)'].mean()
        proyeccion_5 = tipo_df['Proyección 5 años (%)'].mean()

        st.write(f"**Tipo de vivienda: {tipo}**")
        st.write(f"• Precio medio/m²: {precio_m2:.2f} €/m²")
        st.write(f"• Valor medio de compra: {valor_compra:.2f} €")
        st.write(f"• Variación anual: {variacion_anual:.2f} %")
        st.write(f"• Proyección a 5 años: {proyeccion_5:.2f} %")

    # Crear mapa interactivo
    st.subheader(f"Mapa interactivo de {zona_preferencia}")
    mapa = folium.Map(location=[zona_df['Latitud'].mean(), zona_df['Longitud'].mean()], zoom_start=12)

    for _, row in zona_df.iterrows():
        popup_text = f"Tipo: {row['Tipo de vivienda']}<br>Precio/m²: {row['Precio medio/m²']}<br>Valor: {row['Valor medio de compra']}"
        folium.Marker(
            location=[row['Latitud'], row['Longitud']],
            popup=popup_text,
            icon=folium.Icon(color='green' if row['Variación anual (%)'] > 0 else 'red')
        ).add_to(mapa)

    folium_static(mapa)

    # Gráficas dinámicas: Tendencias de precios
    st.subheader("Tendencias de precios")

    # Filtrar datos para la tendencia de precios en la zona seleccionada
    tendencia_precios = zona_df.groupby(['Año', 'Tipo de vivienda']).agg({'Precio medio/m²': 'mean'}).reset_index()

    # Gráfico de líneas por tipo de vivienda
    fig_line = px.line(
        tendencia_precios,
        x='Año',
        y='Precio medio/m²',
        color='Tipo de vivienda',
        title=f"Tendencia de precios en {zona_preferencia} (2014-2024)",
        markers=True
    )
    st.plotly_chart(fig_line, use_container_width=True)

    # Gráfico de distribución de precios
    st.subheader("Distribución de precios por tipo de vivienda")
    fig_hist = px.histogram(
        zona_df,
        x='Precio medio/m²',
        color='Tipo de vivienda',
        nbins=30,
        title="Distribución de precios",
        labels={'Precio medio/m²': 'Precio medio (€/m²)'}
    )
    st.plotly_chart(fig_hist, use_container_width=True)
else:
    st.write(f"No se encontraron datos para la zona '{zona_preferencia}'.")

# Recomendaciones basadas en datos
st.subheader("Recomendación personalizada")
if edad < 30 and ingresos < 20000:
    st.write("Se recomienda explorar opciones más asequibles y verificar programas de asistencia para jóvenes.")
elif edad >= 30 and ingresos >= 20000:
    st.write("Hay opciones disponibles en zonas con precios intermedios o superiores.")
else:
    st.write("Analiza diferentes zonas según tu presupuesto y preferencias.")
