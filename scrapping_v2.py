import time
import pandas as pd
import numpy as np
from io import StringIO
from scipy.stats import poisson
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

class OptaMundialPipelineV2:
    def __init__(self):
        self.url = "https://theanalyst.com/competition/fifa-world-cup/stats"

    def _crear_driver(self):
        """Inicializa una instancia limpia y aislada de Chrome Headless"""
        options = webdriver.ChromeOptions()
        options.add_argument("--headless") # 🟢 Activado para producción veloz
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("window-size=1400,1500")
        return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    def scrape_single_table(self, stat_type):
        """Abre un navegador exclusivo para extraer una sola categoría de datos"""
        driver = self._crear_driver()
        try:
            print(f"\n[SELENIUM] Abriendo sesión aislada para: {stat_type.upper()}...")
            driver.get(self.url)
            wait = WebDriverWait(driver, 15)
            
            # Clic en TEAMS
            teams_btn = wait.until(EC.presence_of_element_located((
                By.XPATH, "//button[contains(translate(text(), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'TEAMS')]"
            )))
            driver.execute_script("arguments[0].click();", teams_btn)
            time.sleep(1.5)
            
            # Clic en NON-PENALTY
            non_penalty_btn = wait.until(EC.presence_of_element_located((
                By.XPATH, "//button[contains(text(), 'NON-PENALTY')]"
            )))
            driver.execute_script("arguments[0].click();", non_penalty_btn)
            time.sleep(1.5)
            
            # Si buscamos la pestaña defensiva ('defending')
            if stat_type.lower() != "attacking":
                print("[SELENIUM] Localizando la caja del menú desplegable...")
                dropdown_menu = wait.until(EC.element_to_be_clickable((
                    By.XPATH, "//*[contains(@class, 'dropdown') or contains(@class, 'select') or contains(@class, 'Dropdown') or @role='button']"
                )))
                driver.execute_script("arguments[0].click();", dropdown_menu)
                time.sleep(2.0) # Pausa estratégica para despliegue de la lista flotante
                
                print("[SELENIUM] Seleccionando 'Defending' por índice físico en la lista...")
                # 🟢 SOLUCIÓN DEFINITIVA: Extraemos todos los componentes interactivos del submenú
                elementos_lista = driver.find_elements(By.XPATH, "//*[contains(@class, 'dropdown')]//li | //ul//li | //option")
                
                # En tu captura de pantalla, 'Defending' ocupa la 5ta posición física (índice 4 del arreglo)
                if len(elementos_lista) >= 5:
                    driver.execute_script("arguments[0].click();", elementos_lista[4])
                    print("[SELENIUM] Clic por índice procesado correctamente.")
                else:
                    # Respaldo de contingencia mediante inyección de texto plano normalizado
                    print("[SELENIUM] Advertencia: Menú anómalo. Ejecutando respaldo por texto...")
                    opcion_target = wait.until(EC.element_to_be_clickable((
                        By.XPATH, "//*[text()='Defending' or contains(text(), 'Defending')]"
                    )))
                    driver.execute_script("arguments[0].click();", opcion_target)
                
                time.sleep(3.5) # Pausa vital para permitir la reconstrucción asíncrona de las columnas

            print(f"[SELENIUM] Capturando estructura de la tabla {stat_type.upper()}...")
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "td")))
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            tabla_html = soup.find('table')
            
            html_en_memoria = StringIO(str(tabla_html))
            df = pd.read_html(html_en_memoria)[0]
            
            # Homogeneizar nombres de columnas añadiendo el prefijo único (att_ o def_)
            prefix = stat_type.lower()[:3]
            df.columns = [f"{prefix}_{col.lower().strip()}" if col.lower().strip() != 'name' else 'name' for col in df.columns]
            df.set_index('name', inplace=True)
            return df
            
        except Exception as e:
            print(f"[ERROR] Falló la extracción de {stat_type}: {e}")
            return None
        finally:
            driver.quit()

    def scrape_full_dataset(self):
        """Consolida las dos sesiones independientes en un único DataFrame"""
        print("[PIPELINE V2] Iniciando recolección por sesiones distribuidas...")
        
        df_att = self.scrape_single_table("attacking")
        if df_att is None: return None
        
        df_def = self.scrape_single_table("defending")
        if df_def is None: return None
        
        # Unificación limpia mediante intersección interna de los índices (nombre del país)
        df_consolidado = df_att.join(df_def, how='inner')
        print(f"\n[ÉXITO] Dataset V2 unificado perfectamente. Total de equipos procesados: {len(df_consolidado)}")
        return df_consolidado

