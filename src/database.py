# Ruta del archivo: src/database.py
import streamlit as st
from supabase import create_client, Client

@st.cache_resource
def get_supabase_client() -> Client:
    """Inicializa de forma segura y cacheada el cliente de Supabase."""
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

# Instancia única del cliente para toda la aplicación
supabase = get_supabase_client()

def fetch_user_by_username(username: str) -> dict | None:
    """Busca un usuario en la tabla 'users' por su nombre de usuario."""
    try:
        response = supabase.table("users").select("*").eq("username", username.strip().lower()).execute()
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        st.error(f"Error de conexión con la base de datos: {e}")
        return None