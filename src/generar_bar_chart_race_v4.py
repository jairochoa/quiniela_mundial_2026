import os
import toml
import pandas as pd
import plotly.express as px
from supabase import create_client

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
        print("🤷‍♂️ No hay partidos jugados con resultados oficiales.")
        return

    # 2. MATEMÁTICA ACUMULATIVA (Nombres amarrados a las etiquetas internas)
    print("🧮 Calculando historial de posiciones estrictas...")
    historial_puntos = []

    for u in jugadores:
        preds_user = [l for l in logs if str(l["user_id"]) == str(u["id"])]
        ultimos_votos = {}
        for log in sorted(preds_user, key=lambda x: x.get("id", 0)):
            ultimos_votos[str(log["match_id"])] = log

        puntos_acumulados = 0
        
        # Frame 0: Estado Inicial uniforme
        historial_puntos.append({
            "Jugador": u["name"],
            "Frame_Animacion": "🏁 Inicio (Torneo Listo)",
            "Puntos": 0,
            # 🟢 TRUCO: Amarramos el nombre del jugador dentro de la etiqueta de la barra
            "Texto_Barra": f" {u['name']} [0 pts]"
        })

        for idx, match in enumerate(partidos_jugados, start=1):
            match_id_str = str(match["id"])
            goles_h = int(match["home_score"])
            goles_a = int(match["away_score"])
            
            rivales_con_score = f"{match['home_team']} {goles_h} - {goles_a} {match['away_team']}"
            label_frame_dinamico = f"⚽ Juego {idx}: {rivales_con_score}"
            
            if match_id_str in ultimos_votos:
                pred = ultimos_votos[match_id_str]
                try:
                    pts = calculate_match_points(
                        pred_home=int(pred["home_score"]), pred_away=int(pred["away_score"]),
                        real_home=goles_h, real_away=goles_a
                    )
                    puntos_acumulados += pts
                except ValueError:
                    pass
            
            historial_puntos.append({
                "Jugador": u["name"],
                "Frame_Animacion": label_frame_dinamico, 
                "Puntos": puntos_acumulados,
                # 🟢 El nombre y los puntos viajan juntos en el mismo contenedor
                "Texto_Barra": f" {u['name']} [{puntos_acumulados} pts]"
            })

    df_animar = pd.DataFrame(historial_puntos)

    # 🎨 3. RENDERIZADO CON PALETA PREMIUM Y TEXTO INTERNO DINÁMICO
    colores_elegantes = px.colors.qualitative.Prism

    fig = px.bar(
        df_animar,
        x="Puntos",
        y="Jugador",
        color="Jugador",
        animation_frame="Frame_Animacion",
        animation_group="Jugador",
        orientation="h",
        # Le damos un margen extra a la derecha (+7) para que las etiquetas largas no se corten
        range_x=[0, df_animar["Puntos"].max() + 7],
        title="🏆 EVOLUCIÓN HISTÓRICA DE LA QUINIELA VALLE GRANDE 2026",
        text="Texto_Barra", # 🟢 Reemplazamos Puntos_Label por nuestro bloque amarrado
        color_discrete_sequence=colores_elegantes
    )

    # ⚙️ 4. CONTROL TOTAL DE ANIMACIÓN, RITMO Y DISEÑO LIMPIO
    duracion_cuadro = 2200  
    duracion_deslizar = 700 

    fig.update_layout(
        # 🟢 DESACTIVAMOS EL EJE Y ESTÁTICO: Quitamos los nombres fijos de la izquierda
        yaxis={
            "categoryorder": "total ascending",
            "showticklabels": False,
            "title": ""
        },
        showlegend=False,
        width=900,
        height=650,
        font=dict(family="Arial, sans-serif", size=13, color="#2D3748"),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#F7FAFC",
        
        # Reducimos el margen izquierdo de l=120 a l=40 porque ya no hay textos en el eje Y
        margin=dict(l=40, r=40, t=140, b=120), 
        
        title={
            "text": "🏆 EVOLUCIÓN HISTÓRICA DE LA QUINIELA VALLE GRANDE 2026",
            "y": 0.96,          
            "x": 0.0,           
            "xanchor": "left",
            "yanchor": "top",
            "font": {"size": 22, "color": "#2D3748"}
        },
        
        xaxis_title="Puntos",
        sliders=[], 
        
        updatemenus=[{
            "type": "buttons",
            "direction": "left",
            "pad": {"r": 10, "t": 10},
            "showactive": False,
            "x": -0.01, 
            "y": -0.22, 
            "xanchor": "left",
            "yanchor": "top",
            "buttons": [{
                "label": "▶️ Play",
                "method": "animate",
                "args": [None, {
                    "frame": {"duration": duracion_cuadro, "redraw": True}, 
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

    # 🟢 5. INYECCIÓN PURA DE TEXTO SUPERIOR EN CADA FRAME
    for frame in fig.frames:
        frame.layout.update(
            annotations=[{
                "text": f"{frame.name}", 
                "xref": "paper",
                "yref": "paper",
                "x": 0.0,      
                "y": 1.10,     
                "showarrow": False,
                "font": {"size": 20, "color": "#1E90FF", "family": "Arial Black"},
                "xanchor": "left",
                "yanchor": "bottom"
            }]
        )

    # 🟢 AJUSTE VISUAL DE LAS BARRAS: Nombres alineados de forma prolija fuera/dentro
    fig.update_traces(
        textposition="outside", # Coloca el texto flotando justo al final de la barra
        textfont=dict(size=13, weight="bold", color="#2D3748"), # Letra oscura elegante y legible
        marker=dict(line=dict(width=1.5, color="#FFFFFF"))
    )
    
    # 6. EXPORTACIÓN
    output_html = "carrera_quiniela_real.html"
    fig.write_html(output_html)
    print(f"\n✅ ¡Listo, papá! Archivo 100% real generado en: '{output_html}'")

if __name__ == "__main__":
    main()