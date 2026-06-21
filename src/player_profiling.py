import math
import numpy as np
import pandas as pd
import toml
from supabase import create_client

class PlayerProfilingEngine:
    def __init__(self, raw_predictions: list, raw_users: list, raw_matches: list):
        """
        Motor de Gamificación y Análisis de Personalidad de Jugadores.
        Asigna arquetipos basados en el comportamiento estadístico relativo del grupo.
        """
        self.user_map = {u["id"]: u["name"] for u in raw_users}
        self.match_map = {m["id"]: f"{m.get('local', 'Loc')}-{m.get('visitante', 'Vis')}" for m in raw_matches}
        
        self.df_base = self._preprocesar_datos(raw_predictions)
        self.df_perfiles = self._calcular_metricas_individuales()
        self.df_arquetipos = self._asignar_arquetipos()

    def _derivar_tendencia(self, home_score, away_score):
        if home_score > away_score: return "L"
        elif home_score == away_score: return "E"
        else: return "V"

    def _preprocesar_datos(self, predictions: list) -> pd.DataFrame:
        if not predictions: return pd.DataFrame()
        df = pd.DataFrame(predictions)
        
        df = df.dropna(subset=["home_score", "away_score"]).copy()
        df["home_score"] = pd.to_numeric(df["home_score"], errors="coerce")
        df["away_score"] = pd.to_numeric(df["away_score"], errors="coerce")
        df = df.dropna(subset=["home_score", "away_score"])

        df["marcador_exacto"] = df["home_score"].astype(int).astype(str) + "-" + df["away_score"].astype(int).astype(str)
        df["total_goles"] = df["home_score"] + df["away_score"]
        df["tendencia_1x2"] = df.apply(lambda row: self._derivar_tendencia(row["home_score"], row["away_score"]), axis=1)
        
        df["usuario"] = df["user_id"].map(self.user_map)
        df["partido"] = df["match_id"].map(self.match_map)
        
        return df

    def _calcular_metricas_individuales(self) -> pd.DataFrame:
        """Calcula el ADN estadístico de cada jugador."""
        # 1. Calcular el consenso del grupo y la rareza (Shannon) de los marcadores
        partido_stats = {}
        for partido, group in self.df_base.groupby("partido"):
            tendencia_moda = group["tendencia_1x2"].mode()[0]
            frecuencias_marcadores = group["marcador_exacto"].value_counts(normalize=True).to_dict()
            partido_stats[partido] = {
                "consenso_1x2": tendencia_moda,
                "frecuencias": frecuencias_marcadores
            }

        perfiles = []
        usuarios = self.df_base["usuario"].unique()
        
        for user in usuarios:
            user_data = self.df_base[self.df_base["usuario"] == user]
            total_partidos = len(user_data)
            
            puntos_consenso = 0
            shannon_score_total = 0.0
            
            for _, row in user_data.iterrows():
                partido = row["partido"]
                tendencia = row["tendencia_1x2"]
                marcador = row["marcador_exacto"]
                stats = partido_stats.get(partido, {})
                
                # ¿Votó con el rebaño?
                if tendencia == stats.get("consenso_1x2"):
                    puntos_consenso += 1
                
                # Calcular sorpresa del marcador
                p_marcador = stats.get("frecuencias", {}).get(marcador, 1.0)
                if p_marcador > 0:
                    shannon_score_total += -math.log2(p_marcador)
            
            perfiles.append({
                "Usuario": user,
                "Partidos_Jugados": total_partidos,
                "Tasa_Rebaño": puntos_consenso / total_partidos if total_partidos > 0 else 0,
                "Indice_Kamikaze": shannon_score_total / total_partidos if total_partidos > 0 else 0,
                "Promedio_Goles_Partido": user_data["total_goles"].mean(),
                "Volatilidad_Goles": user_data["total_goles"].std()
            })
            
        return pd.DataFrame(perfiles).set_index("Usuario")

    def _asignar_arquetipos(self) -> pd.DataFrame:
        """
        Asigna la medalla principal basada en el percentil en el que caen 
        comparados con sus propios compañeros.
        """
        df = self.df_perfiles.copy()
        df["Arquetipo"] = "Jugador Promedio"
        df["Descripción"] = "Mantiene un equilibrio perfecto en sus predicciones."
        df["Icono"] = "⚖️"

        if df.empty: return df

        # Calculamos percentiles relativos al grupo (funciona desde 3 hasta 1000 jugadores)
        q_rebano_alto = df["Tasa_Rebaño"].quantile(0.80)
        q_kamikaze_alto = df["Indice_Kamikaze"].quantile(0.80)
        q_goles_alto = df["Promedio_Goles_Partido"].quantile(0.80)
        q_volatilidad_baja = df["Volatilidad_Goles"].quantile(0.20)

        for user, row in df.iterrows():
            # 1. El Kamikaze (Mayor Índice de Shannon - Vota empates a 0 o locuras)
            if row["Indice_Kamikaze"] >= q_kamikaze_alto and row["Indice_Kamikaze"] > 0.5:
                df.at[user, "Arquetipo"] = "El Cazador de Mitos"
                df.at[user, "Descripción"] = "No le teme a nadie. Apuesta por resultados improbables y rompe la estadística."
                df.at[user, "Icono"] = "🃏"
            
            # 2. El Contable / Conservador (Volatilidad baja, Tasa Rebaño alta)
            elif row["Volatilidad_Goles"] <= q_volatilidad_baja and row["Tasa_Rebaño"] > 0.60:
                df.at[user, "Arquetipo"] = "El Contable"
                df.at[user, "Descripción"] = "Fiel creyente del 1-0 y 2-1. Juega seguro, no asume riesgos innecesarios."
                df.at[user, "Icono"] = "🛡️"
                
            # 3. El Espectáculo (Promedio de Goles más alto)
            elif row["Promedio_Goles_Partido"] >= q_goles_alto:
                df.at[user, "Arquetipo"] = "El Optimista del Gol"
                df.at[user, "Descripción"] = "Siempre espera un partidazo. Pronostica más goles por partido que el resto."
                df.at[user, "Icono"] = "🔥"
                
            # 4. El Rebaño (Tasa de consenso brutalmente alta)
            elif row["Tasa_Rebaño"] >= q_rebano_alto:
                df.at[user, "Arquetipo"] = "La Voz del Pueblo"
                df.at[user, "Descripción"] = "Si la mayoría dice que gana Brasil, él dice que gana Brasil. No discute."
                df.at[user, "Icono"] = "🐑"

        return df[["Icono", "Arquetipo", "Descripción", "Tasa_Rebaño", "Indice_Kamikaze", "Promedio_Goles_Partido"]]

    def obtener_ranking_gamificado(self) -> pd.DataFrame:
        # Formateo limpio para enviar a la interfaz de Streamlit
        df = self.df_arquetipos.reset_index()
        df["Estilo (Rebaño vs Locura)"] = df.apply(
            lambda x: f"Consenso: {x['Tasa_Rebaño']*100:.0f}% | Rareza: {x['Indice_Kamikaze']:.1f} pts", axis=1
        )
        df["Promedio Goles"] = df["Promedio_Goles_Partido"].apply(lambda x: f"{x:.1f} goles/partido")
        return df[["Icono", "Usuario", "Arquetipo", "Descripción", "Estilo (Rebaño vs Locura)", "Promedio Goles"]]

# =====================================================================
# EJECUCIÓN AUTÓNOMA (TEST)
# =====================================================================
if __name__ == "__main__":
    print("🔌 Conectando a Supabase para Gamificación...")
    try:
        secrets = toml.load(".streamlit/secrets.toml")
        supabase = create_client(secrets["supabase"]["url"], secrets["supabase"]["key"])
        
        pronosticos = supabase.table("predictions_log").select("*").execute().data
        matches = supabase.table("matches").select("*").execute().data
        users = supabase.table("users").select("id, name").execute().data
        jugadores = [u for u in users if not u.get("is_admin", False) and u["name"].strip().lower() != "admin"]
        
        if pronosticos and jugadores and matches:
            profiler = PlayerProfilingEngine(pronosticos, jugadores, matches)
            df_gamificado = profiler.obtener_ranking_gamificado()
            
            print("\n" + "="*80 + "\n 🏆 SALÓN DE LA FAMA: ADN Y ARQUETIPOS DE LOS JUGADORES\n" + "="*80)
            print(df_gamificado.to_string(index=False))
            
    except Exception as e:
        print(f"❌ Error de ejecución: {e}")