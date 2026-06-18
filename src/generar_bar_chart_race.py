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

# Función auxiliar para determinar si un color hexadecimal es claro u oscuro
def get_contrast_color(hex_color):
    hex_color = hex_color.lstrip('#')
    claro_checks = ['yellow', 'gold', 'chartreuse', 'yellowgreen', 'palegreen', 'khaki']
    if any(c in hex_color.lower() for c in claro_checks):
        return "#1A202C" 
    try:
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        luminance = (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]) / 255
        return "#1A202C" if luminance > 0.6 else "#FFFFFF"
    except Exception:
        return "#FFFFFF"

def main():
    print("🔌 Conectando a Supabase a través de secrets.toml...")
    try:
        secrets = toml.load(".streamlit/secrets.toml")
        SUPABASE_URL = secrets["supabase"]["url"]
        SUPABASE_KEY = secrets["supabase"]["key"]
    except Exception as e:
        print("❌ Error al leer .streamlit/secrets.toml.")
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

    # Asignar colores únicos fijos de la paleta Dark24
    paleta_colores = px.colors.qualitative.Dark24
    color_map = {j["name"]: paleta_colores[i % len(paleta_colores)] for i, j in enumerate(jugadores)}

    # 3. MATEMÁTICA ACUMULATIVA JUEGO POR JUEGO
    print("🧮 Calculando curvas de rendimiento históricas...")
    historial_puntos = []

    for u in jugadores:
        preds_user = [l for l in logs if str(l["user_id"]) == str(u["id"])]
        ultimos_votos = {}
        for log in sorted(preds_user, key=lambda x: x.get("id", 0)):
            ultimos_votos[str(log["match_id"])] = log

        puntos_acumulados = 0
        j_color = color_map[u["name"]]
        text_color = get_contrast_color(j_color)
        
        # 🟢 CORRECCIÓN: Usamos &nbsp; para forzar espacios reales en la web y un bullet de separación limpio
        etiqueta_html_inicio = (
            f"<span style='float:left; padding-left:12px; font-size:15px; color:{text_color};'><b>{u['name']}</b></span>"
            f"<span style='float:right; padding-right:12px; font-size:14px; color:{text_color}; font-weight:bold;'>0&nbsp;pts</span>"
        )

        historial_puntos.append({
            "Jugador": u["name"],
            "Partido": "🏁 Inicio (Torneo Listo)",
            "Puntos": 0,
            "Texto_Móvil": etiqueta_html_inicio
        })

        for idx, match in enumerate(partidos_jugados, start=1):
            match_id_str = str(match["id"])
            rivales_con_score = f"{match['home_team']} {int(match['home_score'])} - {int(match['away_score'])} {match['away_team']}"
            label_frame = f"Juego {idx}: {rivales_con_score}"
            
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
            
            # 🟢 CORRECCIÓN: Inyección de espacios HTML duros (&nbsp;) para separar nombre y puntos perfectamente
            etiqueta_html_dinamica = (
                f"<span style='float:left; padding-left:12px; font-size:15px; color:{text_color};'><b>{u['name']}&nbsp;</b></span>"
                f"<span style='float:right; padding-right:12px; font-size:14px; color:{text_color}; font-weight:bold;'>{puntos_acumulados}&nbsp;pts</span>"
            )

            historial_puntos.append({
                "Jugador": u["name"],
                "Partido": label_frame,
                "Puntos": puntos_acumulados,
                "Texto_Móvil": etiqueta_html_dinamica
            })

    # 4. CREACIÓN DEL DATAFRAME
    df = pd.DataFrame(historial_puntos)
    
    # 5. CREACIÓN DE LA ANIMACIÓN CON PLOTLY EXPRESS
    print("🎬 Armando los cuadros de animación...")
    
    duracion_cuadro = 1500 
    duracion_deslizar = 600 

    fig = px.bar(
        df,
        x="Puntos",
        y="Jugador",
        color="Jugador", 
        animation_frame="Partido", 
        animation_group="Jugador",
        orientation="h", 
        range_x=[0, df["Puntos"].max() + 5], 
        title="🏆 TABLA DE LÍDERES - QUINIELA VALLE GRANDE 2026",
        text="Texto_Móvil",
        color_discrete_map=color_map
    )

    # Configuración de velocidad y estética de la animación
    fig.update_layout(
        yaxis={
            "categoryorder": "total ascending", 
            "showticklabels": False, 
            "title": ""
        }, 
        xaxis={
            "showticklabels": False,
            "title": "",
            "showgrid": False,
            "zeroline": False
        },
        showlegend=False,
        width=950,
        height=720, # Aumentamos un pelo la altura general para balancear el nuevo espacio
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#F8FAFC",
        
        # 🟢 MODIFICACIÓN CLAVE: Subimos t de 200 a 280. 
        # Esto empuja las barras hacia abajo y las separa por completo del slider.
        margin=dict(l=20, r=40, t=220, b=40), 
        
        title={
            "text": "🏆 TABLA DE LÍDERES - QUINIELA VALLE GRANDE 2026",
            "y": 0.96,          
            "x": 0.0,           
            "xanchor": "left",
            "yanchor": "top",
            "font": {"size": 22, "color": "#2D3748"}
        },
        
        # Mantener el slider arriba en su sitio coordinado
        sliders=[{
            "active": 0,
            "yanchor": "top",
            "xanchor": "left",
            "currentvalue": {
                "font": {"size": 20, "color": "#1A365D", "family": "Arial Black"}, 
                "prefix": "🔥 ⚽ ",
                "visible": True,
                "xanchor": "right"
            },
            "transition": {"duration": duracion_deslizar, "easing": "cubic-in-out"},
            "pad": {"b": 10, "t": 10},
            "len": 0.9,
            "x": 0.1,
            "y": 1.22 # Subido un pelo para emparejar con los botones
        }],
        
        updatemenus=[{
            "type": "buttons",
            "direction": "left",
            "pad": {"r": 10, "t": 5},
            "showactive": False,
            "x": -0.01, 
            "y": 1.22, 
            "xanchor": "left",
            "yanchor": "top",
            "buttons": [{
                "label": "▶️ Play",
                "method": "animate",
                "args": [None, {
                    "frame": {"duration": duracion_cuadro, "redraw": False}, 
                    "transition": {"duration": duracion_deslizar, "easing": "cubic-in-out"},
                    "fromcurrent": True,
                    "mode": "immediate"
                }]
            }, {
                "label": "⏸️ Pause",
                "method": "animate",
                "args": [[None], {
                    "frame": {"duration": 0, "redraw": False},
                    "transition": {"duration": 0},
                    "mode": "immediate"
                }]
            }]
        }]
    )
    
    fig.update_traces(
        textposition="inside",
        texttemplate="%{text}", 
        marker=dict(line=dict(width=1, color="#FFFFFF"))
    )

    # 6. EXPORTAR A ARCHIVO LOCAL
    print("💾 Generando archivo interactivo definitivo...")
    output_html = "carrera_quiniela.html"
    fig.write_html(output_html)
    
    print(f"\n🏆 ¡PROYECTO TERMINADO CON ÉXITO! Todo alineado y espaciado en de forma impecable en: '{output_html}'")

if __name__ == "__main__":
    main()