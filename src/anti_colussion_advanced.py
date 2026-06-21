import os
import math
import toml
import numpy as np
import pandas as pd
from scipy.spatial.distance import jensenshannon
import plotly.express as px
from src.config import config
from supabase import create_client

class AdvancedCollusionEngine:
    def __init__(self, raw_predictions: list, raw_users: list, raw_matches: list):
        """Motor Forense Multidimensional: Margen de Goles, Shannon y Perfil de Riesgo."""
        self.params = config.get_section("advanced_collusion_audit")
        self.thresh_margin = self.params.get("margin_similarity_threshold", 0.85)
        self.thresh_shannon = self.params.get("shannon_similarity_threshold", 0.70)
        self.thresh_risk = self.params.get("risk_profile_threshold", 0.90)

        self.user_map = {u["id"]: u["name"] for u in raw_users}
        self.match_map = {m["id"]: f"[{m['id']}] {m.get('local', 'Loc')}-{m.get('visitante', 'Vis')}" for m in raw_matches}
        
        self.df_base = self._preprocesar_datos(raw_predictions)
        self.usuarios = sorted(list(self.df_base["usuario"].unique()))

    def _preprocesar_datos(self, predictions: list) -> pd.DataFrame:
        if not predictions: return pd.DataFrame()
        df = pd.DataFrame(predictions)
        
        df = df.dropna(subset=["home_score", "away_score"]).copy()
        df["home_score"] = pd.to_numeric(df["home_score"], errors="coerce")
        df["away_score"] = pd.to_numeric(df["away_score"], errors="coerce")
        df = df.dropna(subset=["home_score", "away_score"])

        # Derivaciones matemáticas para las tres métricas
        df["margen_goles"] = df["home_score"] - df["away_score"]
        df["total_goles"] = df["home_score"] + df["away_score"]
        df["marcador_exacto"] = df["home_score"].astype(int).astype(str) + "-" + df["away_score"].astype(int).astype(str)
        
        df["usuario"] = df["user_id"].map(self.user_map)
        df["partido"] = df["match_id"].map(self.match_map)
        
        return df[["usuario", "partido", "marcador_exacto", "margen_goles", "total_goles"]].dropna()

    def metric_margen_goles(self) -> pd.DataFrame:
        """METODOLOGÍA 1: Distancia MAE sobre el Margen de Goles."""
        df_pivot = self.df_base.pivot(index="usuario", columns="partido", values="margen_goles")
        matriz_similitud = pd.DataFrame(0.0, index=self.usuarios, columns=self.usuarios)
        
        for u1 in self.usuarios:
            for u2 in self.usuarios:
                if u1 == u2:
                    matriz_similitud.loc[u1, u2] = 1.0
                    continue
                
                # Filtrar solo partidos donde AMBOS votaron
                mask = df_pivot.loc[u1].notna() & df_pivot.loc[u2].notna()
                if mask.sum() > 0:
                    v1 = df_pivot.loc[u1, mask]
                    v2 = df_pivot.loc[u2, mask]
                    mae = np.mean(np.abs(v1 - v2))
                    # Normalización: Penalización suave. MAE de 0 es 100% similitud. MAE > 4 es 0%.
                    similitud = max(0.0, 1.0 - (mae / 4.0))
                    matriz_similitud.loc[u1, u2] = similitud
                    
        return matriz_similitud

    def metric_shannon_surprise(self) -> pd.DataFrame:
        """METODOLOGÍA 2: Ponderación de coincidencias por la Rareza del marcador."""
        df_pivot = self.df_base.pivot(index="usuario", columns="partido", values="marcador_exacto")
        info_dict = {}
        
        # Calcular Sorpresa (-log2(P)) para cada marcador de cada partido
        for col in df_pivot.columns:
            frecuencias = df_pivot[col].value_counts(normalize=True)
            info_dict[col] = frecuencias.apply(lambda p: -math.log2(p) if p > 0 else 0).to_dict()
            
        matriz_similitud = pd.DataFrame(0.0, index=self.usuarios, columns=self.usuarios)
        
        for u1 in self.usuarios:
            for u2 in self.usuarios:
                if u1 == u2:
                    matriz_similitud.loc[u1, u2] = 1.0
                    continue
                
                info_compartida = 0.0
                info_total_posible = 0.0
                
                for partido in df_pivot.columns:
                    m1 = df_pivot.loc[u1, partido]
                    m2 = df_pivot.loc[u2, partido]
                    
                    if pd.notna(m1) and pd.notna(m2):
                        peso_sorpresa = info_dict[partido].get(m1, 0)
                        info_total_posible += peso_sorpresa
                        
                        # Si coinciden exactamente, se suman los puntos de sorpresa
                        if m1 == m2:
                            info_compartida += peso_sorpresa
                            
                # Similitud de Shannon Normalizada
                if info_total_posible > 0:
                    matriz_similitud.loc[u1, u2] = info_compartida / info_total_posible
                    
        return matriz_similitud

    def metric_perfil_riesgo(self) -> pd.DataFrame:
        """METODOLOGÍA 3: Distancia de Jensen-Shannon sobre tendencias de Goles Totales."""
        # Categorizamos el riesgo: 0-1 goles (cerrado), 2-3 (normal), 4+ (arriesgado)
        bins = [-1, 1, 3, 100]
        labels = ['Bajo', 'Medio', 'Alto']
        self.df_base['riesgo'] = pd.cut(self.df_base['total_goles'], bins=bins, labels=labels)
        
        # Crear distribuciones de probabilidad por usuario
        distribuciones = {}
        for u in self.usuarios:
            counts = self.df_base[self.df_base["usuario"] == u]["riesgo"].value_counts(normalize=True)
            # Asegurar que el vector siempre tenga las 3 categorías en el mismo orden
            dist = np.array([counts.get('Bajo', 0), counts.get('Medio', 0), counts.get('Alto', 0)])
            distribuciones[u] = dist

        matriz_similitud = pd.DataFrame(0.0, index=self.usuarios, columns=self.usuarios)
        for u1 in self.usuarios:
            for u2 in self.usuarios:
                if u1 == u2:
                    matriz_similitud.loc[u1, u2] = 1.0
                else:
                    d1, d2 = distribuciones[u1], distribuciones[u2]
                    # Divergencia JS requiere que la suma sea > 0
                    if np.sum(d1) > 0 and np.sum(d2) > 0:
                        js_dist = jensenshannon(d1, d2)
                        matriz_similitud.loc[u1, u2] = 1.0 - js_dist
                        
        return matriz_similitud

    def ejecutar_auditoria_integral(self):
        """Ejecuta los tres modelos y consolida un reporte si alguna de las métricas salta."""
        print("[ANALÍTICA] 1. Calculando distancias por Margen de Goles...")
        sim_margin = self.metric_margen_goles()
        
        print("[ANALÍTICA] 2. Calculando ponderaciones de Sorpresa (Info. Shannon)...")
        sim_shannon = self.metric_shannon_surprise()
        
        print("[ANALÍTICA] 3. Calculando divergencias de Perfil de Riesgo (JSD)...")
        sim_risk = self.metric_perfil_riesgo()

        self.generar_mapas_termicos(sim_margin, sim_shannon, sim_risk)

        alertas = []
        for i in range(len(self.usuarios)):
            for j in range(i + 1, len(self.usuarios)):
                u1, u2 = self.usuarios[i], self.usuarios[j]
                
                m_score = sim_margin.loc[u1, u2]
                s_score = sim_shannon.loc[u1, u2]
                r_score = sim_risk.loc[u1, u2]
                
                # ¿Superan el umbral en alguna de las tres métricas?
                if (m_score >= self.thresh_margin or 
                    s_score >= self.thresh_shannon or 
                    r_score >= self.thresh_risk):
                    
                    alertas.append({
                        "Jugador_A": u1,
                        "Jugador_B": u2,
                        "Margen (Estructura)": f"{m_score*100:.1f}%",
                        "Shannon (Sorpresa)": f"{s_score*100:.1f}%",
                        "Riesgo (Comportamiento)": f"{r_score*100:.1f}%",
                        "Alerta": "🔴 SÍ"
                    })

        df_reporte = pd.DataFrame(alertas)
        return df_reporte.sort_values(by="Shannon (Sorpresa)", ascending=False) if not df_reporte.empty else pd.DataFrame()

    def generar_mapas_termicos(self, m_margin, m_shannon, m_risk, output_dir="data/reports_advanced"):
        """Exporta las 3 matrices térmicas para inspección visual."""
        os.makedirs(output_dir, exist_ok=True)
        
        px.imshow(m_margin, text_auto=".2f", color_continuous_scale="Blues", title="Similitud por Margen de Goles").write_html(os.path.join(output_dir, "heatmap_margin.html"))
        px.imshow(m_shannon, text_auto=".2f", color_continuous_scale="Oranges", title="Similitud por Sorpresa (Shannon)").write_html(os.path.join(output_dir, "heatmap_shannon.html"))
        px.imshow(m_risk, text_auto=".2f", color_continuous_scale="Greens", title="Similitud de Perfil de Riesgo (JSD)").write_html(os.path.join(output_dir, "heatmap_risk.html"))
        print(f"[VISUALIZACIÓN] 3 Mapas de Calor exportados a: {os.path.abspath(output_dir)}")

