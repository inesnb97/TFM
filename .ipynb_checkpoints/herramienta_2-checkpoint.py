import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import folium_static
import plotly.express as px
import os

# Cargar el dataset principal
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

# Archivo para almacenar el historial
HISTORICAL_FILE = 'historico_busquedas.csv'

# Crear el archivo si no existe
if not os.path.exists(HISTORICAL_FILE):
    pd.DataFrame(columns=['Edad', 'Ingresos', 'Zona', 'Precio medio/m²', 'Valor medio de compra', 
                          'Proyección 5 años (%)']).to_csv(HISTORICAL_FILE, index=False)

# Título principal
st.markdown("<h1 style='text-align: center; color: #EE6C4D;'>Herramienta de Análisis de Vivienda</h1>", unsafe_allow_html=True)

# Solicitar datos del usuario
st.sidebar.header("Introduce tus datos")
edad = st.sidebar.number_input("¿Cuál es tu edad?", min_value=18, max_value=100, step=1)
ingresos = st.sidebar.number_input("¿Cuáles son tus ingresos anuales (en euros)?", min_value=1000, step=100)
zona_preferencia = st.sidebar.selectbox("Selecciona tu zona o localidad preferida:", df['Ciudad'].unique())

# Filtrar los datos según la zona seleccionada
zona_df = df[df['Ciudad'] == zona_preferencia]

# Cargar datos geoespaciales
try:
    gdf = gpd.read_file("georef-spain-municipio.geojson")
except:
    st.error("Error al cargar el archivo GeoJSON. Asegúrate de que el archivo 'georef-spain-municipio.geojson' esté disponible.")
    st.stop()

# Función para asignar colores según los criterios de viabilidad
def asignar_color(criterio):
    if criterio == 1:
        return 'green'
    elif criterio == 2:
        return 'orange'
    elif criterio == 3:
        return 'red'
    return 'gray'

# Función para calcular la hipoteca mensual (simplificada)
def calcular_hipoteca(precio, tasa_interes, plazo_anos):
    tasa_mensual = tasa_interes / 12 / 100
    num_pagos = plazo_anos * 12
    pago_mensual = precio * tasa_mensual / (1 - (1 + tasa_mensual) ** -num_pagos)
    return pago_mensual

# Función para determinar la viabilidad en base a los ingresos
def determinar_viabilidad(hipoteca_mensual, ingresos):
    porcentaje_ingresos = (hipoteca_mensual * 12) / ingresos * 100
    if porcentaje_ingresos < 30:
        return 1  # Verde: Viable
    elif porcentaje_ingresos < 50:
        return 2  # Amarillo: Moderadamente viable
    else:
        return 3  # Rojo: No viable

# Tasa de interés y plazo para el cálculo de la hipoteca
TASA_INTERES = 3.5  # Tasa de interés anual
PLAZO_ANIOS = 30  # Plazo en años

if not zona_df.empty:
    # Pestañas para estructurar la visualización
    tab1, tab2, tab3, tab4 = st.tabs(["Indicadores", "Gráficos", "Mapa de Zonas", "Historial de búsquedas"])

    # Tab 1: Indicadores
    with tab1:
        st.subheader(f"Indicadores clave para {zona_preferencia}")

        # Usar columnas para organizar indicadores
        col1, col2, col3 = st.columns(3)

        with col1:
            precio_m2 = zona_df['Precio medio/m²'].mean()
            st.metric(label="Precio medio/m²", value=f"{precio_m2:.2f} €/m²")

        with col2:
            valor_compra = zona_df['Valor medio de compra'].mean()
            st.metric(label="Valor medio de compra", value=f"{valor_compra:.2f} €")

        with col3:
            proyeccion = zona_df['Proyección 5 años (%)'].mean()
            st.metric(label="Proyección 5 años", value=f"{proyeccion:.2f} %")

        # Registrar la búsqueda en el historial
        nuevo_registro = pd.DataFrame([{
            'Edad': edad,
            'Ingresos': ingresos,
            'Zona': zona_preferencia,
            'Precio medio/m²': precio_m2,
            'Valor medio de compra': valor_compra,
            'Proyección 5 años (%)': proyeccion
        }])
        historico = pd.read_csv(HISTORICAL_FILE)
        historico = pd.concat([historico, nuevo_registro], ignore_index=True)
        historico.to_csv(HISTORICAL_FILE, index=False)

    # Tab 2: Gráficos
    with tab2:
        st.subheader("Tendencias de precios")

        tendencia_precios = zona_df.groupby(['Año', 'Tipo de vivienda']).agg({'Precio medio/m²': 'mean'}).reset_index()
        fig_line = px.line(
            tendencia_precios,
            x='Año',
            y='Precio medio/m²',
            color='Tipo de vivienda',
            title=f"Tendencia de precios en {zona_preferencia} (2014-2024)",
            markers=True
        )
        st.plotly_chart(fig_line, use_container_width=True)

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

    # Tab 3: Mapa de Zonas
    with tab3:
        st.subheader("Mapa de Viabilidad de Compra")
        mapa_sevilla = folium.Map(location=[37.3886, -5.9823], zoom_start=10)

        for _, row in gdf.iterrows():
            try:
                zona_nombre = row['mun_name']
                geometry = row['geometry']

                if geometry.is_valid:
                    zona_precio = df[df['Ciudad'] == zona_nombre]['Valor medio de compra'].mean()
                    hipoteca_mensual = calcular_hipoteca(zona_precio, TASA_INTERES, PLAZO_ANIOS)
                    criterio_viabilidad = determinar_viabilidad(hipoteca_mensual, ingresos)

                    folium.GeoJson(
                        geometry,
                        style_function=lambda x, criterio=criterio_viabilidad: {
                            'fillColor': asignar_color(criterio),
                            'color': 'black',
                            'weight': 1,
                            'fillOpacity': 0.6,
                        },
                        tooltip=f"{zona_nombre} - Viabilidad: {criterio_viabilidad}"
                    ).add_to(mapa_sevilla)
            except KeyError:
                st.warning(f"No se pudo procesar la zona: {zona_nombre}")

        folium_static(mapa_sevilla)

    # Tab 4: Historial de búsquedas
    with tab4:
        st.subheader("Historial de búsquedas")
        historico = pd.read_csv(HISTORICAL_FILE)
        st.dataframe(historico)
