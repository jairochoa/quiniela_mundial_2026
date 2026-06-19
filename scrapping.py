'''import time
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

class OptaDynamicScraper:
    def __init__(self):
        print("[INFO] Inicializando Navegador Automatizado para Opta...")
        options = webdriver.ChromeOptions()
        #options.add_argument("--headless") # Ejecutar en segundo plano sin abrir ventana
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("window-size=1400,1500") # Asegurar espacio para clics
        
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        self.url = "https://theanalyst.com/competition/fifa-world-cup/stats"

    def scrape_opta_table(self, stat_type="attacking"):
        """
        Navega, hace clic en TEAMS -> NON-PENALTY -> (Attacking o Defensive) 
        y extrae la tabla de datos real generada por JS.
        """
        try:
            print(f"[SELENIUM] Conectando a {self.url}...")
            self.driver.get(self.url)
            wait = WebDriverWait(self.driver, 15)
            
            # 1. CLIC EN EL MENÚ "TEAMS" (Intentando múltiples variantes de selectores)
            print("[SELENIUM] Seleccionando pestaña 'TEAMS'...")
            
            # Intentamos buscar por un XPath más flexible que ignore mayúsculas/minúsculas
            teams_btn = wait.until(EC.presence_of_element_located((
                By.XPATH, "//button[contains(translate(text(), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'TEAMS')]"
            )))
            
            # Forzar el clic mediante JavaScript para evitar bloqueos de capas/animaciones
            self.driver.execute_script("arguments[0].click();", teams_btn)
            time.sleep(2) # Damos tiempo a que se dibuje el submenú
            
            # 2. CLIC EN EL FILTRO "NON-PENALTY"
            print("[SELENIUM] Activando filtro 'NON-PENALTY'...")
            non_penalty_btn = wait.until(EC.presence_of_element_located((
                By.XPATH, "//button[contains(text(), 'NON-PENALTY')]"
            )))
            self.driver.execute_script("arguments[0].click();", non_penalty_btn)
            time.sleep(2)
            
            # 3. SELECCIONAR CATEGORÍA (Con bypass si ya está activo)
            if stat_type.lower() == "attacking":
                print("[SELENIUM] Detectado tipo 'attacking'. Saltando selección por defecto si ya está activa...")
            else:
                print(f"[SELENIUM] Abriendo el menú de sub-categoría...")
                try:
                    # Intentamos abrir el dropdown específico
                    dropdown_menu = wait.until(EC.presence_of_element_located((
                        By.XPATH, "//*[contains(@class, 'dropdown') or contains(@class, 'select')]"
                    )))
                    self.driver.execute_script("arguments[0].click();", dropdown_menu)
                    time.sleep(1.5)
                    
                    print(f"[SELENIUM] Haciendo clic en la opción: {stat_type.upper()}...")
                    # Forzamos la opción usando un selector de texto exacto
                    opcion_target = wait.until(EC.presence_of_element_located((
                        By.XPATH, f"//option[@value='{stat_type.lower()}'] | //li[contains(text(), '{stat_type.capitalize()}')]"
                    )))
                    self.driver.execute_script("arguments[0].click();", opcion_target)
                    time.sleep(2)
                except Exception as e_click:
                    print(f"[Aviso] No se requirió interacción de clics para sub-categoría: {e_click}")

            # 4. ESPERAR A QUE LA TABLA SE ACTUALICE Y EXTRAER HTML
            print("[SELENIUM] Localizando contenedor de la tabla Opta...")
            # Esperamos que aparezca cualquier celda de datos (td) para asegurar que hay registros cargados
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "td")))
            
            # Importa esto al inicio de tu archivo si no lo tienes:
            # from io import StringIO

            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            tabla_html = soup.find('table')
            
            if not tabla_html:
                raise ValueError("No se localizó una etiqueta <table> válida en el HTML.")
                
            # 🟢 LA CORRECCIÓN CRUCIAL: Envolver con StringIO
            from io import StringIO
            html_en_memoria = StringIO(str(tabla_html))
            
            df = pd.read_html(html_en_memoria)[0]
            print(f"[ÉXITO] Datos de {stat_type} extraídos correctamente. Registros: {len(df)}")
            return df
            
        except Exception as e:
            print(f"[ERROR CRÍTICO] Falló la automatización de clics: {e}")
            return None
        finally:
            self.driver.quit()

# =====================================================================
# PRUEBA LOCAL DE COMPROBACIÓN
# =====================================================================
if __name__ == "__main__":
    scraper = OptaDynamicScraper()
    # Extraemos el set de ataque idéntico al de tu imagen
    df_ataque = scraper.scrape_opta_table(stat_type="attacking")
    if df_ataque is not None:
        print(df_ataque.head())'''
        

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

