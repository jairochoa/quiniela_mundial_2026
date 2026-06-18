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

# --- INYECCIÓN DE CSS CALIBRADO PARA MÓVILES (JALONAR MARCADORES A LA IZQUIERDA) ---
st.markdown("""
<style>
    /* Bloqueo total y absoluto de scroll horizontal a nivel raíz */
    html, body, .main, section[data-testid="stMain"], [data-testid="stApp"], [data-testid="stAppViewBlockContainer"], [data-testid="stAppViewContainer"] {
        overflow-x: hidden !important;
    }
    
    /* 1. Oculta la barra de herramientas superior de Streamlit */
    header[data-testid="stHeader"] {
        display: none !important;
    }
    
    /* 2. Mantiene las pestañas fijas arriba sin cortes */
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
    
    /* 3. Reduce márgenes muertos en smartphones */
    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 0.5rem !important;
    }
    
    /* 4. Compacta el espaciado de los formularios */
    div[data-testid="stForm"] {
        padding: 8px !important;
        overflow: hidden !important; /* Camisa de fuerza para la tarjeta blanca */
    }
    
    /* 5. SOLUCIÓN: Agrega un colchón derecho de 50px para JALONAR los marcadores hacia la izquierda */
    div[data-testid="stForm"] div[data-testid="stHorizontalBlock"] {
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
        gap: 6px !important;
        padding-right: 50px !important; /* Empuja el contenido de la derecha hacia adentro */
        box-sizing: border-box !important;
        margin-left: 0 !important;       /* ANULA el margen negativo izquierdo nativo */
        margin-right: 0 !important;      /* ANULA el margen negativo derecho que creaba el scroll */
        width: 100% !important; /* Fuerza a la fila a medir exactamente lo mismo que la tarjeta */
    }
    
    /* 6. Bloquea el ancho de las columnas internas para que no ignoren la pantalla */
    div[data-testid="stForm"] div[data-testid="column"] {
        min-width: 0 !important;
        flex-shrink: 1 !important;
    }
    
    /* 7. Limita el tamaño de las cajas de goles y elimina márgenes rebeldes */
    div[data-testid="stForm"] div[data-testid="stSelectbox"] {
        max-width: 65px !important;
        width: 100% !important;
        margin: 0 !important;
    }

    /* 8. Trunca nombres largos de países automáticamente si no caben */
    .team-text-container {
        margin-top: -20px !important; /* Margen negativo: Jala el texto hacia arriba. Calíbralo si te falta o sobra */
        margin-bottom: 0 !important;
        margin-left: 0 !important;
        margin-right: 0 !important;
        font-size: 14px; 
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        display: block !important;
        width: 100%;
    }
    
    .team-text-container img {
        vertical-align: middle !important;
        margin-right: 6px !important;
        margin-top: -2px !important;
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
    
    div[data-testid="stFormSubmitButton"] {
        margin-top: -10px !important;
    }
    /* 9. ELIMINA EL ESPACIO VERTICAL: Pega la fila de abajo con la de arriba colapsando el gap nativo */
    div[data-testid="stForm"] > div[data-testid="stVerticalBlockBorderWrapper"] > div > div[data-testid="stVerticalBlock"] {
        gap: 2px !important; /* Reduce a casi cero el espacio de separación entre las filas del partido */
    }
    
</style>
""", unsafe_allow_html=True)