class PredictorAvanzadoV2:
    def __init__(self, df_consolidado, elo_map):
        self.df = df_consolidado
        self.elo = elo_map
        # 🟢 CORRECCIÓN DE COLUMNAS: Apuntamos de manera exacta a los prefijos generados por el pipeline
        self.avg_npxg = self.df['att_xg'].mean()
        self.avg_xga = self.df['def_xg'].mean() if 'def_xg' in self.df.columns else self.avg_npxg
        self.base_goals = 1.35 

    def predict_match_v2(self, local, visitante, hfa_local=0.0, fatigue_visitante=1.0):
        # 1. Fuerza Relativa (Ratios Cruzados Ataque vs Defensa)
        fuerza_ataque_local = self.df.loc[local, 'att_xg'] / self.avg_npxg
        fuerza_defensa_visitante = self.df.loc[visitante, 'def_xg'] / self.avg_xga if 'def_xg' in self.df.columns else 1.0
        
        fuerza_ataque_visitante = self.df.loc[visitante, 'att_xg'] / self.avg_npxg
        fuerza_defensa_local = self.df.loc[local, 'def_xg'] / self.avg_xga if 'def_xg' in self.df.columns else 1.0
        
        # 2. Modificadores Macroeconómicos (ELO)
        elo_loc = self.elo.get(local, 1600)
        elo_vis = self.elo.get(visitante, 1600)
        diff_elo = (elo_loc - elo_vis) / 400.0
        factor_elo_local = 1.0 + (diff_elo * 0.2)
        factor_elo_visitante = 1.0 - (diff_elo * 0.2)

        # 3. Compilación de Lambdas de Poisson Opiáceos
        lambda_local = (self.base_goals * fuerza_ataque_local * fuerza_defensa_visitante * factor_elo_local) + hfa_local
        lambda_visitante = (self.base_goals * fuerza_ataque_visitante * fuerza_defensa_local * factor_elo_visitante) * fatigue_visitante
        
        max_goles = 5
        matriz = np.zeros((max_goles, max_goles))
        for i in range(max_goles):
            for j in range(max_goles):
                matriz[i, j] = poisson.pmf(i, lambda_local) * poisson.pmf(j, lambda_visitante)
                
        prob_local = np.sum(np.tril(matriz, -1))
        prob_empate = np.sum(np.diag(matriz))
        prob_visitante = np.sum(np.triu(matriz, 1))
        
        resultados = []
        for i in range(max_goles):
            for j in range(max_goles):
                resultados.append((i, j, matriz[i, j]))
        resultados_ordenados = sorted(resultados, key=lambda x: x[2], reverse=True)
        
        print(f"\n{'='*50}\n 🚀 MODELO V2 AUTOCALIBRADO: {local} vs {visitante}\n{'='*50}")
        print(f"Lambdas Operacionales -> λ_{local}: {lambda_local:.2f} | λ_{visitante}: {lambda_visitante:.2f}")
        print(f"Probabilidades (1X2) -> Gana Local: {prob_local*100:.1f}% | Empate: {prob_empate*100:.1f}% | Gana Visitante: {prob_visitante*100:.1f}%")
        print("Top Marcadores Exactos Optimizados para la Quiniela:")
        for idx, (g_l, g_v, p) in enumerate(resultados_ordenados[:3]):
            print(f"  🎯 Opción {idx+1}: {g_l} - {g_v} (Probabilidad: {p*100:.1f}%)")

# =====================================================================
# CONFIGURACIÓN DE CORRIDA DE LA JORNADA
# =====================================================================
if __name__ == "__main__":
    pipeline = OptaMundialPipelineV2()
    df_dataset = pipeline.scrape_full_dataset()
    
    if df_dataset is not None:
        elo_map = {
            "Germany": 1920, "Norway": 1740, "England": 1950, "Switzerland": 1810,
            "Korea Rep": 1795, "Spain": 1980, "France": 2010, "Uruguay": 1890,
            "Mexico": 1821, "Czech Rep": 1782, "South Africa": 1594, "Bosnia": 1625,
            "Canada": 1745, "Qatar": 1610
        }
        
        predictor = PredictorAvanzadoV2(df_dataset, elo_map)
        
        # Corremos las simulaciones con el nuevo motor de emparejamiento cruzado
        predictor.predict_match_v2("Canada", "Qatar", hfa_local=0.15, fatigue_visitante=0.85)
        predictor.predict_match_v2("Mexico", "Korea Rep", hfa_local=0.22)