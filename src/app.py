# Ruta del archivo: src/app.py
import streamlit as st
from datetime import datetime, timezone, timedelta
from auth import authenticate_user, hash_password
from config import TEAM_FLAGS, LOCK_WINDOW_HOURS, REVELATION_WINDOW_MINUTES, FLAG_CDN_URL, DEFAULT_FLAG_CODE, USUARIOS_EXCLUIDOS
from database import (
    fetch_all_matches, 
    fetch_latest_user_predictions, 
    save_prediction_log, 
    get_leaderboard_data,
    supabase,
    fetch_all_users,
    update_user_password,
    normalizar_nombre
)

# --- INYECCIÓN DE CSS CALIBRADO PARA MÓVILES ---
st.markdown("""
<style>
    html, body, .main, section[data-testid="stMain"], [data-testid="stApp"], [data-testid="stAppViewBlockContainer"], [data-testid="stAppViewContainer"] {
        overflow-x: hidden !important;
    }
    header[data-testid="stHeader"] { display: none !important; }
    div[data-testid="stTabs"] > div:first-child {
        position: -webkit-sticky; position: sticky; top: 0; background-color: #FFFFFF;
        z-index: 9999; padding-top: 4px; padding-bottom: 4px; border-bottom: 1px solid #E0E0E0;
    }
    .block-container { padding-top: 0.5rem !important; padding-bottom: 0.5rem !important; }
    div[data-testid="stForm"] { padding: 8px !important; overflow: hidden !important; }
    div[data-testid="stForm"] div[data-testid="stHorizontalBlock"] {
        flex-direction: row !important; flex-wrap: nowrap !important; align-items: center !important;
        gap: 6px !important; padding-right: 50px !important; box-sizing: border-box !important;
        margin-left: 0 !important; margin-right: 0 !important; width: 100% !important;
    }
    div[data-testid="stForm"] div[data-testid="column"] { min-width: 0 !important; flex-shrink: 1 !important; }
    div[data-testid="stForm"] div[data-testid="stSelectbox"] { max-width: 65px !important; width: 100% !important; margin: 0 !important; }
    .team-text-container {
        margin-top: -20px !important; margin-bottom: 0 !important; margin-left: 0 !important; margin-right: 0 !important;
        font-size: 14px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; display: block !important; width: 100%;
    }
    .team-text-container img { vertical-align: middle !important; margin-right: 6px !important; margin-top: -2px !important; }
    div[data-testid="stFormSubmitButton"] { margin-top: -10px !important; }
    div[data-testid="stForm"] > div[data-testid="stVerticalBlockBorderWrapper"] > div > div[data-testid="stVerticalBlock"] { gap: 2px !important; }
    
    /* ESTILOS NUEVOS PARA LA TABLA LEADERBOARD MOBILE-FIRST */
    .tabla-leaderboard { width: 100%; border-collapse: collapse; font-size: 15px; }
    .tabla-leaderboard th { background-color: #F8F9FA; color: #212529; text-align: left; padding: 8px; border-bottom: 2px solid #E0E0E0; font-size: 13px;}
    .tabla-leaderboard td { padding: 8px; border-bottom: 1px solid #F1F1F1; vertical-align: middle; }
    .micro-data { font-size: 11px; color: #5F6368; margin-top: 3px; letter-spacing: 0.2px; }
    .racha { font-size: 12px; font-weight: bold; margin-top: 2px; }
    .trend-up { color: #1E8E3E; font-size: 11px; font-weight: bold; margin-left: 4px; }
    .trend-down { color: #D93025; font-size: 11px; font-weight: bold; margin-left: 4px; }
    .trend-flat { color: #80868B; font-size: 11px; font-weight: bold; margin-left: 4px; }
</style>
""", unsafe_allow_html=True)

