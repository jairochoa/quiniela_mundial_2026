# Ruta del archivo: src/import_fixture.py
import json
import re
import os
from datetime import datetime, timezone, timedelta
from database import supabase
from config import TEAM_TRANSLATIONS

def process_times(date_str: str, time_str: str):
    match = re.match(r"(\d{2}):(\d{2})\s+UTC([+-]\d+)?", time_str)
    if match:
        hh, mm, offset = match.groups()
        offset_hours = int(offset) if offset else 0
        
        dt_local = datetime.strptime(f"{date_str} {hh}:{mm}", "%Y-%m-%d %H:%M")
        dt_utc = dt_local - timedelta(hours=offset_hours)
        dt_utc = dt_utc.replace(tzinfo=timezone.utc)
        
        dt_venezuela = dt_utc - timedelta(hours=4)
        venezuela_time_str = dt_venezuela.strftime("%I:%M %p")
        
        return dt_utc.isoformat(), venezuela_time_str
        
    return f"{date_str}T00:00:00+00:00", "Por definir"

def import_json_fixture():
    json_path = "worldcup.json"
    
    if not os.path.exists(json_path):
        print(f"❌ Error: No se encontró el archivo '{json_path}' en la raíz.")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"⏳ Procesando e insertando fixture traducido al español...")
    
    match_counter = 1
    partidos_cargados = 0

    for match_item in data.get("matches", []):
        try:
            utc_timestamp, vzla_time = process_times(match_item["date"], match_item["time"])
            
            # 1. Traducir nombres de equipos usando el diccionario de config.py
            team1_raw = match_item["team1"].strip()
            team2_raw = match_item["team2"].strip()
            home_es = TEAM_TRANSLATIONS.get(team1_raw, team1_raw)
            away_es = TEAM_TRANSLATIONS.get(team2_raw, team2_raw)
            
            # 2. Traducir la Ronda dinámicamente (Matchday X -> Jornada X)
            round_raw = match_item.get("round", "Matchday Desconocido").strip()
            round_es = round_raw.replace("Matchday", "Jornada")
            
            
            match_data = {
                "id": match_counter,
                "home_team": home_es,
                "away_team": away_es,
                "match_time": utc_timestamp,
                "home_score": None,
                "away_score": None,
                "round": round_es,
                "ground": match_item.get("ground", "Estadio por definir").strip(),
                "venezuela_time": vzla_time
            }
            
            supabase.table("matches").upsert(match_data).execute()
            partidos_cargados += 1
            match_counter += 1
            
        except Exception as e:
            print(f"⚠️ Error en juego {match_item.get('team1')} vs {match_item.get('team2')}: {e}")

    print(f"🚀 ¡Ingesta completada! {partidos_cargados} partidos guardados en perfecto español.")

if __name__ == "__main__":
    import_json_fixture()