import pandas as pd
import streamlit as st

# Cargar el dataset con un separador personalizado (puede ser ;, tabulador, etc.)
# Asegúrate de que el separador sea el correcto para tu archivo CSV
df = pd.read_csv('datos_vivienda.csv', sep=';')  # Cambia ';' si es necesario

# Verificar las columnas del dataframe
st.write("Columnas del dataframe:", df.columns)

# Limpiar los nombres de las columnas eliminando espacios adicionales
df.columns = df.columns.str.strip()

# Verificar si la columna 'Ciudad' existe
if 'Ciudad' in df.columns:
    st.write("La columna 'Ciudad' está presente.")
else:
    st.write("La columna 'Ciudad' no está presente en el dataframe.")

# Verificar si hay valores nulos en la columna 'Ciudad'
if 'Ciudad' in df.columns:
    st.write(f"Valores nulos en 'Ciudad': {df['Ciudad'].isnull().sum()}")
else:
    st.write("No se puede verificar valores nulos, ya que la columna 'Ciudad' no existe.")

# Ver las primeras filas del dataframe
st.write("Primeras filas del dataframe:", df.head())
