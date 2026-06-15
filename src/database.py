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
    
# Añadir al final de: src/database.py

def fetch_all_matches() -> list:
    """Trae todos los partidos ordenados por fecha."""
    response = supabase.table("matches").select("*").order("match_time").execute()
    return response.data if response.data else []

def fetch_latest_user_predictions(user_id: int) -> dict:
    """
    Trae el historial de predicciones del usuario y extrae 
    SÓLO la última versión guardada de cada partido.
    """
    response = supabase.table("predictions_log")\
        .select("*")\
        .eq("user_id", user_id)\
        .order("updated_at", desc=True)\
        .execute()
    
    latest_preds = {}
    # Al estar ordenados por fecha descendente, el primero que encontremos de cada match_id es el último
    for log in response.data:
        m_id = log["match_id"]
        if m_id not in latest_preds:
            latest_preds[m_id] = log
            
    return latest_preds

def save_prediction_log(user_id: int, match_id: int, home_score: int, away_score: int):
    """Inserta un nuevo registro de predicción (mantiene la auditoría)."""
    data = {
        "user_id": user_id,
        "match_id": match_id,
        "home_score": home_score,
        "away_score": away_score
    }
    supabase.table("predictions_log").insert(data).execute()