class OptaDynamicScraper:
    def __init__(self):
        print("[INFO] Inicializando Navegador Automatizado para Opta...")
        options = webdriver.ChromeOptions()
        options.add_argument("--headless") 
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("window-size=1400,1500")
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        self.url = "https://theanalyst.com/competition/fifa-world-cup/stats"

    def scrape_opta_table(self, stat_type="attacking"):
        try:
            print(f"[SELENIUM] Conectando a {self.url}...")
            self.driver.get(self.url)
            wait = WebDriverWait(self.driver, 15)
            
            print("[SELENIUM] Seleccionando pestaña 'TEAMS'...")
            teams_btn = wait.until(EC.presence_of_element_located((
                By.XPATH, "//button[contains(translate(text(), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'TEAMS')]"
            )))
            self.driver.execute_script("arguments[0].click();", teams_btn)
            time.sleep(2)
            
            print("[SELENIUM] Activando filtro 'NON-PENALTY'...")
            non_penalty_btn = wait.until(EC.presence_of_element_located((
                By.XPATH, "//button[contains(text(), 'NON-PENALTY')]"
            )))
            self.driver.execute_script("arguments[0].click();", non_penalty_btn)
            time.sleep(2)
            
            if stat_type.lower() != "attacking":
                print(f"[SELENIUM] Abriendo el menú de sub-categoría...")
                dropdown_menu = wait.until(EC.presence_of_element_located((
                    By.XPATH, "//*[contains(@class, 'dropdown') or contains(@class, 'select')]"
                )))
                self.driver.execute_script("arguments[0].click();", dropdown_menu)
                time.sleep(1.5)
                
                opcion_target = wait.until(EC.presence_of_element_located((
                    By.XPATH, f"//option[@value='{stat_type.lower()}'] | //li[contains(text(), '{stat_type.capitalize()}')]"
                )))
                self.driver.execute_script("arguments[0].click();", opcion_target)
                time.sleep(2)

            print("[SELENIUM] Localizando contenedor de la tabla Opta...")
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "td")))
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            tabla_html = soup.find('table')
            
            html_en_memoria = StringIO(str(tabla_html))
            df = pd.read_html(html_en_memoria)[0]
            
            # Normalizar nombres de columnas a minúsculas y quitar espacios
            df.columns = [str(col).lower().strip() for col in df.columns]
            # Hacer que el nombre del equipo sea el índice para búsquedas rápidas
            df.set_index('name', inplace=True)
            
            print(f"[ÉXITO] Datos de {stat_type} extraídos y normalizados. Registros: {len(df)}")
            return df
        except Exception as e:
            print(f"[ERROR CRÍTICO] Falló el pipeline: {e}")
            return None
        finally:
            self.driver.quit()

