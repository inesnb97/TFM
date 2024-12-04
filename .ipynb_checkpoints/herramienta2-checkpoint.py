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

# Título principal
st.markdown("<h1 style='text-align: center; color: #EE6C4D;'>Herramienta de Análisis de Vivienda</h1>", unsafe_allow_html=True)

# Solicitar datos del usuario
st.sidebar.header("Introduce tus datos")
edad = st.sidebar.number_input("¿Cuál es tu edad?", min_value=18, max_value=100, step=1)
ingresos = st.sidebar.number_input("¿Cuáles son tus ingresos anuales (en euros)?", min_value=1000, step=100)
zona_preferencia = st.sidebar.selectbox("Selecciona tu zona o localidad preferida:", df['Ciudad'].unique())

# Filtrar los datos según la zona seleccionada
zona_df = df[df['Ciudad'] == zona_preferencia]

if not zona_df.empty:
    # Pestañas para estructurar la visualización
    tab1, tab2, tab3 = st.tabs(["Indicadores", "Gráficos", "Mapa Interactivo"])

    # Tab 1: Indicadores
    with tab1:
        st.subheader(f"Indicadores clave para {zona_preferencia}")

        # Usar columnas para organizar indicadores
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(label="Precio medio/m²", value=f"{zona_df['Precio medio/m²'].mean():.2f} €/m²")

        with col2:
            st.metric(label="Valor medio de compra", value=f"{zona_df['Valor medio de compra'].mean():.2f} €")

        with col3:
            st.metric(label="Proyección 5 años", value=f"{zona_df['Proyección 5 años (%)'].mean():.2f} %")

        # Indicadores adicionales por tipo de vivienda
        st.subheader("Detalles por tipo de vivienda")
        for tipo in zona_df['Tipo de vivienda'].unique():
            tipo_df = zona_df[zona_df['Tipo de vivienda'] == tipo]
            st.write(f"**{tipo}**:")
            st.write(f"- Precio medio/m²: {tipo_df['Precio medio/m²'].mean():.2f} €/m²")
            st.write(f"- Valor medio de compra: {tipo_df['Valor medio de compra'].mean():.2f} €")
            st.write(f"- Variación anual: {tipo_df['Variación anual (%)'].mean():.2f} %")

    # Tab 2: Gráficos
    with tab2:
        st.subheader("Tendencias de precios")

        # Gráfico de líneas por tipo de vivienda
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

    # Tab 3: Mapa interactivo
    with tab3:
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

    # Recomendaciones personalizadas
    st.subheader("Recomendación personalizada")
    if edad < 30 and ingresos < 20000:
        st.write("Se recomienda explorar opciones más asequibles y verificar programas de asistencia para jóvenes.")
    elif edad >= 30 and ingresos >= 20000:
        st.write("Hay opciones disponibles en zonas con precios intermedios o superiores.")
    else:
        st.write("Analiza diferentes zonas según tu presupuesto y preferencias.")
else:
    st.write(f"No se encontraron datos para la zona '{zona_preferencia}'.")