if authenticate_user():
    user = st.session_state.user_info
    now_utc = datetime.now(timezone.utc)
    
    # --- BARRA LATERAL UNIFICADA: PERFIL, CONTRASEÑA Y LOGOUT ---
    with st.sidebar:
        st.markdown(f"### 👤 Perfil")
        st.markdown(f"**Nombre:** {user['name']}")
        st.markdown(f"**Rol:** {'Administrador 🛠️' if user['is_admin'] else 'Jugador 🏃'}")
        st.divider()
        
        # Un solo expander limpio con IDs únicos para evitar colisiones
        with st.expander("🔑 Cambiar mi Contraseña"):
            with st.form("change_password_sidebar_form", clear_on_submit=True):
                nueva_clave = st.text_input("Nueva Contraseña", type="password", placeholder="Mínimo 6 caracteres")
                confirmar_clave = st.text_input("Confirmar Contraseña", type="password", placeholder="Repite la contraseña")
                submit_clave = st.form_submit_button("Actualizar Clave", use_container_width=True)
                
                if submit_clave:
                    if len(nueva_clave) < 6:
                        st.error("La contraseña debe tener al menos 6 caracteres.")
                    elif nueva_clave != confirmar_clave:
                        st.error("Las contraseñas no coinciden.")
                    else:
                        nuevo_hash = hash_password(nueva_clave)
                        if update_user_password(user["id"], nuevo_hash):
                            st.success("¡Clave actualizada!")
                            st.toast("Contraseña cambiada con éxito. 🔐", icon="🎉")
        
        st.divider()
        # Un solo botón de cerrar sesión blindado con su respectiva llave única
        if st.button("🚪 Cerrar Sesión", use_container_width=True, type="secondary", key="sidebar_logout_btn"):
            st.session_state.authenticated = False
            st.session_state.user_info = None
            st.rerun()
    
    # 1. Carga de datos base
    matches = fetch_all_matches()
    user_preds = fetch_latest_user_predictions(user["id"])
    
    # 🟢 CÓDIGO NUEVO: Precalcular el partido inaugural de cada jornada (round) en hora de Venezuela
    tz_ve = timezone(timedelta(hours=-4))
    primer_partido_por_round = {}
    for m in matches:
        r_name = m.get("round", "Jornada")
        if m.get("match_time"):
            m_time = datetime.fromisoformat(m["match_time"].replace("Z", "+00:00"))
            if r_name not in primer_partido_por_round or m_time < primer_partido_por_round[r_name]:
                primer_partido_por_round[r_name] = m_time

    # 2. Configuración dinámica de Pestañas Móviles
    if user["is_admin"]:
        tab_p, tab_g, tab_t, tab_a = st.tabs(["📝 Votos", "👥 Grupo", "📊 Tabla", "⚙️ Admin"])
    else:
        tab_p, tab_g, tab_t = st.tabs(["📝 Mis Pronósticos", "👥 Grupo", "📊 Tabla"])
        tab_a = None

    # --- PESTAÑA 1: MIS PRONÓSTICOS ---
    with tab_p:
        filtro_vista = st.selectbox(
            "🔍 Filtrar partidos:",
            ["📅 Hoy y Mañana", "⏳ Pendientes por Pronosticar", "📖 Ver Todo el Fixture"],
            label_visibility="collapsed"
        )
        
        matches_filtrados = []
        for m in matches:
            match_id = m["id"]
            round_name = m.get("round", "Jornada")
            match_time = datetime.fromisoformat(m["match_time"].replace("Z", "+00:00"))
            
            # 🟢 CÓDIGO NUEVO: Evaluar bloqueo basado en el primer juego de SU JORNADA (1 hora antes)
            primer_juego_time = primer_partido_por_round.get(round_name, match_time)
            time_limit = primer_juego_time - timedelta(hours=1)
            is_locked = now_utc >= time_limit
            
            # CÓDIGO CORREGIDO (CONVERTIDO A ENTORNO VENEZUELA UTC-4):
            date_juego = match_time.astimezone(tz_ve).date()
            date_hoy = now_utc.astimezone(tz_ve).date()
            date_manana = date_hoy + timedelta(days=1)
            tiene_prediccion = match_id in user_preds

            if filtro_vista == "📅 Hoy y Mañana":
                if date_juego == date_hoy or date_juego == date_manana:
                    matches_filtrados.append((m, match_time, is_locked, time_limit))
            elif filtro_vista == "⏳ Pendientes por Pronosticar":
                if not tiene_prediccion and not is_locked:
                    matches_filtrados.append((m, match_time, is_locked, time_limit))
            else:
                matches_filtrados.append((m, match_time, is_locked, time_limit))
        
        if not matches_filtrados:
            st.info("No hay partidos en este filtro. 🙌")
        
        for m, match_time, is_locked, time_limit in matches_filtrados:
            match_id = m["id"]
            tiene_prediccion = match_id in user_preds
            saved_home = user_preds[match_id]["home_score"] if match_id in user_preds else 0
            saved_away = user_preds[match_id]["away_score"] if match_id in user_preds else 0
            
            with st.container(border=True):
                info_juego = f"🏆 {m.get('round', 'Jornada')} | 🇻🇪 {m.get('venezuela_time', '00:00')}"
                # 🟢 CÓDIGO NUEVO: Advertencia de bloqueo colectivo en el estado del contenedor
                estado = "🔒 BLOQUEADO" if is_locked else "🟢 Abierto"
                if tiene_prediccion and not is_locked:
                    estado += " | 💾 ¡PRONÓSTICO GUARDADO!"
                st.caption(f"{estado}\n\n{info_juego}")
                if tiene_prediccion and not is_locked:
                    st.success(f"✓ Tu voto actual: {int(saved_home)} - {int(saved_away)}", icon="ℹ️")
                
                with st.form(key=f"user_form_{match_id}"):
                    # Si el usuario ya votó este partido, le clavamos un aviso verde impecable arriba
                    if tiene_prediccion:
                        st.markdown(f"""
                        <div style="background-color: #E6F4EA; color: #137333; border-left: 4px solid #1E8E3E; padding: 4px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; margin-bottom: 6px; text-align: center;">
                            ✓ TU PRONÓSTICO ES: {int(saved_home)} - {int(saved_away)}
                        </div>
                        """, unsafe_allow_html=True)
                    url_home = FLAG_CDN_URL.format(code=TEAM_FLAGS.get(m['home_team'], DEFAULT_FLAG_CODE))
                    url_away = FLAG_CDN_URL.format(code=TEAM_FLAGS.get(m['away_team'], DEFAULT_FLAG_CODE))
                    
                    # FILA 1: Local (Proporción 6:4 horizontal)
                    c1_h, c2_h = st.columns([5.5, 4.5])
                    with c1_h:
                        st.markdown(f"<p class='team-text-container'><img src='{url_home}' width='18'> <b>{m['home_team']}</b></p>", unsafe_allow_html=True)
                    with c2_h:
                        h_in = st.selectbox("H", options=list(range(11)), index=int(saved_home), key=f"uh_{match_id}", disabled=is_locked, label_visibility="collapsed")
                    
                    # FILA 2: Visitante (Proporción 6:4 horizontal)
                    c1_a, c2_a = st.columns([5.5, 4.5])
                    with c1_a:
                        st.markdown(f"<p class='team-text-container'><img src='{url_away}' width='18'> <b>{m['away_team']}</b></p>", unsafe_allow_html=True)
                    with c2_a:
                        a_in = st.selectbox("A", options=list(range(11)), index=int(saved_away), key=f"ua_{match_id}", disabled=is_locked, label_visibility="collapsed")
                    
                    # CÓDIGO NUEVO (BOTÓN INTELIGENTE: CAMBIA COLOR Y TEXTO):
                    if not is_locked:
                        # Si ya existe voto, el botón se vuelve gris y le recuerda qué número guardó. Si no, se vuelve azul.
                        texto_btn = f"🔄 Actualizar (Registrado: {int(saved_home)} - {int(saved_away)})" if tiene_prediccion else "💾 Guardar Pronóstico"
                        tipo_btn = "secondary" if tiene_prediccion else "primary"
                        
                        if st.form_submit_button(texto_btn, use_container_width=True, type=tipo_btn):
                            save_prediction_log(user["id"], match_id, h_in, a_in)
                            st.toast("💾 ¡Pronóstico guardado exitosamente!", icon="✅")
                            st.rerun()
                    else:
                        st.form_submit_button(f"Ya no puedes cambiar tu pronóstico: {int(saved_home)} - {int(saved_away)}", disabled=True, use_container_width=True)

