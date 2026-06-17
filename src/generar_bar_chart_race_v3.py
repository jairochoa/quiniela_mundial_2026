import os
import toml
import pandas as pd
from supabase import create_client

# 🟢 MONKEY PATCH CRUCIAL: Engañamos a las librerías viejas para que fillna acepte 'method' en Pandas moderno
if not hasattr(pd.Series, '_old_fillna'):
    pd.Series._old_fillna = pd.Series.fillna
    def new_series_fillna(self, value=None, method=None, *args, **kwargs):
        if method == 'ffill':
            return self.ffill(*args, **kwargs)
        elif method == 'bfill':
            return self.bfill(*args, **kwargs)
        return self._old_fillna(value=value, *args, **kwargs)
    pd.Series.fillna = new_series_fillna

if not hasattr(pd.DataFrame, '_old_fillna'):
    pd.DataFrame._old_fillna = pd.DataFrame.fillna
    def new_df_fillna(self, value=None, method=None, *args, **kwargs):
        if method == 'ffill':
            return self.ffill(*args, **kwargs)
        elif method == 'bfill':
            return self.bfill(*args, **kwargs)
        return self._old_fillna(value=value, *args, **kwargs)
    pd.DataFrame.fillna = new_df_fillna

# Ahora sí podemos importar bar_chart_race de forma segura
import bar_chart_race as bcr

def calculate_match_points(pred_home: int, pred_away: int, real_home: int, real_away: int) -> int:
    if pred_home == real_home and pred_away == real_away:
        return 5
    real_trend = "H" if real_home > real_away else ("A" if real_away > real_home else "D")
    pred_trend = "H" if pred_home > pred_away else ("A" if pred_away > pred_home else "D")
    return 3 if real_trend == pred_trend else 0

def main():
    print("🔌 Conectando a Supabase...")
    try:
        secrets = toml.load(".streamlit/secrets.toml")
        SUPABASE_URL = secrets["supabase"]["url"]
        SUPABASE_KEY = secrets["supabase"]["key"]
    except Exception:
        print("❌ Error al leer secrets.toml.")
        return

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    # 1. DESCARGA DE DATOS
    print("📥 Descargando datos desde la tabla 'users'...")
    users = supabase.table("users").select("id, name, is_admin").execute().data
    matches = supabase.table("matches").select("*").execute().data
    logs = supabase.table("predictions_log").select("*").execute().data

    jugadores = [u for u in users if not u.get("is_admin", False) and u["name"].strip().lower() != "admin"]
    partidos_jugados = sorted(
        [m for m in matches if m.get("home_score") is not None and str(m.get("home_score")).strip() != ""],
        key=lambda x: x.get("match_time", "")
    )

    if not partidos_jugados:
        print("🤷‍♂️ No hay partidos para procesar.")
        return

    # 2. CONSTRUCCIÓN DE LA MATRIZ DE TIEMPO
    print("Estructurando matriz histórica de puntos...")
    datos_carrera = {u["name"]: [0] for u in jugadores}
    indices_partidos = ["Inicio"]
    puntos_corriendo = {u["name"]: 0 for u in jugadores}

    for idx, match in enumerate(partidos_jugados, start=1):
        match_id_str = str(match["id"])
        goles_h = int(match["home_score"])
        goles_a = int(match["away_score"])
        
        label_partido = f"J{idx}: {match['home_team']} {goles_h}-{goles_a} {match['away_team']}"
        indices_partidos.append(label_partido)

        for u in jugadores:
            preds_user = [l for l in logs if str(l["user_id"]) == str(u["id"]) and str(l["match_id"]) == match_id_str]
            
            if preds_user:
                pred = sorted(preds_user, key=lambda x: x.get("id", 0))[-1]
                try:
                    pts = calculate_match_points(
                        pred_home=int(pred["home_score"]), pred_away=int(pred["away_score"]),
                        real_home=goles_h, real_away=goles_a
                    )
                    puntos_corriendo[u["name"]] += pts
                except ValueError:
                    pass
            
            datos_carrera[u["name"]].append(puntos_corriendo[u["name"]])

    df_carrera = pd.DataFrame(datos_carrera, index=indices_partidos)

    # 3. RENDERIZADO DE LA CARRERA
    print("🎬 Generando video con transiciones físicas reales...")
    output_file = "quiniela_valle_grande_2026.gif"
    
    bcr.bar_chart_race(
        df=df_carrera,
        filename=output_file,
        orientation='h',
        sort='desc',
        n_bars=10,                      
        fixed_max=True,                 
        steps_per_period=10,            # 🟢 Reducido a 10 para máxima velocidad de renderizado
        period_length=1500,             # 1.5 segundos por partido
        title='Evolucion de la Quiniela Valle Grande 2026', # 🟢 100% texto plano, sin emojis
        bar_label_size=12,
        tick_label_size=12,
        shared_fontdict={'family': 'Arial', 'color': '#2D3748', 'weight': 'bold'},
        scale='linear',
        writer=None,                    
        bar_kwargs={'alpha': 0.85, 'ec': '#FFFFFF', 'lw': 1.5}, 
        cmap='prism'                    
    )

    print(f"\n✅ ¡BRUTAL! Video fluido e histórico generado en: '{output_file}'")

if __name__ == "__main__":
    main()