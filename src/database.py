# Ruta del archivo: src/database.py
import streamlit as st
from supabase import create_client, Client
from scoring import calculate_match_points

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
    

def update_match_result(match_id: int, home_score: int, away_score: int):
    """Guarda el resultado oficial de un partido (Uso exclusivo del Admin)."""
    supabase.table("matches").update({
        "home_score": home_score,
        "away_score": away_score
    }).eq("id", match_id).execute()

def fetch_all_users() -> list:
    """Trae la lista de todos los jugadores registrados."""
    response = supabase.table("users").select("id", "name", "username").execute()
    return response.data if response.data else []

def get_leaderboard_data() -> list:
    """
    Calcula las puntuaciones de todos los jugadores procesando 
    las predicciones vs los resultados reales guardados.
    """
    users = fetch_all_users()
    matches = supabase.table("matches").select("*").execute().data
    
    # Mapear partidos jugados (los que tienen score no nulo)
    played_matches = {m["id"]: m for m in matches if m["home_score"] is not None}
    
    leaderboard = []
    
    for user in users:
        # 🔥 CORRECCIÓN 1: Excluir al Admin de raíz para que no gaste procesamiento ni sume puntos
        if user.get("is_admin", False) or user["name"].strip().lower() == "admin":
            continue
            
        # 🔥 CORRECCIÓN 2: Cambiamos 'updated_at' por 'id' (descendente).
        # El 'id' es serial y autoincremental, lo que garantiza que lea los datos del JSON perfectamente.
        preds_response = supabase.table("predictions_log")\
            .select("*").eq("user_id", user["id"])\
            .order("id", desc=True).execute().data
            
        latest_preds = {}
        for log in preds_response:
            if log["match_id"] not in latest_preds:
                latest_preds[log["match_id"]] = log
        
        # Calcular puntos acumulados
        total_points = 0
        for match_id, match in played_matches.items():
            if match_id in latest_preds:
                pred = latest_preds[match_id]
                
                # Forzamos conversión a int por seguridad de tipos en la BD
                pts = calculate_match_points(
                    pred_home=int(pred["home_score"]),
                    pred_away=int(pred["away_score"]),
                    real_home=int(match["home_score"]),
                    real_away=int(match["away_score"])
                )
                total_points += pts
        
        leaderboard.append({
            "Jugador": user["name"],
            "Puntos": total_points
        })
        
    # Ordenar ranking de mayor a menor puntuación
    return sorted(leaderboard, key=lambda x: x["Puntos"], reverse=True)

def update_user_password(user_id: int, new_hash: str) -> bool:
    """Actualiza de forma segura el hash de la contraseña de un usuario."""
    try:
        supabase.table("users").update({"password_hash": new_hash}).eq("id", user_id).execute()
        return True
    except Exception as e:
        st.error(f"Error técnico al actualizar contraseña: {e}")
        return False