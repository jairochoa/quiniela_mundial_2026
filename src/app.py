# Ruta del archivo: src/app.py
import streamlit as st
from datetime import datetime, timezone, timedelta
from auth import authenticate_user, hash_password
from config import TEAM_FLAGS, LOCK_WINDOW_HOURS, REVELATION_WINDOW_MINUTES, FLAG_CDN_URL, DEFAULT_FLAG_CODE
from database import (
    fetch_all_matches, 
    fetch_latest_user_predictions, 
    save_prediction_log, 
    get_leaderboard_data,
    supabase,
    fetch_all_users,
    update_user_password
)

# --- INYECCIÓN DE CSS AVANZADO: OCULTAR HEADER, FIJAR PESTAÑAS Y COMPACTAR TARJETAS ---
st.markdown("""
<style>
    /* 1. Oculta el encabezado nativo de Streamlit para evitar cortes y ganar pantalla */
    header[data-testid="stHeader"] {
        display: none !important;
    }
    
    /* 2. Congela la barra de pestañas en el borde superior absoluto del teléfono */
    div[data-testid="stTabs"] > div:first-child {
        position: -webkit-sticky;
        position: sticky;
        top: 0;
        background-color: #FFFFFF;
        z-index: 9999;
        padding-top: 4px;
        padding-bottom: 4px;
        border-bottom: 1px solid #E0E0E0;
    }
    
    /* 3. Reduce márgenes muertos del contenedor móvil */
    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 0.5rem !important;
    }
    
    /* 4. Minimiza el acolchado interno de los formularios */
    div[data-testid="stForm"] {
        padding: 6px !important;
    }
    
    /* 5. Centra las cajas de selección de goles */
    div[data-testid="stSelectbox"] {
        margin: 0 auto !important;
    }

    /* Estilos para la tabla compacta de posiciones */
    .tabla-leaderboard {
        width: 100%;
        border-collapse: collapse;
        font-size: 15px;
    }
    .tabla-leaderboard th {
        background-color: #F8F9FA;
        color: #212529;
        text-align: left;
        padding: 8px;
        border-bottom: 2px solid #E0E0E0;
    }
    .tabla-leaderboard td {
        padding: 10px 8px;
        border-bottom: 1px solid #F1F1F1;
    }
</style>
""", unsafe_allow_html=True)

