import numpy as np
import pandas as pd
from scipy.spatial.distance import pdist, squareform
from scipy.cluster.hierarchy import linkage, fcluster
from sklearn.cluster import DBSCAN
import networkx as nx
import plotly.graph_objects as go
import plotly.express as px
import plotly.figure_factory as ff
from src.config import config
import os
import time
import toml
from supabase import create_client

class QuinielaAntiCollusionEngine:
    def __init__(self, raw_predictions: list, raw_users: list, raw_matches: list):
        audit_params = config.get_section("anti_collusion_audit")
        self.max_consensus = audit_params.get("max_expert_consensus", 0.85)
        self.alert_threshold = audit_params.get("similarity_alert_threshold", 0.80)
        self.dbscan_eps = audit_params.get("dbscan_eps", 0.20)
        self.dbscan_min_samples = audit_params.get("dbscan_min_samples", 2)
        
        self.user_map = {u["id"]: u["name"] for u in raw_users}
        self.match_map = {m["id"]: f"{m.get('local', 'Loc')}-{m.get('visitante', 'Vis')}" for m in raw_matches}
        self.df_matrix = self._construir_matriz_pivot(raw_predictions)
        
    def _construir_matriz_pivot(self, predictions: list) -> pd.DataFrame:
        if not predictions: return pd.DataFrame()
        df = pd.DataFrame(predictions)
        df["marcador_exacto"] = df["home_score"].astype(str) + "-" + df["away_score"].astype(str)
        df_pivot = df.pivot(index="user_id", columns="match_id", values="marcador_exacto")
        df_pivot.index = df_pivot.index.map(self.user_map)
        df_pivot.columns = df_pivot.columns.map(lambda m_id: f"[{m_id}] {self.match_map.get(m_id, 'Partido')}")
        
        # Corrección Teórica: Los valores faltantes se marcan pero no se cruzarán positivamente
        return df_pivot.dropna(how="all").fillna("MISSING")

    def aplicar_filtro_entropia(self) -> pd.DataFrame:
        df_filtrado = self.df_matrix.copy()
        partidos_a_mantener = []
        for col in df_filtrado.columns:
            try:
                col_data = df_filtrado.loc[:, col]
                if isinstance(col_data, pd.DataFrame): col_data = col_data.iloc[:, 0]
                
                # Ignoramos los 'MISSING' para calcular el consenso real
                col_data_valid = col_data[col_data != "MISSING"]
                if len(col_data_valid) == 0: continue
                
                top_option_percentage = col_data_valid.value_counts(normalize=True).max()
                if top_option_percentage < self.max_consensus:
                    partidos_a_mantener.append(col)
            except Exception:
                partidos_a_mantener.append(col)
                
        return df_filtrado[partidos_a_mantener]

    def calcular_matrices_distancia(self, df_analisis: pd.DataFrame) -> tuple:
        df_numeric = df_analisis.apply(lambda x: pd.factorize(x)[0])
        hamming_distances = pdist(df_numeric.values, metric="hamming")
        matrix_hamming = squareform(hamming_distances)
        matrix_similarity = 1.0 - matrix_hamming
        df_similarity = pd.DataFrame(matrix_similarity, index=df_analisis.index, columns=df_analisis.index)
        return df_similarity, matrix_hamming, hamming_distances

    def ejecutar_clustering(self, df_similarity: pd.DataFrame, matrix_hamming: np.ndarray, hamming_distances: np.ndarray) -> tuple:
        usuarios = df_similarity.index.tolist()
        dbscan = DBSCAN(eps=self.dbscan_eps, min_samples=self.dbscan_min_samples, metric="precomputed")
        labels_dbscan = dbscan.fit_predict(matrix_hamming)
        linked = linkage(hamming_distances, method="average")
        labels_jerarquico = fcluster(linked, t=1.0 - self.alert_threshold, criterion="distance")
        
        df_clusters = pd.DataFrame({
            "Usuario": usuarios, "Clan_DBSCAN": labels_dbscan, "Grupo_Jerarquico": labels_jerarquico
        }).set_index("Usuario")
        return df_clusters, linked

    def generar_grafo_red(self, df_similarity: pd.DataFrame) -> nx.Graph:
        G = nx.Graph()
        usuarios = df_similarity.index.tolist()
        for u in usuarios: G.add_node(u)
        for i in range(len(usuarios)):
            for j in range(i + 1, len(usuarios)):
                sim = df_similarity.iloc[i, j]
                if sim >= self.alert_threshold:
                    G.add_edge(usuarios[i], usuarios[j], weight=sim)
        return G

    def emitir_reporte_sospecha(self, df_similarity: pd.DataFrame, df_clusters: pd.DataFrame) -> pd.DataFrame:
        usuarios = df_similarity.index.tolist()
        alertas = []
        for i in range(len(usuarios)):
            for j in range(i + 1, len(usuarios)):
                user_a, user_b = usuarios[i], usuarios[j]
                similitud_critica = df_similarity.loc[user_a, user_b]
                
                if similitud_critica >= self.alert_threshold:
                    mismo_clan = "SÍ" if df_clusters.loc[user_a, "Clan_DBSCAN"] == df_clusters.loc[user_b, "Clan_DBSCAN"] and df_clusters.loc[user_a, "Clan_DBSCAN"] != -1 else "NO"
                    
                    # Corrección Teórica: Cálculo REAL sobre toda la jornada, ignorando N/A
                    jugadas_a = self.df_matrix.loc[user_a]
                    jugadas_b = self.df_matrix.loc[user_b]
                    
                    # Contamos matches donde no están ausentes
                    mascara_validos = (jugadas_a != "MISSING") & (jugadas_b != "MISSING")
                    total_jugados_mutuamente = mascara_validos.sum()
                    coincidencias_exactas_totales = (jugadas_a[mascara_validos] == jugadas_b[mascara_validos]).sum()
                    
                    alertas.append({
                        "Jugador_A": user_a,
                        "Jugador_B": user_b,
                        "Similitud_Partidos_Difíciles": f"{similitud_critica*100:.1f}%",
                        "Partidos_IDÉNTICOS_Totales": f"{coincidencias_exactas_totales} de {total_jugados_mutuamente}",
                        "Mismo_Clan_Denso": mismo_clan
                    })
                    
        df_reporte = pd.DataFrame(alertas)
        return df_reporte.sort_values(by="Similitud_Partidos_Difíciles", ascending=False) if not df_reporte.empty else pd.DataFrame()

    def generar_reportes_visuales(self, df_similarity: pd.DataFrame, linkage_tree: np.ndarray, G: nx.Graph, output_dir: str = "data/reports"):
        """Genera y guarda gráficos interactivos de la auditoría en formato HTML."""
        os.makedirs(output_dir, exist_ok=True)
        usuarios = df_similarity.index.tolist()

        # 1. HEATMAP DE SIMILITUD (Matriz de Confusión)
        fig_heat = px.imshow(df_similarity, text_auto=".2f", color_continuous_scale="Reds", 
                             title="Matriz Térmica de Similitud (Partidos Críticos)")
        fig_heat.write_html(os.path.join(output_dir, "heatmap_similitud.html"))

        # 2. DENDROGRAMA DE CLUSTERING JERÁRQUICO
        fig_dendro = ff.create_dendrogram(1.0 - df_similarity.values, orientation='left', labels=usuarios)
        fig_dendro.update_layout(width=800, height=600, title="Dendrograma de Ramificación de Alianzas (Usuarios unidos cerca del 0 son idénticos)")
        fig_dendro.write_html(os.path.join(output_dir, "dendrograma_alianzas.html"))

        # 3. GRAFO DE RED ESPACIAL (Copiones y Nodos)
        pos = nx.spring_layout(G, seed=42)
        edge_x, edge_y = [], []
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])

        node_x = [pos[node][0] for node in G.nodes()]
        node_y = [pos[node][1] for node in G.nodes()]

        fig_net = go.Figure(data=[
            go.Scatter(x=edge_x, y=edge_y, line=dict(width=2, color='#888'), hoverinfo='none', mode='lines'),
            go.Scatter(x=node_x, y=node_y, mode='markers+text', text=list(G.nodes()), textposition="bottom center",
                       marker=dict(showscale=True, size=20, color="red", line_width=2))
        ])
        fig_net.update_layout(title="Red de Alianzas (Conectados = Sospecha de Copia)", showlegend=False, 
                              xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                              yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
        fig_net.write_html(os.path.join(output_dir, "grafo_red_copias.html"))
        print(f"[VISUALIZACIÓN] Gráficos interactivos guardados en: {os.path.abspath(output_dir)}")

# =====================================================================
# EJECUCIÓN
# =====================================================================
if __name__ == "__main__":
    print("🔌 Conectando a Supabase a través de secrets.toml...")
    try:
        secrets = toml.load(".streamlit/secrets.toml")
        SUPABASE_URL = secrets["supabase"]["url"]
        SUPABASE_KEY = secrets["supabase"]["key"]
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        print("📥 Descargando datos de juego...")
        pronosticos = supabase.table("predictions_log").select("*").execute().data
        matches = supabase.table("matches").select("*").execute().data
        users = supabase.table("users").select("id, name").execute().data
        jugadores = [u for u in users if not u.get("is_admin", False) and u["name"].strip().lower() != "admin"]
        
        if pronosticos and jugadores and matches:
            engine = QuinielaAntiCollusionEngine(pronosticos, jugadores, matches)
            df_critico = engine.aplicar_filtro_entropia()
            df_similitud, matrix_hamming, hamming_condensado = engine.calcular_matrices_distancia(df_critico)
            df_clusters, linkage_tree = engine.ejecutar_clustering(df_similitud, matrix_hamming, hamming_condensado)
            Grafo_Red = engine.generar_grafo_red(df_similitud)
            
            # Exportación Gráfica (¡Magia Pura!)
            engine.generar_reportes_visuales(df_similitud, linkage_tree, Grafo_Red)
            
            reporte_fraude = engine.emitir_reporte_sospecha(df_similitud, df_clusters)
            print("\n" + "="*60 + "\n 🔥 REPORTE FORENSE DE POSIBLES ALIANZAS / COPIAS\n" + "="*60)
            if not reporte_fraude.empty:
                print(reporte_fraude.to_string(index=False))
            else:
                print("✅ Limpio. No se detectaron patrones de copia o clanes sospechosos en esta jornada.")
    except Exception as e:
        print(f"❌ Error de ejecución: {e}")