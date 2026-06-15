# Ruta del archivo: src/seed_matches.py
from datetime import datetime, timezone
import streamlit as st
# Reutilizamos el cliente cacheado que ya creamos
from database import supabase 

# Diccionario maestro de banderas para el Mundial 2026 (Flagcdn ISO Codes)
TEAM_FLAGS = {
    "Estados Unidos": "us",
    "México": "mx",
    "Canadá": "ca",
    "Argentina": "ar",
    "Brasil": "br",
    "Francia": "fr",
    "España": "es",
    "Alemania": "de",
    "Italia": "it",
    "Colombia": "co",
    "Marruecos": "ma",
    "Japón": "jp"
}

# Lista de partidos iniciales de la Fase de Grupos
# NOTA: Usamos horas en UTC estrictamente
INITIAL_MATCHES = [
    {
        "id": 1,
        "home_team": "México",
        "away_team": "Marruecos",
        "phase": "groups",
        "match_time": datetime(2026, 6, 11, 22, 0, 0, tzinfo=timezone.utc).isoformat()
    },
    {
        "id": 2,
        "home_team": "Estados Unidos",
        "away_team": "Japón",
        "phase": "groups",
        "match_time": datetime(2026, 6, 12, 19, 0, 0, tzinfo=timezone.utc).isoformat()
    },
    {
        "id": 3,
        "home_team": "Canadá",
        "away_team": "Italia",
        "phase": "groups",
        "match_time": datetime(2026, 6, 12, 23, 0, 0, tzinfo=timezone.utc).isoformat()
    },
    {
        "id": 4,
        "home_team": "Argentina",
        "away_team": "España",
        "phase": "groups",
        "match_time": datetime(2026, 6, 15, 18, 0, 0, tzinfo=timezone.utc).isoformat()
    }
]

def seed_database():
    print("⏳ Insertando fixture en Supabase...")
    for match in INITIAL_MATCHES:
        try:
            # Upsert evita duplicados si corres el script más de una vez
            supabase.table("matches").upsert(match).execute()
            print(f"✅ Partido {match['id']}: {match['home_team']} vs {match['away_team']} cargado.")
        except Exception as e:
            print(f"❌ Error en partido {match['id']}: {e}")
    print("🚀 Proceso de carga finalizado.")

if __name__ == "__main__":
    # Ejecutar directo si se llama desde la terminal
    seed_database()