if authenticate_user():
    user = st.session_state.user_info
    now_utc = datetime.now(timezone.utc)
    
    # --- BARRA LATERAL PARA GESTIÓN DE SESIÓN EN MÓVIL ---
    with st.sidebar:
        st.markdown(f"### 👤 Perfil")
        st.markdown(f"**Nombre:** {user['name']}")
        st.markdown(f"**Rol:** {'Administrador 🛠️' if user['is_admin'] else 'Jugador 🏃'}")
        st.divider()
        
        with st.expander("🔑 Cambiar mi Contraseña"):
            with st.form("change_password_form", clear_on_submit=True):
                nueva_clave = st.text_input("Nueva Contraseña", type="password", placeholder="Mínimo 6 caracteres")
                confirmar_clave = st.text_input("Confirmar Contraseña", type="password", placeholder="Repite la contraseña")
                submit_clave = st.form_submit_button("Actualizar Clave", use_container_width=True)
                
                if submit_clave:
                    if len(nueva_clave) < 6:
                        st.error("La contraseña debe tener al menos 6 caracteres.")
                    elif nueva_clave != confirmar_clave:
                        st.error("Las contraseñas no coinciden.")
                    else:
                        from src.auth import hash_password
                        from src.database import update_user_password
                        
                        nuevo_hash = hash_password(nueva_clave)
                        if update_user_password(user["id"], nuevo_hash):
                            st.success("¡Clave actualizada!")
                            st.toast("Contraseña cambiada con éxito. 🔐", icon="🎉")
        
        st.divider()
        if st.button("🚪 Cerrar Sesión", use_container_width=True, type="secondary"):
            st.session_state.authenticated = False
            st.session_state.user_info = None
            st.rerun()
    
    # 1. Carga de datos base
    matches = fetch_all_matches()
    user_preds = fetch_latest_user_predictions(user["id"])
    
    # 2. Configuración dinámica de Pestañas Móviles
    if user["is_admin"]:
        tab_p, tab_g, tab_t, tab_a = st.tabs(["📝 Votos", "👥 Grupo", "📊 Tabla", "⚙️ Admin"])
    else:
        tab_p, tab_g, tab_t = st.tabs(["📝 Votos", "👥 Grupo", "📊 Tabla"])
        tab_a = None

    # --- PESTAÑA 1: MIS PRONÓSTICOS ---
    with tab_p:
        filtro_vista = st.selectbox(
            "🔍 Filtrar partidos:",
            ["📅 Hoy y Mañana", "⏳ Pendientes por Votar", "📖 Ver Todo el Fixture"],
            label_visibility="collapsed"
        )
        
        matches_filtrados = []
        for m in matches:
            match_id = m["id"]
            match_time = datetime.fromisoformat(m["match_time"].replace("Z", "+00:00"))
            time_limit = match_time - timedelta(hours=LOCK_WINDOW_HOURS)
            is_locked = now_utc >= time_limit
            
            date_juego = match_time.date()
            date_hoy = now_utc.date()
            date_manana = date_hoy + timedelta(days=1)
            tiene_prediccion = match_id in user_preds

            if filtro_vista == "📅 Hoy y Mañana":
                if date_juego == date_hoy or date_juego == date_manana:
                    matches_filtrados.append((m, match_time, is_locked, time_limit))
            elif filtro_vista == "⏳ Pendientes por Votar":
                if not tiene_prediccion and not is_locked:
                    matches_filtrados.append((m, match_time, is_locked, time_limit))
            else:
                matches_filtrados.append((m, match_time, is_locked, time_limit))
        
        if not matches_filtrados:
            st.info("No hay partidos en este filtro. 🙌")
        
        for m, match_time, is_locked, time_limit in matches_filtrados:
            match_id = m["id"]
            saved_home = user_preds[match_id]["home_score"] if match_id in user_preds else 0
            saved_away = user_preds[match_id]["away_score"] if match_id in user_preds else 0
            
            with st.container(border=True):
                info_juego = f"🏆 {m.get('round', 'Jornada')} | 📍 {m.get('ground', 'Estadio')} | 🇻🇪 {m.get('venezuela_time', '00:00')}"
                st.caption(f"{'🔒 BLOQUEADO' if is_locked else '🟢 Abierto'} | {info_juego}")
                
                with st.form(key=f"user_form_{match_id}"):
                    # LÍNEA 1: Ambos países con sus banderas en una sola tira horizontal centrada
                    url_home = FLAG_CDN_URL.format(code=TEAM_FLAGS.get(m['home_team'], DEFAULT_FLAG_CODE))
                    url_away = FLAG_CDN_URL.format(code=TEAM_FLAGS.get(m['away_team'], DEFAULT_FLAG_CODE))
                    
                    st.markdown(f"""
                    <p style='text-align: center; font-size: 15px; font-weight: bold; margin-bottom: 10px; margin-top: 2px;'>
                        <img src='{url_home}' width='18'> {m['home_team']} 
                        <span style='color: #888; font-weight: normal; margin: 0 8px;'>vs</span> 
                        {m['away_team']} <img src='{url_away}' width='18'>
                    </p>
                    """, unsafe_allow_html=True)
                    
                    # LÍNEA 2: Marcador compacto usando Selectbox (Menú desplegable de un toque)
                    c1, c2, c3 = st.columns([5, 2, 5])
                    with c1:
                        h_in = st.selectbox("H", options=list(range(16)), index=int(saved_home), key=f"uh_{match_id}", disabled=is_locked, label_visibility="collapsed")
                    with c2:
                        st.markdown("<p style='text-align: center; font-size: 18px; font-weight: bold; margin-top: 4px;'>-</p>", unsafe_allow_html=True)
                    with c3:
                        a_in = st.selectbox("A", options=list(range(16)), index=int(saved_away), key=f"ua_{match_id}", disabled=is_locked, label_visibility="collapsed")
                    
                    # LÍNEA 3: Botón de acción adaptativo abajo
                    if not is_locked:
                        if st.form_submit_button("Guardar Pronóstico", use_container_width=True):
                            save_prediction_log(user["id"], match_id, h_in, a_in)
                            st.toast("💾 Registrado.", icon="✅")
                            st.rerun()
                    else:
                        st.form_submit_button(f"Tu Marcador Registrado: {int(saved_home)} - {int(saved_away)}", disabled=True, use_container_width=True)

    # --- PESTAÑA 2: APUESTAS DEL GRUPO ---
    with tab_g:
        st.markdown("### 👥 Apuestas Abiertas")
        dict_dias = {}
        for m in matches:
            fecha_dia = m["match_time"].split("T")[0]
            if fecha_dia not in dict_dias:
                dict_dias[fecha_dia] = []
            dict_dias[fecha_dia].append(m)
            
        for dia, juegos in dict_dias.items():
            tiempos_juegos = [datetime.fromisoformat(j["match_time"].replace("Z", "+00:00")) for j in juegos]
            primer_juego_del_dia = min(tiempos_juegos)
            hora_revelacion = primer_juego_del_dia - timedelta(minutes=REVELATION_WINDOW_MINUTES)
            revelado = now_utc >= hora_revelacion
            
            with st.expander(f"📅 Jornada del {dia}", expanded=revelado):
                if not revelado:
                    st.warning(f"🔒 Revelación: {hora_revelacion.strftime('%H:%M UTC')}")
                else:
                    logs_all = supabase.table("predictions_log").select("*").execute().data
                    all_users = fetch_all_users()
                    for j in juegos:
                        st.markdown(f"**⚽ {j['home_team']} vs {j['away_team']}**")
                        for u in all_users:
                            user_log = [l for l in logs_all if l["user_id"] == u["id"] and l["match_id"] == j["id"]]
                            if user_log:
                                ultimo_voto = sorted(user_log, key=lambda x: x["id"], reverse=True)[0]
                                st.markdown(f"• *{u['name']}:* {ultimo_voto['home_score']} - {ultimo_voto['away_score']}")
                            else:
                                st.markdown(f"• *{u['name']}:* No jugó 🤷‍♂️")
                        st.divider()

    # --- PESTAÑA 3: TABLA DE POSICIONES COMPACTA ---
    with tab_t:
        st.markdown("### 🏆 Tabla de Posiciones")
        leaderboard = get_leaderboard_data()
        
        tabla_html = "<table class='tabla-leaderboard'>"
        tabla_html += "<tr><th>Pos</th><th>Jugador</th><th style='text-align:right;'>Puntos</th></tr>"
        for idx, row in enumerate(leaderboard):
            medal = "🥇" if idx == 0 else ("🥈" if idx == 1 else ("🥉" if idx == 2 else f"{idx + 1}"))
            tabla_html += f"<tr><td>{medal}</td><td><b>{row['Jugador']}</b></td><td style='text-align:right; font-weight:bold; color:#1E90FF;'>{row['Puntos']} pts</td></tr>"
        tabla_html += "</table>"
        
        st.markdown(tabla_html, unsafe_allow_html=True)

    # --- PESTAÑA 4: PANEL ADMINISTRADOR ---
    if tab_a:
        with tab_a:
            st.markdown("### ⚙️ Cargar Resultados Oficiales")
            for m in matches:
                match_id = m["id"]
                curr_h = m["home_score"] if m["home_score"] is not None else 0
                curr_a = m["away_score"] if m["away_score"] is not None else 0
                
                with st.container(border=True):
                    info_juego = f"🏆 {m.get('round', 'Jornada')} | 📍 {m.get('ground', 'Estadio')} | 🇻🇪 {m.get('venezuela_time', '00:00')}"
                    st.caption(f"🆔 Partido #{match_id} | {info_juego}")
                    
                    with st.form(key=f"admin_form_{match_id}"):
                        # LÍNEA 1: Países en una sola línea horizontal para el administrador
                        url_home = FLAG_CDN_URL.format(code=TEAM_FLAGS.get(m['home_team'], DEFAULT_FLAG_CODE))
                        url_away = FLAG_CDN_URL.format(code=TEAM_FLAGS.get(m['away_team'], DEFAULT_FLAG_CODE))
                        
                        st.markdown(f"""
                        <p style='text-align: center; font-size: 15px; font-weight: bold; margin-bottom: 10px; margin-top: 2px;'>
                            <img src='{url_home}' width='18'> {m['home_team']} 
                            <span style='color: #888; font-weight: normal; margin: 0 8px;'>vs</span> 
                            {m['away_team']} <img src='{url_away}' width='18'>
                        </p>
                        """, unsafe_allow_html=True)
                        
                        # LÍNEA 2: Selectores de goles
                        c1, c2, c3 = st.columns([5, 2, 5])
                        with c1:
                            res_h = st.selectbox("H", options=list(range(16)), index=int(curr_h), key=f"ah_{match_id}", label_visibility="collapsed")
                        with c2:
                            st.markdown("<p style='text-align: center; font-size: 18px; font-weight: bold; margin-top: 4px;'>-</p>", unsafe_allow_html=True)
                        with c3:
                            res_a = st.selectbox("A", options=list(range(16)), index=int(curr_a), key=f"aa_{match_id}", label_visibility="collapsed")
                        
                        if st.form_submit_button("Publicar Resultado Oficial", use_container_width=True):
                            supabase.table("matches").update({"home_score": res_h, "away_score": res_a}).eq("id", match_id).execute()
                            st.toast("📢 Puntos recalculados.", icon="🚀")
                            st.rerun()