# =====================================================================
# EJECUCIÓN
# =====================================================================
if __name__ == "__main__":
    print("🔌 Conectando a Supabase para Auditoría Avanzada Multidimensional...")
    try:
        secrets = toml.load(".streamlit/secrets.toml")
        supabase = create_client(secrets["supabase"]["url"], secrets["supabase"]["key"])
        
        print("📥 Descargando datos de juego...")
        pronosticos = supabase.table("predictions_log").select("*").execute().data
        matches = supabase.table("matches").select("*").execute().data
        users = supabase.table("users").select("id, name").execute().data
        jugadores = [u for u in users if not u.get("is_admin", False) and u["name"].strip().lower() != "admin"]
        
        if pronosticos and jugadores and matches:
            engine = AdvancedCollusionEngine(pronosticos, jugadores, matches)
            reporte_avanzado = engine.ejecutar_auditoria_integral()
            
            print("\n" + "="*80 + "\n 🧬 REPORTE FORENSE MULTIDIMENSIONAL (Márgenes, Sorpresa y Riesgo)\n" + "="*80)
            if not reporte_avanzado.empty:
                print(reporte_avanzado.to_string(index=False))
                print("\n[NOTA] Un puntaje alto en 'Shannon' es la prueba más fuerte de colusión.")
            else:
                print("✅ Limpio. Ningún par de usuarios supera los umbrales dinámicos avanzados.")
    except Exception as e:
        print(f"❌ Error de ejecución: {e}")