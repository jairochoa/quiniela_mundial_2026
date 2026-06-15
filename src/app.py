# Ruta del archivo: src/app.py
import streamlit as st
from datetime import datetime, timezone, timedelta
from auth import authenticate_user
from database import fetch_all_matches, fetch_latest_user_predictions, save_prediction_log, get_leaderboard_data

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
    
    # Menú responsivo de pestañas para el móvil
    if user["is_admin"]:
        tab_pronosticos, tab_tabla, tab_admin = st.tabs(["📝 Mis Pronósticos", "📊 Posiciones", "⚙️ Admin"])
    else:
        tab_pronosticos, tab_tabla = st.tabs(["📝 Mis Pronósticos", "📊 Posiciones"])
        tab_admin = None

    # --- PESTAÑA 1: PRONÓSTICOS ---
    with tab_pronosticos:
        st.markdown(f"### 👋 Hola, {user['name']}")
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
                
    # --- PESTAÑA 2: TABLA DE POSICIONES ---
    with tab_tabla:
        st.markdown("### 🏆 Tabla de Posiciones")
        leaderboard = get_leaderboard_data()
        
        # Formato visual limpio en tarjetas para que se lea perfecto en móvil sin scroll horizontal
        for idx, row in enumerate(leaderboard):
            medal = "🥇" if idx == 0 else ("🥈" if idx == 1 else ("🥉" if idx == 2 else "🏃"))
            with st.container(border=True):
                col_name, col_pts = st.columns([8, 2])
                col_name.markdown(f"{medal} **{row['Jugador']}**")
                col_pts.markdown(f"<p style='text-align: right; font-weight: bold; color: #1E90FF;'>{row['Puntos']} pts</p>", unsafe_allow_html=True)

    # --- PESTAÑA 3: PANEL ADMINISTRADOR ---
    if tab_admin:
        with tab_admin:
            st.markdown("### ⚙️ Cargar Resultados Oficiales")
            matches_to_update = fetch_all_matches()
            
            for m in matches_to_update:
                with st.container(border=True):
                    st.caption(f"Partido ID #{m['id']} - {m['phase'].upper()}")
                    with st.form(key=f"admin_form_{m['id']}"):
                        col1, col2, col3 = st.columns([4, 2, 4])
                        
                        current_h = m["home_score"] if m["home_score"] is not None else 0
                        current_a = m["away_score"] if m["away_score"] is not None else 0
                        
                        col1.markdown(f"**{m['home_team']}**")
                        res_h = col1.number_input("Goles Local", min_value=0, value=int(current_h), key=f"adm_h_{m['id']}", label_visibility="collapsed")
                        
                        col2.markdown("<p style='text-align: center; margin-top:25px;'>vs</p>", unsafe_allow_html=True)
                        
                        col3.markdown(f"<p style='text-align: right;'>**{m['away_team']}**</p>", unsafe_allow_html=True)
                        res_a = col3.number_input("Goles Visita", min_value=0, value=int(current_a), key=f"adm_a_{m['id']}", label_visibility="collapsed")
                        
                        if st.form_submit_button("Publicar Resultado Oficial", use_container_width=True):
                            update_match_result(m["id"], res_h, res_a)
                            st.toast("📢 Resultado guardado y puntajes recalculados.", icon="🚀")
                            st.rerun()