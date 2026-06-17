import os
import time
import toml
import pandas as pd
import plotly.express as px
from supabase import create_client

# 1. FUNCIÓN DE SCORING OFICIAL
def calculate_match_points(pred_home: int, pred_away: int, real_home: int, real_away: int) -> int:
    if pred_home == real_home and pred_away == real_away:
        return 5
    real_trend = "H" if real_home > real_away else ("A" if real_away > real_home else "D")
    pred_trend = "H" if pred_home > pred_away else ("A" if pred_away > pred_home else "D")
    return 3 if real_trend == pred_trend else 0

def main():
    print("🔌 Conectando a Supabase a través de secrets.toml...")
    # Cargar secretos manualmente desde el formato TOML
    try:
        secrets = toml.load(".streamlit/secrets.toml")
        SUPABASE_URL = secrets["supabase"]["url"]
        SUPABASE_KEY = secrets["supabase"]["key"]
    except Exception as e:
        print("❌ Error al leer .streamlit/secrets.toml. Asegúrate de ejecutar el script en la raíz.")
        return

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    # 2. DESCARGA DE DATOS CRUDOS
    print("📥 Descargando datos de juego...")
    users = supabase.table("users").select("id, name, is_admin").execute().data
    matches = supabase.table("matches").select("*").execute().data
    logs = supabase.table("predictions_log").select("*").execute().data

    jugadores = [u for u in users if not u.get("is_admin", False) and u["name"].strip().lower() != "admin"]
    partidos_jugados = sorted(
        [m for m in matches if m.get("home_score") is not None and str(m.get("home_score")).strip() != ""],
        key=lambda x: x.get("match_time", "")
    )

    if not partidos_jugados:
        print("🤷‍♂️ No hay partidos jugados con resultados oficiales para procesar.")
        return

    # 3. MATEMÁTICA ACUMULATIVA JUEGO POR JUEGO
    print("🧮 Calculando curvas de rendimiento históricas...")
    historial_puntos = []

    for u in jugadores:
        preds_user = [l for l in logs if str(l["user_id"]) == str(u["id"])]
        ultimos_votos = {}
        for log in sorted(preds_user, key=lambda x: x.get("id", 0)):
            ultimos_votos[str(log["match_id"])] = log

        puntos_acumulados = 0
        
        # Estado inicial (Antes del torneo)
        historial_puntos.append({
            "Jugador": u["name"],
            "Partido": "Inicio",
            "Puntos": 0,
            "Paso": 0,
            "Vs": "Torneo Listo"
        })

        for idx, match in enumerate(partidos_jugados, start=1):
            match_id_str = str(match["id"])
            label_partido = f"J{idx}"
            rivales = f"{match['home_team']} vs {match['away_team']}"
            
            if match_id_str in ultimos_votos:
                pred = ultimos_votos[match_id_str]
                try:
                    pts = calculate_match_points(
                        pred_home=int(pred["home_score"]), pred_away=int(pred["away_score"]),
                        real_home=int(match["home_score"]), real_away=int(match["away_score"])
                    )
                    puntos_acumulados += pts
                except ValueError:
                    pass
            
            historial_puntos.append({
                "Jugador": u["name"],
                "Partido": label_partido,
                "Puntos": puntos_acumulados,
                "Paso": idx,
                "Vs": rivales
            })

    # 4. CREACIÓN DEL DATAFRAME
    df = pd.DataFrame(historial_puntos)
    
    # 5. CREACIÓN DE LA ANIMACIÓN CON PLOTLY EXPRESS
    print("🎬 Armando los cuadros de animación...")
    
    # Usamos un gráfico de barras animado (Bar Chart Race)
    fig = px.bar(
        df,
        x="Puntos",
        y="Jugador",
        color="Jugador",
        animation_frame="Partido", # Cuadro de tiempo (J1, J2, J3...)
        animation_group="Jugador",
        orientation="h", # Barras horizontales que suben y bajan
        range_x=[0, df["Puntos"].max() + 5], # Ajuste dinámico de escala
        title="🏁 BAR CHART RACE: Evolución de la Quiniela",
        text="Puntos",
        hover_data=["Vs"]
    )

    # Configuración de velocidad y estética de la animación
    fig.update_layout(
        yaxis={"categoryorder": "total ascending"}, # Obliga a ordenar las barras de mayor a menor
        showlegend=False,
        width=800,
        height=600,
        plot_bgcolor="rgba(240,240,240,0.9)"
    )
    
    # Hacer que la animación corra suave
    fig.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 1200 # Milisegundos por juego
    fig.layout.updatemenus[0].buttons[0].args[1]["transition"]["duration"] = 500

    # 6. EXPORTAR A ARCHIVO LOCAL
    print("💾 Abriendo el visor interactivo en tu navegador...")
    output_html = "carrera_quiniela.html"
    fig.write_html(output_html)
    
    print(f"✅ ¡LISTO! Se generó el archivo '{output_html}' en la raíz.")
    print("💡 Abre ese archivo HTML en tu computadora, dale al botón de 'Play' y graba la pantalla con tu celular o una app de captura para enviarlo por WhatsApp.")

if __name__ == "__main__":
    main()