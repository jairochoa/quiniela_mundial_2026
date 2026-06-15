# Ruta del archivo: src/app.py
import streamlit as st
from datetime import datetime, timezone, timedelta
from auth import authenticate_user
from database import fetch_all_matches, fetch_latest_user_predictions, save_prediction_log

# Mapeo estático de banderas (Flagcdn)
FLAGS = {"México": "mx", "Marruecos": "ma", "Estados Unidos": "us", "Japón": "jp", "Canadá": "ca", "Italia": "it", "Argentina": "ar", "España": "es"}

if authenticate_user():
    user = st.session_state.user_info
    st.markdown(f"<h3 style='text-align: center;'>⚽ Panel de {user['name']}</h3>", unsafe_allow_html=True)
    
    # 1. Obtener datos de la BD
    matches = fetch_all_matches()
    user_preds = fetch_latest_user_predictions(user["id"])
    
    # Hora actual estricta en UTC (Año 2026)
    now_utc = datetime.now(timezone.utc)
    
    # 2. Renderizar los partidos en formato tarjeta para móvil
    for m in matches:
        match_id = m["id"]
        # Convertir string de Supabase a objeto datetime con zona horaria
        match_time = datetime.fromisoformat(m["match_time"].replace("Z", "+00:00"))
        
        # Calcular límites de tiempo (Condición 3: 1 hora antes)
        time_limit = match_time - timedelta(hours=1)
        is_locked = now_utc >= time_limit
        
        # Recuperar valores previos si existen, sino por defecto 0
        saved_home = user_preds[match_id]["home_score"] if match_id in user_preds else 0
        saved_away = user_preds[match_id]["away_score"] if match_id in user_preds else 0
        
        # Contenedor visual tipo Tarjeta
        with st.container(border=True):
            # Encabezado de la tarjeta
            local_time_str = match_time.strftime('%d/%m %H:%M UTC')
            if is_locked:
                st.caption(f"🔒 **BLOQUEADO** ({local_time_str})")
            else:
                st.caption(f"🟢 **Disponible hasta:** {(time_limit).strftime('%d/%m %H:%M UTC')}")
            
            # Formulario para aislar el comportamiento del botón en móviles
            with st.form(key=f"form_match_{match_id}", clear_on_submit=False):
                col1, col2, col3 = st.columns([4, 2, 4])
                
                with col1:
                    flag = FLAGS.get(m["home_team"], "un")
                    st.markdown(f"<img src='https://flagcdn.com/w40/{flag}.png' width='22'> **{m['home_team']}**", unsafe_allow_html=True)
                    home_input = st.number_input("Goles", min_value=0, max_value=20, value=int(saved_home), key=f"h_{match_id}", disabled=is_locked, label_visibility="collapsed")
                
                with col2:
                    st.markdown("<p style='text-align: center; font-size: 20px; font-weight: bold; margin-top: 5px;'>VS</p>", unsafe_allow_html=True)
                
                with col3:
                    flag = FLAGS.get(m["away_team"], "un")
                    st.markdown(f"<p style='text-align: right;'>**{m['away_team']}** <img src='https://flagcdn.com/w40/{flag}.png' width='22'></p>", unsafe_allow_html=True)
                    away_input = st.number_input("Goles", min_value=0, max_value=20, value=int(saved_away), key=f"a_{match_id}", disabled=is_locked, label_visibility="collapsed")
                
                # Botón de guardado dinámico
                if not is_locked:
                    submit_btn = st.form_submit_button("Guardar Pronóstico", use_container_width=True)
                    if submit_btn:
                        save_prediction_log(user["id"], match_id, home_input, away_input)
                        st.toast(f"💾 ¡Pronóstico guardado para el {m['home_team']} vs {m['away_team']}!", icon="✅")
                        st.rerun()
                else:
                    st.form_submit_button(f"Tu apuesta: {saved_home} - {saved_away}", disabled=True, use_container_width=True)