# --- PESTAÑA 2: APUESTAS DEL GRUPO (CON AUTO-APERTURA DE JORNADA ACTUAL) ---
    with tab_g:
        st.markdown("### 👥 Juegos Abiertos")
        
        # CEREBRO DE PROXIMIDAD: Encontramos el round actual basado en el partido más cercano a este preciso instante
        round_actual = ""
        if matches:
            partido_mas_cercano = min(
                matches, 
                key=lambda x: abs((datetime.fromisoformat(x["match_time"].replace("Z", "+00:00")) - now_utc).total_seconds())
            )
            round_actual = partido_mas_cercano.get("round", "Jornada")
        
        # AGRUPACIÓN MAESTRA: Agrupamos los partidos por el campo 'round' de Supabase
        dict_rounds = {}
        for m in matches:
            r = m.get("round", "Jornada")
            if r not in dict_rounds:
                dict_rounds[r] = []
            dict_rounds[r].append(m)
            
        # Iteramos sobre cada Round/Jornada oficial del torneo
        for round_name, juegos in dict_rounds.items():
            tiempos_juegos = [datetime.fromisoformat(j["match_time"].replace("Z", "+00:00")) for j in juegos]
            
            # Buscamos el juego que abre el round
            primer_juego_del_round = min(tiempos_juegos)
            hora_revelacion = primer_juego_del_round - timedelta(minutes=REVELATION_WINDOW_MINUTES)
            revelado = now_utc >= hora_revelacion
            
            # DINÁMICO: El expander se abre por defecto SOLO si es la jornada que se está jugando hoy o la más próxima
            jornada_activa = (round_name == round_actual)
            
            with st.expander(f"🏆 {round_name}", expanded=jornada_activa):
                logs_all = supabase.table("predictions_log").select("*").execute().data
                all_users = [u for u in fetch_all_users() if not u.get("is_admin", False)]
                
                # Mensaje informativo calibrado a hora de Venezuela para los usuarios
                if not revelado:
                    hora_ve_revelacion = hora_revelacion.astimezone(tz_ve).strftime("%I:%M %p")
                    st.caption(f"🔒 Los pronósticos de este bloque se liberarán a las {hora_ve_revelacion} ({REVELATION_WINDOW_MINUTES} min antes del primer juego).")
                
                for j in juegos:
                    st.markdown(f"**⚽ {j['home_team']} vs {j['away_team']}**")
                    
                    for u in all_users:
                        is_me = (u["id"] == user["id"])
                        user_log = [l for l in logs_all if l["user_id"] == u["id"] and l["match_id"] == j["id"] and not l["is_admin"]]
                        nombre_mostrar = f"• **Tú**" if is_me else f"• *{u['name']}*"
                        
                        if user_log:
                            ultimo_voto = sorted(user_log, key=lambda x: x["id"], reverse=True)[0]
                            
                            # FILTRO DE PRIVACIDAD: Si ya se reveló el bloque entero O soy yo, veo el score
                            if revelado or is_me:
                                st.markdown(f"{nombre_mostrar}: {int(ultimo_voto['home_score'])} - {int(ultimo_voto['away_score'])}")
                            else:
                                st.markdown(f"{nombre_mostrar}: Ya envió su pronóstico 🔒")
                        else:
                            if is_me:
                                st.markdown(f"{nombre_mostrar}: Aún no has votado 🤷‍♂️")
                            else:
                                st.markdown(f"{nombre_mostrar}: Aún no envió su pronóstico ⏳")
                    st.divider()
                    
