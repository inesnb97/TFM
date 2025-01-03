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
tipo_vivienda_preferencia = st.sidebar.selectbox(
    "Selecciona tu tipo de vivienda preferida:",
    ["Nueva", "Segunda mano"]
)

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

# Función para formatear números con separadores personalizados
def formatear_numero(numero):
    return f"{numero:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# Tab 1: Indicadores
with tab1:
    st.subheader(f"Indicadores clave para {zona_preferencia}")

    # Usar columnas para organizar indicadores
    col1, col2, col3 = st.columns(3)

    with col1:
        precio_m2 = zona_df['Precio medio/m²'].mean()
        st.metric(label="Precio medio/m²", value=f"{precio_m2:,.2f} €/m²".replace(",", "X").replace(".", ",").replace("X", "."))

    with col2:
        valor_compra = zona_df['Valor medio de compra'].mean()
        st.metric(label="Valor medio de compra", value=f"{valor_compra:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."))

    with col3:
        proyeccion = zona_df['Proyección 5 años (%)'].mean()
        st.metric(label="Proyección 5 años", value=f"{proyeccion:,.2f} %".replace(",", "X").replace(".", ",").replace("X", "."))

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

    # Nuevo gráfico comparativo: Evolución del precio por m²
    st.subheader(f"Evolución del precio para viviendas '{tipo_vivienda_preferencia}' en todas las zonas")
    filtro_tipo_vivienda = df[df['Tipo de vivienda'] == tipo_vivienda_preferencia]
    tendencia_todas_zonas = filtro_tipo_vivienda.groupby(['Año', 'Ciudad']).agg({'Precio medio/m²': 'mean'}).reset_index()

    fig_comparativo = px.line(
        tendencia_todas_zonas,
        x='Año',
        y='Precio medio/m²',
        color='Ciudad',
        title="Evolución del precio por m² en todas las zonas",
        labels={
            "Precio medio/m²": "Precio medio (€/m²)",
            "Año": "Año",
            "Ciudad": "Zona"
        },
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    fig_comparativo.update_traces(mode="lines+markers")
    fig_comparativo.update_layout(
        yaxis_tickformat=".2f",
        yaxis_title="Precio medio (€/m²)",
        xaxis_title="Año",
        legend_title="Zonas"
    )

    st.plotly_chart(fig_comparativo, use_container_width=True)


# Tab 2: Gráficos
with tab2:
    st.subheader("Tendencias de precios")

    # Gráfico de línea para la tendencia de precios
    tendencia_precios = zona_df.groupby(['Año', 'Tipo de vivienda']).agg({'Precio medio/m²': 'mean'}).reset_index()
    fig_line = px.line(
        tendencia_precios,
        x='Año',
        y='Precio medio/m²',
        color='Tipo de vivienda',
        title=f"Tendencia de precios en {zona_preferencia} (2014-2024)",
        markers=True,
        color_discrete_sequence=["#3D5A80", "#EE6C4D"]
    )
    fig_line.update_traces(mode="lines+markers")
    st.plotly_chart(fig_line, use_container_width=True)

    st.subheader("Distribución de precios por tipo de vivienda")

    # Gráfico de caja (boxplot) para la distribución de precios por tipo de vivienda
    fig_boxplot = px.box(
        zona_df,
        x='Tipo de vivienda',
        y='Precio medio/m²',
        color='Tipo de vivienda',
        title="Distribución de precios por tipo de vivienda",
        labels={
            "Precio medio/m²": "Precio medio (€/m²)",
            "Tipo de vivienda": "Tipo de vivienda"
        },
        color_discrete_sequence=["#3D5A80", "#EE6C4D"]
    )
    fig_boxplot.update_layout(
        showlegend=False,
        yaxis_tickformat=".2f",
        yaxis_title="Precio medio (€/m²)",
        xaxis_title=""
    )

    st.plotly_chart(fig_boxplot, use_container_width=True)


# Tab 3: Mapa de Zonas
with tab3:
    st.subheader("Mapa de Viabilidad de Compra")

    # Crear el mapa
    mapa_sevilla = folium.Map(location=[37.3886, -5.9823], zoom_start=10)

    # Añadir zonas con colores según viabilidad
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

    # Añadir leyenda personalizada
    legend_html = """
    <div style="
        position: fixed;
        bottom: 50px;
        left: 50px;
        width: 250px;
        height: 140px;
        background-color: white;
        border: 2px solid black;
        z-index: 1000;
        padding: 10px;
        font-size: 14px;
    ">
        <b>Viabilidad de compra:</b><br>
        <i style="background: green; width: 15px; height: 15px; display: inline-block; margin-right: 5px;"></i>
        Viable (&lt; 30% de ingresos)<br>
        <i style="background: orange; width: 15px; height: 15px; display: inline-block; margin-right: 5px;"></i>
        Moderadamente viable (30%-50% de ingresos)<br>
        <i style="background: red; width: 15px; height: 15px; display: inline-block; margin-right: 5px;"></i>
        No viable (&gt; 50% de ingresos)<br>
        <i style="background: gray; width: 15px; height: 15px; display: inline-block; margin-right: 5px;"></i>
        Sin datos disponibles<br>
    </div>
    """
    mapa_sevilla.get_root().html.add_child(folium.Element(legend_html))

    # Mostrar el mapa en Streamlit
    folium_static(mapa_sevilla)

    # Añadir descripción de los criterios
    st.markdown("""
        **Criterios de viabilidad:**  
        - 🟢 **Viable:** El coste de la hipoteca mensual representa menos del 30% de los ingresos anuales.  
        - 🟠 **Moderadamente viable:** El coste de la hipoteca mensual está entre el 30% y el 50% de los ingresos anuales.  
        - 🔴 **No viable:** El coste de la hipoteca mensual supera el 50% de los ingresos anuales.  
        - ⚪ **Sin datos:** No se dispone de información suficiente para calcular la viabilidad.
    """)


# Tab 4: Historial de búsquedas con recomendaciones mejoradas
with tab4:

    # Cargar el historial
    historico = pd.read_csv(HISTORICAL_FILE)

    if historico.empty:
        st.info("No hay búsquedas registradas. Realiza tu primera búsqueda para ver recomendaciones.")
    else:
        # Mostrar el historial de búsquedas
        st.markdown("### Historial de búsquedas")
        st.dataframe(historico)

        # Generar recomendaciones personalizadas con puntuación compuesta
        st.markdown("### Recomendaciones personalizadas basadas en múltiples factores")

        # Filtrar el dataset según el tipo de vivienda seleccionado
        df_filtrado = df[df['Tipo de vivienda'] == tipo_vivienda_preferencia]

        # Calcular el promedio de precio medio/m² para usar como referencia
        promedio_precio_m2 = df['Precio medio/m²'].mean()

        # Crear un nuevo DataFrame para las recomendaciones
        recomendaciones = []
        for _, row in df_filtrado.iterrows():
            precio = row['Valor medio de compra']
            proyeccion = row['Proyección 5 años (%)']
            precio_m2 = row['Precio medio/m²']

            if pd.isna(precio) or precio <= 0 or pd.isna(proyeccion) or pd.isna(precio_m2):
                continue  # Ignorar registros con valores faltantes o inválidos

            # Calcular viabilidad financiera
            hipoteca_mensual = calcular_hipoteca(precio, TASA_INTERES, PLAZO_ANIOS)
            porcentaje_ingresos = (hipoteca_mensual * 12) / ingresos * 100

            # Calcular puntuaciones individuales
            puntuacion_viabilidad = max(0, 100 - porcentaje_ingresos)  # Menor porcentaje es mejor
            puntuacion_proyeccion = max(0, proyeccion)  # Mayor proyección es mejor
            puntuacion_accesibilidad = max(0, 100 - abs(precio_m2 - promedio_precio_m2))  # Más cerca del promedio es mejor

            # Ponderar las puntuaciones
            puntuacion_total = (
                0.4 * puntuacion_viabilidad +
                0.3 * puntuacion_proyeccion +
                0.3 * puntuacion_accesibilidad
            )

            recomendaciones.append({
                'Ciudad': row['Ciudad'],
                'Tipo de vivienda': row['Tipo de vivienda'],
                'Precio medio/m²': precio_m2,
                'Valor medio de compra': precio,
                'Proyección 5 años (%)': proyeccion,
                'Hipoteca mensual': hipoteca_mensual,
                'Porcentaje de ingresos': porcentaje_ingresos,
                'Puntuación total': puntuacion_total
            })

        # Convertir las recomendaciones en un DataFrame y ordenarlas por puntuación total
        recomendaciones_df = pd.DataFrame(recomendaciones)
        recomendaciones_df = recomendaciones_df.sort_values(by='Puntuación total', ascending=False)

        if recomendaciones_df.empty:
            st.info("No se encontraron recomendaciones viables basadas en tus ingresos y preferencia de vivienda.")
        else:
            # Mostrar las 5 mejores recomendaciones
            for _, row in recomendaciones_df.head(5).iterrows():
                st.markdown(f"**{row['Ciudad']}** ({row['Tipo de vivienda']})")
                st.write(f"- Precio medio/m²: {row['Precio medio/m²']:.2f} €/m²")
                st.write(f"- Valor medio de compra: {row['Valor medio de compra']:.2f} €")
                st.write(f"- Proyección a 5 años: {row['Proyección 5 años (%)']:.2f} %")
                st.write(f"- Hipoteca mensual estimada: {row['Hipoteca mensual']:.2f} €")
                st.write(f"- Porcentaje de ingresos: {row['Porcentaje de ingresos']:.2f} %")
                st.write(f"- **Puntuación total:** {row['Puntuación total']:.2f}")
                st.write("---")
