# Ruta del archivo: src/import_fixture.py
import json
import re
import os
from datetime import datetime, timezone, timedelta
from database import supabase

def process_times(date_str: str, time_str: str):
    """
    Procesa las cadenas del JSON para calcular:
    1. El timestamp ISO nativo en UTC para la lógica del sistema.
    2. La hora formateada de Venezuela (UTC-4) para la visualización.
    """
    # Expresión regular para entender formatos como "13:00 UTC-6" o "18:00 UTC+1"
    match = re.match(r"(\d{2}):(\d{2})\s+UTC([+-]\d+)?", time_str)
    if match:
        hh, mm, offset = match.groups()
        offset_hours = int(offset) if offset else 0
        
        # 1. Calcular UTC absoluto
        dt_local = datetime.strptime(f"{date_str} {hh}:{mm}", "%Y-%m-%d %H:%M")
        dt_utc = dt_local - timedelta(hours=offset_hours)
        dt_utc = dt_utc.replace(tzinfo=timezone.utc)
        
        # 2. Calcular Hora de Venezuela (UTC - 4)
        dt_venezuela = dt_utc - timedelta(hours=4)
        venezuela_time_str = dt_venezuela.strftime("%I:%M %p") # Ejemplo: "03:00 PM"
        
        return dt_utc.isoformat(), venezuela_time_str
        
    return f"{date_str}T00:00:00+00:00", "Por definir"

def import_json_fixture():
    json_path = "worldcup.json"
    
    if not os.path.exists(json_path):
        print(f"❌ Error: No se encontró el archivo '{json_path}' en la raíz.")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"⏳ Procesando fixture con hora de Venezuela y sedes...")
    
    match_counter = 1
    partidos_cargados = 0

    for match_item in data.get("matches", []):
        try:
            # Procesar tiempos intercalados
            utc_timestamp, vzla_time = process_times(match_item["date"], match_item["time"])
            
            # Armar payload con las nuevas columnas
            match_data = {
                "id": match_counter,
                "home_team": match_item["team1"].strip(),
                "away_team": match_item["team2"].strip(),
                "phase": "groups",
                "match_time": utc_timestamp,
                "home_score": None,
                "away_score": None,
                "round": match_item.get("round", "Matchday Desconocido").strip(),
                "ground": match_item.get("ground", "Estadio por definir").strip(),
                "venezuela_time": vzla_time
            }
            
            # Upsert en Supabase
            supabase.table("matches").upsert(match_data).execute()
            partidos_cargados += 1
            match_counter += 1
            
        except Exception as e:
            print(f"⚠️ Error en juego {match_item.get('team1')} vs {match_item.get('team2')}: {e}")

    print(f"🚀 ¡Ingesta limpia completada! {partidos_cargados} partidos listos con hora de Venezuela y sedes.")

if __name__ == "__main__":
    import_json_fixture()