# --- PESTAÑA 3: TABLA DE POSICIONES COMPACTA (RESOLVIDO) ---
    with tab_t:
        st.markdown("### 🏆 Tabla de Posiciones")
        
        # 🟢 AQUÍ ESTÁ LA SOLUCIÓN: Definimos la función exacta dentro del scope para eliminar el NameError
        def calculate_match_points(pred_home: int, pred_away: int, real_home: int, real_away: int) -> int:
            # Caso 1: Marcador Exacto
            if pred_home == real_home and pred_away == real_away:
                return 5
            # Determinar tendencias
            real_trend = "H" if real_home > real_away else ("A" if real_away > real_home else "D")
            pred_trend = "H" if pred_home > pred_away else ("A" if pred_away > pred_home else "D")
            # Caso 2: Acertar tendencia
            if real_trend == pred_trend:
                return 3
            return 0

        # 1. MOTOR DE CÁLCULO EN TIEMPO REAL
        todos_usuarios = fetch_all_users()
        logs_all = supabase.table("predictions_log").select("*").execute().data
        matches_db = supabase.table("matches").select("*").execute().data
        
        # Filtramos partidos jugados
        partidos_jugados = {
            str(m["id"]): m for m in matches_db 
            if m.get("home_score") is not None and str(m.get("home_score")).strip() != ""
        }
        
        leaderboard_data = []
        
        for u in todos_usuarios:
            # Filtro total anti-admin
            if u.get("is_admin", False) or u["name"].strip().lower() in ["admin", "administrator"]:
                continue
                
            preds_usuario = [l for l in logs_all if str(l["user_id"]) == str(u["id"])]
            
            puntos_totales = 0
            
            # Agrupar los últimos votos del usuario
            ultimos_votos_usuario = {}
            for log in sorted(preds_usuario, key=lambda x: x.get("id", 0)):
                ultimos_votos_usuario[str(log["match_id"])] = log
                
            for m_id_str, match in partidos_jugados.items():
                if m_id_str in ultimos_votos_usuario:
                    pred = ultimos_votos_usuario[m_id_str]
                    try:
                        # Ahora sí llamará a la función local sin caerse
                        pts = calculate_match_points(
                            pred_home=int(pred["home_score"]),
                            pred_away=int(pred["away_score"]),
                            real_home=int(match["home_score"]),
                            real_away=int(match["away_score"])
                        )
                        puntos_totales += pts
                    except Exception:
                        pass
            
            leaderboard_data.append({
                "Jugador": u["name"],
                "Puntos": puntos_totales
            })
            
        leaderboard = sorted(leaderboard_data, key=lambda x: x["Puntos"], reverse=True)
        
        # 2. RENDERIZADO DE LA TABLA HTML LIMPIA
        if not partidos_jugados:
            st.info("⚽ La tabla se activará cuando el Admin cargue los primeros resultados oficiales.")
        else:
            tabla_html = "<table class='tabla-leaderboard'>"
            tabla_html += "<tr><th>Pos</th><th>Jugador</th><th style='text-align:right;'>Puntos</th></tr>"
            for idx, row in enumerate(leaderboard):
                medal = "🥇" if idx == 0 else ("🥈" if idx == 1 else ("🥉" if idx == 2 else f"{idx + 1}"))
                tabla_html += f"<tr><td>{medal}</td><td><b>{row['Jugador']}</b></td><td style='text-align:right; font-weight:bold; color:#1E90FF;'>{row['Puntos']} pts</td></tr>"
            tabla_html += "</table>"
            st.markdown(tabla_html, unsafe_allow_html=True)
        
        # 3. BOTÓN DE REFRESH ABSOLUTO
        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
        if st.button("🔄 Forzar Recálculo de Puntos", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
            
# --- PESTAÑA 4: PANEL ADMINISTRADOR (UX INTELIGENTE) ---
    if tab_a:
        with tab_a:
            st.markdown("### ⚙️ Cargar Resultados Oficiales")
            for m in matches:
                match_id = m["id"]
                
                # 1. DETECTOR DE UX: Evaluamos si el partido ya fue procesado y guardado en la BD
                tiene_resultado = m["home_score"] is not None
                
                curr_h = m["home_score"] if tiene_resultado else 0
                curr_a = m["away_score"] if tiene_resultado else 0
                
                with st.container(border=True):
                    info_juego = f"🏆 {m.get('round', 'Jornada')} | 🇻🇪 {m.get('venezuela_time', '00:00')}"
                    st.caption(f"🆔 Partido #{match_id} | {info_juego}")
                    
                    # 2. BANNER DE CERTEZA VISUAL: Para que el scroll no sea soso
                    if tiene_resultado:
                        st.markdown(f"""
                        <div style="background-color: #FCE8E6; color: #C5221F; border-left: 4px solid #EA4335; padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: bold; margin-bottom: 8px; text-align: center;">
                            📢 RESULTADO OFICIAL PUBLICADO: {int(curr_h)} - {int(curr_a)}
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with st.form(key=f"admin_form_{match_id}"):
                        url_home = FLAG_CDN_URL.format(code=TEAM_FLAGS.get(m['home_team'], DEFAULT_FLAG_CODE))
                        url_away = FLAG_CDN_URL.format(code=TEAM_FLAGS.get(m['away_team'], DEFAULT_FLAG_CODE))
                        
                        # FILA 1 ADMIN
                        c1_h, c2_h = st.columns([5.5, 4.5])
                        with c1_h:
                            st.markdown(f"<p class='team-text-container'><img src='{url_home}' width='18'> <b>{m['home_team']}</b></p>", unsafe_allow_html=True)
                        with c2_h:
                            res_h = st.selectbox("H", options=list(range(11)), index=int(curr_h), key=f"ah_{match_id}", label_visibility="collapsed")
                        
                        # FILA 2 ADMIN
                        c1_a, c2_a = st.columns([5.5, 4.5])
                        with c1_a:
                            st.markdown(f"<p class='team-text-container'><img src='{url_away}' width='18'> <b>{m['away_team']}</b></p>", unsafe_allow_html=True)
                        with c2_a:
                            res_a = st.selectbox("A", options=list(range(11)), index=int(curr_a), key=f"aa_{match_id}", label_visibility="collapsed")
                        
                        # 🟢 3. BOTÓN INTELIGENTE: Cambia dinámicamente de color y etiqueta
                        texto_btn = f"🔄 Actualizar Score (Guardado: {int(curr_h)} - {int(curr_a)})" if tiene_resultado else "🚀 Publicar Resultado Oficial"
                        tipo_btn = "secondary" if tiene_resultado else "primary"
                        
                        if st.form_submit_button(texto_btn, use_container_width=True, type=tipo_btn):
                            supabase.table("matches").update({"home_score": res_h, "away_score": res_a}).eq("id", match_id).execute()
                            
                            # Limpiamos explícitamente el caché para que la pestaña 3 recalcule en el acto
                            st.cache_data.clear() 
                            
                            st.toast("📢 Puntos recalculated con éxito.", icon="🚀")
                            st.rerun()