class EnsambladoModel:
    def __init__(self, opta_df, elo_map):
        self.df = opta_df
        self.elo = elo_map
        self.global_average_goals = 1.35 
        
    def predict_match(self, team_a, team_b, hfa_team_a=0.0, fatigue_team_b=1.0):
        elo_a = self.elo.get(team_a, 1600)
        elo_b = self.elo.get(team_b, 1600)
        diff_elo = (elo_a - elo_b) / 400.0
        
        # Búsqueda defensiva en el DataFrame indexado (manejando variaciones de nombre de columnas)
        # En tu captura de pantalla las columnas son: 'xg' y 'xg per shot'
        npxg_a = self.df.loc[team_a, 'xg'] if team_a in self.df.index else 1.2
        npxg_b = self.df.loc[team_b, 'xg'] if team_b in self.df.index else 1.2
        
        xg_shot_a = self.df.loc[team_a, 'xg per shot'] if team_a in self.df.index else 0.10
        xg_shot_b = self.df.loc[team_b, 'xg per shot'] if team_b in self.df.index else 0.10
        
        # Cálculo de Lambdas (35% Elo, 45% Volumen xG, 20% Calidad xG/Shot)
        lambda_a = (self.global_average_goals + (diff_elo * 0.4)) * 0.35 + (npxg_a * 0.45) + (xg_shot_a * 10 * 0.20) + hfa_team_a
        lambda_b = ((self.global_average_goals - (diff_elo * 0.4)) * 0.35 + (npxg_b * 0.45) + (xg_shot_b * 10 * 0.20)) * fatigue_team_b
        
        max_goles = 5
        matriz = np.zeros((max_goles, max_goles))
        for i in range(max_goles):
            for j in range(max_goles):
                matriz[i, j] = poisson.pmf(i, lambda_a) * poisson.pmf(j, lambda_b)
                
        prob_local = np.sum(np.tril(matriz, -1))
        prob_empate = np.sum(np.diag(matriz))
        prob_visitante = np.sum(np.triu(matriz, 1))
        
        # Encontrar los marcadores más probables
        resultados = []
        for i in range(max_goles):
            for j in range(max_goles):
                resultados.append((i, j, matriz[i, j]))
        resultados_ordenados = sorted(resultados, key=lambda x: x[2], reverse=True)
        
        print(f"\n{'='*50}\n PRONÓSTICO QUINIELA: {team_a} vs {team_b}\n{'='*50}")
        print(f"Probabilidades (1X2): Gana {team_a}: {prob_local*100:.1f}% | Empate: {prob_empate*100:.1f}% | Gana {team_b}: {prob_visitante*100:.1f}%")
        print("Top Marcadores Exactos Recomendados:")
        for idx, (g_a, g_b, p) in enumerate(resultados_ordenados[:3]):
            print(f"  🎯 Opción {idx+1}: {g_a} - {g_b} (Probabilidad: {p*100:.1f}%)")

# =====================================================================
# EJECUCIÓN DEL PROCESO COMPLETO
# =====================================================================
if __name__ == "__main__":
    from bs4 import BeautifulSoup # Asegurar importación
    
    # 1. Correr el Scraper que ya validaste
    scraper = OptaDynamicScraper()
    df_ataque = scraper.scrape_opta_table(stat_type="attacking")
    
    if df_ataque is not None:
        # 2. Diccionario Macro ELO (Normalizado con los nombres exactos de la tabla de tu consola)
        elo_map = {
            "Germany": 1920, "Norway": 1740, "England": 1950, "Switzerland": 1810,
            "Korea Rep": 1795, "Spain": 1980, "France": 2010, "Uruguay": 1890,
            "Mexico": 1821, "Czech Rep": 1782, "South Africa": 1594, "Bosnia": 1625,
            "Canada": 1745, "Qatar": 1610
        }
        
        # 3. Instanciar el modelo con los datos reales raspados de Opta
        model = EnsambladoModel(df_ataque, elo_map)
        
        # 4. Generar las predicciones definitivas de la Jornada
        model.predict_match("Czech Rep", "South Africa", hfa_team_a=0.0, fatigue_team_b=0.82)
        model.predict_match("Switzerland", "Bosnia")
        model.predict_match("Canada", "Qatar", hfa_team_a=0.15, fatigue_team_b=0.85)
        model.predict_match("Mexico", "Korea Rep", hfa_team_a=0.22)