if authenticate_user():
    user = st.session_state.user_info
    now_utc = datetime.now(timezone.utc)
    tz_ve = timezone(timedelta(hours=-4))
    
    # --- BARRA LATERAL UNIFICADA ---
    with st.sidebar:
        st.markdown(f"### 👤 Perfil")
        st.markdown(f"**Nombre:** {user['name']}")
        st.markdown(f"**Rol:** {'Administrador 🛠️' if user['is_admin'] else 'Jugador 🏃'}")
        st.divider()
        with st.expander("🔑 Cambiar mi Contraseña"):
            with st.form("change_password_sidebar_form", clear_on_submit=True):
                nueva_clave = st.text_input("Nueva Contraseña", type="password", placeholder="Mínimo 6 caracteres")
                confirmar_clave = st.text_input("Confirmar Contraseña", type="password", placeholder="Repite la contraseña")
                submit_clave = st.form_submit_button("Actualizar Clave", use_container_width=True)
                
                if submit_clave:
                    if len(nueva_clave) < 6: st.error("La contraseña debe tener al menos 6 caracteres.")
                    elif nueva_clave != confirmar_clave: st.error("Las contraseñas no coinciden.")
                    else:
                        nuevo_hash = hash_password(nueva_clave)
                        if update_user_password(user["id"], nuevo_hash):
                            st.success("¡Clave actualizada!")
                            st.toast("Contraseña cambiada con éxito. 🔐", icon="🎉")
        st.divider()
        if st.button("🚪 Cerrar Sesión", use_container_width=True, type="secondary", key="sidebar_logout_btn"):
            st.session_state.authenticated = False
            st.session_state.user_info = None
            st.rerun()
    
    # 1. Carga de datos base
    matches = fetch_all_matches()
    user_preds = fetch_latest_user_predictions(user["id"])
    
    # Precalcular el partido inaugural de cada jornada
    primer_partido_por_round = {}
    for m in matches:
        r_name = m.get("round", "Jornada")
        if m.get("match_time"):
            m_time = datetime.fromisoformat(m["match_time"].replace("Z", "+00:00"))
            if r_name not in primer_partido_por_round or m_time < primer_partido_por_round[r_name]:
                primer_partido_por_round[r_name] = m_time

    # 2. Configuración dinámica de Pestañas
    if user["is_admin"]:
        tab_p, tab_g, tab_t, tab_a = st.tabs(["📝 Votos", "👥 Grupo", "📊 Tabla", "⚙️ Admin"])
    else:
        tab_p, tab_g, tab_t = st.tabs(["📝 Mis Pronósticos", "👥 Grupo", "📊 Tabla"])
        tab_a = None

    # --- PESTAÑA 1: MIS PRONÓSTICOS ---
    with tab_p:
        filtro_vista = st.selectbox("🔍 Filtrar partidos:", ["📅 Hoy y Mañana", "⏳ Pendientes por Pronosticar", "📖 Ver Todo el Fixture"], label_visibility="collapsed")
        
        matches_filtrados = []
        for m in matches:
            match_id = m["id"]
            round_name = m.get("round", "Jornada")
            match_time = datetime.fromisoformat(m["match_time"].replace("Z", "+00:00"))
            
            primer_juego_time = primer_partido_por_round.get(round_name, match_time)
            time_limit = primer_juego_time - timedelta(hours=1)
            is_locked = now_utc >= time_limit
            
            date_juego = match_time.astimezone(tz_ve).date()
            date_hoy = now_utc.astimezone(tz_ve).date()
            date_manana = date_hoy + timedelta(days=1)
            tiene_prediccion = match_id in user_preds

            if filtro_vista == "📅 Hoy y Mañana":
                if date_juego == date_hoy or date_juego == date_manana: matches_filtrados.append((m, match_time, is_locked, time_limit))
            elif filtro_vista == "⏳ Pendientes por Pronosticar":
                if not tiene_prediccion and not is_locked: matches_filtrados.append((m, match_time, is_locked, time_limit))
            else: matches_filtrados.append((m, match_time, is_locked, time_limit))
        
        if not matches_filtrados: st.info("No hay partidos en este filtro. 🙌")
        
        for m, match_time, is_locked, time_limit in matches_filtrados:
            match_id = m["id"]
            tiene_prediccion = match_id in user_preds
            saved_home = user_preds[match_id]["home_score"] if tiene_prediccion else 0
            saved_away = user_preds[match_id]["away_score"] if tiene_prediccion else 0
            
            with st.container(border=True):
                info_juego = f"🏆 {m.get('round', 'Jornada')} | 🇻🇪 {m.get('venezuela_time', '00:00')}"
                estado = "🔒 BLOQUEADO" if is_locked else "🟢 Abierto"
                if tiene_prediccion and not is_locked: estado += " | 💾 ¡PRONÓSTICO GUARDADO!"
                st.caption(f"{estado}\n\n{info_juego}")
                if tiene_prediccion and not is_locked: st.success(f"✓ Tu voto actual: {int(saved_home)} - {int(saved_away)}", icon="ℹ️")
                
                with st.form(key=f"user_form_{match_id}"):
                    if tiene_prediccion:
                        st.markdown(f"""
                        <div style="background-color: #E6F4EA; color: #137333; border-left: 4px solid #1E8E3E; padding: 4px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; margin-bottom: 6px; text-align: center;">
                            ✓ TU PRONÓSTICO ES: {int(saved_home)} - {int(saved_away)}
                        </div>""", unsafe_allow_html=True)
                    
                    url_home = FLAG_CDN_URL.format(code=TEAM_FLAGS.get(m['home_team'], DEFAULT_FLAG_CODE))
                    url_away = FLAG_CDN_URL.format(code=TEAM_FLAGS.get(m['away_team'], DEFAULT_FLAG_CODE))
                    
                    c1_h, c2_h = st.columns([5.5, 4.5])
                    with c1_h: st.markdown(f"<p class='team-text-container'><img src='{url_home}' width='18'> <b>{m['home_team']}</b></p>", unsafe_allow_html=True)
                    with c2_h: h_in = st.selectbox("H", options=list(range(11)), index=int(saved_home), key=f"uh_{match_id}", disabled=is_locked, label_visibility="collapsed")
                    
                    c1_a, c2_a = st.columns([5.5, 4.5])
                    with c1_a: st.markdown(f"<p class='team-text-container'><img src='{url_away}' width='18'> <b>{m['away_team']}</b></p>", unsafe_allow_html=True)
                    with c2_a: a_in = st.selectbox("A", options=list(range(11)), index=int(saved_away), key=f"ua_{match_id}", disabled=is_locked, label_visibility="collapsed")
                    
                    if not is_locked:
                        texto_btn = f"🔄 Actualizar (Registrado: {int(saved_home)} - {int(saved_away)})" if tiene_prediccion else "💾 Guardar Pronóstico"
                        if st.form_submit_button(texto_btn, use_container_width=True, type="secondary" if tiene_prediccion else "primary"):
                            save_prediction_log(user["id"], match_id, h_in, a_in)
                            st.toast("💾 ¡Pronóstico guardado exitosamente!", icon="✅")
                            st.rerun()
                    else: st.form_submit_button(f"Ya no puedes cambiar tu pronóstico: {int(saved_home)} - {int(saved_away)}", disabled=True, use_container_width=True)

    # --- PESTAÑA 2: GRUPO ---
    with tab_g:
        st.markdown("### 👥 Juegos Abiertos")
        round_actual = ""
        if matches:
            partido_mas_cercano = min(matches, key=lambda x: abs((datetime.fromisoformat(x["match_time"].replace("Z", "+00:00")) - now_utc).total_seconds()))
            round_actual = partido_mas_cercano.get("round", "Jornada")
        
        dict_rounds = {}
        for m in matches:
            r = m.get("round", "Jornada")
            if r not in dict_rounds: dict_rounds[r] = []
            dict_rounds[r].append(m)
            
        for round_name, juegos in dict_rounds.items():
            tiempos_juegos = [datetime.fromisoformat(j["match_time"].replace("Z", "+00:00")) for j in juegos]
            primer_juego_del_round = min(tiempos_juegos)
            hora_revelacion = primer_juego_del_round - timedelta(minutes=REVELATION_WINDOW_MINUTES)
            revelado = now_utc >= hora_revelacion
            
            with st.expander(f"🏆 {round_name}", expanded=(round_name == round_actual)):
                logs_all = supabase.table("predictions_log").select("*").execute().data
                all_users = [u for u in fetch_all_users() if not u.get("is_admin", False) and str(u.get("is_admin")).strip().lower() != "true" and u["name"].strip().lower() not in ["admin", "administrator", "administrador"]]
                
                if not revelado:
                    hora_ve_revelacion = hora_revelacion.astimezone(tz_ve).strftime("%I:%M %p")
                    st.caption(f"🔒 Los pronósticos de este bloque se liberarán a las {hora_ve_revelacion} ({REVELATION_WINDOW_MINUTES} min antes del primer juego).")
                
                for j in juegos:
                    st.markdown(f"**⚽ {j['home_team']} vs {j['away_team']}**")
                    # 🟢 LISTA DE EXCLUSIÓN PARA ELIMINATORIAS
                    usuarios_excluidos = USUARIOS_EXCLUIDOS
                    for u in all_users:
                        if normalizar_nombre(u["name"]) in usuarios_excluidos:
                            continue
                        is_me = (u["id"] == user["id"])
                        user_log = [l for l in logs_all if l["user_id"] == u["id"] and l["match_id"] == j["id"]]
                        nombre_mostrar = f"• **Tú**" if is_me else f"• *{u['name']}*"
                        
                        if user_log:
                            ultimo_voto = sorted(user_log, key=lambda x: x["id"], reverse=True)[0]
                            if revelado or is_me: st.markdown(f"{nombre_mostrar}: {int(ultimo_voto['home_score'])} - {int(ultimo_voto['away_score'])}")
                            else: st.markdown(f"{nombre_mostrar}: Ya envió su pronóstico 🔒")
                        else:
                            if is_me: st.markdown(f"{nombre_mostrar}: Aún no has votado 🤷‍♂️")
                            else: st.markdown(f"{nombre_mostrar}: Aún no envió su pronóstico ⏳")
                    st.divider()
                    
    # --- PESTAÑA 3: TABLA DE POSICIONES COMPACTA CON MICRO-DATOS ---
    with tab_t:
        st.markdown("### 🏆 Tabla de Posiciones")
        
        def calculate_match_points(pred_home: int, pred_away: int, real_home: int, real_away: int) -> int:
            if pred_home == real_home and pred_away == real_away: return 5
            real_trend = "H" if real_home > real_away else ("A" if real_away > real_home else "D")
            pred_trend = "H" if pred_home > pred_away else ("A" if pred_away > pred_home else "D")
            if real_trend == pred_trend: return 3
            return 0

        # 1. PREPARACIÓN DE DATOS (ADAPTADO A ELIMINATORIAS DE OCTAVOS)
        todos_usuarios = fetch_all_users()
        logs_all = supabase.table("predictions_log").select("*").execute().data
        matches_db = supabase.table("matches").select("*").execute().data
        
        # 🟢 FILTRO DE RESET: Partidos jugados ordenados cronológicamente EXCLUYENDO la Fase de Grupos ("Jornada")
        partidos_jugados = [
            m for m in matches_db 
            if m.get("home_score") is not None 
            and str(m.get("home_score")).strip() != ""
            and "jornada" not in str(m.get("round", "")).strip().lower() # 🔥 Deja por fuera el pasado
        ]
        partidos_jugados.sort(key=lambda x: x.get("match_time", ""))
        
        leaderboard_data = []
        
        # 🟢 LISTA DE EXCLUSIÓN: Jugadores que ya no participan de aquí en adelante
        usuarios_excluidos = USUARIOS_EXCLUIDOS
        
        # Buscar el último partido (para el cálculo de la tendencia)
        max_time = partidos_jugados[-1].get("match_time", "") if partidos_jugados else ""
        
        for u in todos_usuarios:
            if u.get("is_admin", False) or normalizar_nombre(u["name"]) in ["admin", "administrator"]: continue
            # 🟢 FILTRO DE JUGADORES: Si el usuario actual está retirado, lo saltamos y no va a la tabla
            if normalizar_nombre(u["name"]) in usuarios_excluidos: continue 
            
            preds_usuario = {str(l["match_id"]): l for l in sorted([log for log in logs_all if str(log["user_id"]) == str(u["id"])], key=lambda x: x.get("id", 0))}
            
            puntos_totales = 0
            puntos_previos = 0 # Puntos hasta antes del último partido
            c_5 = 0; c_3 = 0; c_0 = 0
            historial_rachas = []
            
            for match in partidos_jugados:
                m_id_str = str(match["id"])
                pts = 0
                if m_id_str in preds_usuario:
                    pred = preds_usuario[m_id_str]
                    try:
                        pts = calculate_match_points(int(pred["home_score"]), int(pred["away_score"]), int(match["home_score"]), int(match["away_score"]))
                    except: pass
                
                # Actualizar contadores absolutos
                if pts == 5: c_5 += 1
                elif pts == 3: c_3 += 1
                else: c_0 += 1
                
                puntos_totales += pts
                # Acumulador para la tabla anterior (ignorar los partidos recién jugados al mismo tiempo)
                if match.get("match_time", "") < max_time:
                    puntos_previos += pts
                    
                historial_rachas.append(pts)
            
            # Calcular Racha (Streak) desde el último partido hacia atrás
            streak_type = None
            streak_count = 0
            for pts in reversed(historial_rachas):
                if pts > 0:
                    if streak_type == 'L': break
                    streak_type = 'W'
                    streak_count += 1
                else:
                    if streak_type == 'W': break
                    streak_type = 'L'
                    streak_count += 1
                    
            leaderboard_data.append({
                "Jugador": u["name"],
                "Puntos": puntos_totales,
                "PuntosPrevios": puntos_previos,
                "C5": c_5, "C3": c_3, "C0": c_0,
                "RachaType": streak_type, "RachaCount": streak_count
            })
            
        # 2. CÁLCULO DE POSICIONES Y TENDENCIAS
        def assign_ranks(lb_list, sort_key):
            lb_list.sort(key=lambda x: x[sort_key], reverse=True)
            rank = 1
            for i, user in enumerate(lb_list):
                if i > 0 and lb_list[i][sort_key] < lb_list[i-1][sort_key]:
                    rank = i + 1
                user[f"Rank_{sort_key}"] = rank

        assign_ranks(leaderboard_data, "Puntos")
        assign_ranks(leaderboard_data, "PuntosPrevios")

        # 3. RENDERIZADO DE LA TABLA HTML
        if not partidos_jugados:
            st.info("⚽ La tabla se activará cuando el Admin cargue resultados oficiales.")
        else:
            tabla_html = "<table class='tabla-leaderboard'><tr><th style='width: 40px;'>Pos</th><th>Jugador</th><th style='text-align:right;'>Puntos</th></tr>"
            
            # Imprimir ordenados por Ranking actual
            leaderboard_data.sort(key=lambda x: x["Rank_Puntos"])
            
            for idx, row in enumerate(leaderboard_data):
                # Medallas
                if row["Rank_Puntos"] == 1: medal = "🥇"
                elif row["Rank_Puntos"] == 2: medal = "🥈"
                elif row["Rank_Puntos"] == 3: medal = "🥉"
                else: medal = f"<b>{row['Rank_Puntos']}</b>"
                
                # Flecha de Tendencia (Mejorada con íconos geométricos sólidos y colores UX)
                diff = row["Rank_PuntosPrevios"] - row["Rank_Puntos"]
                if diff > 0:
                    trend_html = f"<span style='color: #1E8E3E; font-weight: bold; margin-left: 8px; font-size: 13px;'>▲ {diff}</span>"
                elif diff < 0:
                    trend_html = f"<span style='color: #D93025; font-weight: bold; margin-left: 8px; font-size: 13px;'>▼ {abs(diff)}</span>"
                else:
                    trend_html = "<span style='color: #212121; font-weight: bold; margin-left: 8px; font-size: 13px;'>■</span>"
                    
                if not max_time: trend_html = ""
                
                # Racha HTML
                racha_txt = f"🔥 {row['RachaCount']}" if row["RachaType"] == 'W' else (f"❄️ {row['RachaCount']}" if row["RachaType"] == 'L' else "-")
                color_racha = '#E65100' if row['RachaType'] == 'W' else '#0288D1'
                racha_html = f"<span class='racha' style='color: {color_racha}; margin-left: 8px;'>{racha_txt}</span>"
                
                # Concatenación optimizada
                tabla_html += "<tr>"
                
                # Celda 1: Posición
                tabla_html += f"<td>{medal}</td>"
                
                # Celda 2: Nombre + Micro-Data + Tendencia
                tabla_html += f"<td><b>{row['Jugador']}</b><span class='micro-data' style='margin-left: 8px;'>🎯 {row['C5']} | 📈 {row['C3']} | ❌ {row['C0']}</span> {trend_html}</td>"
                
                # Celda 3: Puntos (Tamaño aumentado a 16px) + Racha
                tabla_html += f"<td style='text-align:right;'><span style='font-weight:900; color:#1E90FF; font-size:16px;'>{row['Puntos']} </span>{racha_html}</td>"
                
                tabla_html += "</tr>"
                
            tabla_html += "</table>"
            st.markdown(tabla_html, unsafe_allow_html=True)
            
            # Leyenda sutil
            st.markdown("<div style='font-size: 11px; color: #888; text-align: center; margin-top: 10px;'>🎯 Exacto (5pts) | 📈 Ganador (3pts) | ❌ Fallo (0pts)</div>", unsafe_allow_html=True)
        
        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
        if st.button("🔄 Forzar Recálculo de Puntos", use_container_width=True, key="btn_recalculo_leaderboard"):
            st.cache_data.clear()
            st.rerun()
            
            
    # --- PESTAÑA 4: ADMIN ---
    if tab_a:
        with tab_a:
            st.markdown("### ⚙️ Cargar Resultados Oficiales")
            for m in matches:
                match_id = m["id"]
                tiene_resultado = m["home_score"] is not None
                curr_h = m["home_score"] if tiene_resultado else 0
                curr_a = m["away_score"] if tiene_resultado else 0
                
                with st.container(border=True):
                    info_juego = f"🏆 {m.get('round', 'Jornada')} | 🇻🇪 {m.get('venezuela_time', '00:00')}"
                    st.caption(f"🆔 Partido #{match_id} | {info_juego}")
                    
                    if tiene_resultado:
                        st.markdown(f"""
                        <div style="background-color: #FCE8E6; color: #C5221F; border-left: 4px solid #EA4335; padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: bold; margin-bottom: 8px; text-align: center;">
                            📢 RESULTADO OFICIAL: {int(curr_h)} - {int(curr_a)}
                        </div>""", unsafe_allow_html=True)
                    
                    with st.form(key=f"admin_form_{match_id}"):
                        url_home = FLAG_CDN_URL.format(code=TEAM_FLAGS.get(m['home_team'], DEFAULT_FLAG_CODE))
                        url_away = FLAG_CDN_URL.format(code=TEAM_FLAGS.get(m['away_team'], DEFAULT_FLAG_CODE))
                        
                        c1_h, c2_h = st.columns([5.5, 4.5])
                        with c1_h: st.markdown(f"<p class='team-text-container'><img src='{url_home}' width='18'> <b>{m['home_team']}</b></p>", unsafe_allow_html=True)
                        with c2_h: res_h = st.selectbox("H", options=list(range(11)), index=int(curr_h), key=f"ah_{match_id}", label_visibility="collapsed")
                        
                        c1_a, c2_a = st.columns([5.5, 4.5])
                        with c1_a: st.markdown(f"<p class='team-text-container'><img src='{url_away}' width='18'> <b>{m['away_team']}</b></p>", unsafe_allow_html=True)
                        with c2_a: res_a = st.selectbox("A", options=list(range(11)), index=int(curr_a), key=f"aa_{match_id}", label_visibility="collapsed")
                        
                        texto_btn = f"🔄 Actualizar Score (Guardado: {int(curr_h)} - {int(curr_a)})" if tiene_resultado else "🚀 Publicar Resultado Oficial"
                        if st.form_submit_button(texto_btn, use_container_width=True, type="secondary" if tiene_resultado else "primary"):
                            supabase.table("matches").update({"home_score": res_h, "away_score": res_a}).eq("id", match_id).execute()
                            st.cache_data.clear() 
                            st.toast("📢 Puntos recalculados con éxito.", icon="🚀")
                            st.rerun()