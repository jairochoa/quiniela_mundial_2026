# src/app.py
import streamlit as st

st.title("Prueba de Entorno")

try:
    # Intentar leer el secreto de Supabase de manera segura
    supabase_url = st.secrets["supabase"]["url"]
    st.success(f"¡Configuración exitosa! Conectando simuladamente a: {supabase_url}")
except KeyError:
    st.error("Error: No se pudo leer el archivo secrets.toml o faltan llaves.")