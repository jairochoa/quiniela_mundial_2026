# Ruta del archivo: src/config.py

import os
import yaml  # O 'toml' según lo que estés usando en tu arquitectura actual

# --- REGLAS DE TIEMPO (LÓGICA DE NEGOCIO) ---
LOCK_WINDOW_HOURS = 1          # Tiempo antes del juego para bloquear la edición del usuario
REVELATION_WINDOW_MINUTES = 60  # Tiempo antes del primer juego del día para revelar los votos del grupo

# --- CONFIGURACIÓN DE PROVEEDORES EXTERNOS ---
FLAG_CDN_URL = "https://flagcdn.com/w40/{code}.png"
DEFAULT_FLAG_CODE = "un"       # Bandera por defecto (unknown) si un país no está mapeado

# --- DICCIONARIO MAESTRO DE BANDERAS (MUNDIAL 2026) ---
TEAM_FLAGS = {
    # Anfitriones del Mundial 2026
    "Canada": "ca",
    "Canadá": "ca",
    "Mexico": "mx",
    "México": "mx",
    "United States": "us",
    "Estados Unidos": "us",
    "USA": "us",

    # CONMEBOL
    "Argentina": "ar",
    "Brazil": "br",
    "Brasil": "br",
    "Colombia": "co",
    "Ecuador": "ec",
    "Paraguay": "py",
    "Uruguay": "uy",

    # UEFA (Inglaterra y Escocia usan códigos de subdivisión FlagCDN)
    "Austria": "at",
    "Belgium": "be",
    "Bélgica": "be",
    "Bosnia and Herzegovina": "ba",
    "Bosnia y Herzegovina": "ba",
    "Bosnia & Herzegovina": "ba",
    "Croatia": "hr",
    "Croacia": "hr",
    "Czechia": "cz",
    "Chequia": "cz",
    "Czech Republic": "cz",
    "England": "gb-eng",
    "Inglaterra": "gb-eng",
    "France": "fr",
    "Francia": "fr",
    "Germany": "de",
    "Alemania": "de",
    "Netherlands": "nl",
    "Países Bajos": "nl",
    "Norway": "no",
    "Noruega": "no",
    "Portugal": "pt",
    "Scotland": "gb-sct",
    "Escocia": "gb-sct",
    "Spain": "es",
    "España": "es",
    "Sweden": "se",
    "Suecia": "se",
    "Switzerland": "ch",
    "Suiza": "ch",
    "Türkiye": "tr",
    "Turquía": "tr",

    # AFC
    "Australia": "au",
    "Iran": "ir",
    "Irán": "ir",
    "Iraq": "iq",
    "Japan": "jp",
    "Japón": "jp",
    "Jordan": "jo",
    "Jordania": "jo",
    "Qatar": "qa",
    "Catar": "qa",
    "Saudi Arabia": "sa",
    "Arabia Saudita": "sa",
    "South Korea": "kr",
    "Corea del Sur": "kr",
    "Uzbekistan": "uz",
    "Uzbekistán": "uz",

    # CAF
    "Algeria": "dz",
    "Argelia": "dz",
    "Cape Verde": "cv",
    "Cabo Verde": "cv",
    "DR Congo": "cd",
    "República Democrática del Congo": "cd",
    "Egypt": "eg",
    "Egipto": "eg",
    "Ghana": "gh",
    "Ivory Coast": "ci",
    "Costa de Marfil": "ci",
    "Morocco": "ma",
    "Marruecos": "ma",
    "Senegal": "sn",
    "South Africa": "za",
    "Sudáfrica": "za",
    "Tunisia": "tn",
    "Túnez": "tn",

    # CONCACAF
    "Curaçao": "cw",
    "Curazao": "cw",
    "Haiti": "ht",
    "Haití": "ht",
    "Panama": "pa",
    "Panamá": "pa",

    # OFC
    "New Zealand": "nz",
    "Nueva Zelanda": "nz"
}

TEAM_TRANSLATIONS = {
    # Anfitriones
    "Canada": "Canadá",
    "Mexico": "México",
    "United States": "Estados Unidos",
    "United States of America": "Estados Unidos",
    "USA": "Estados Unidos",

    # CONMEBOL
    "Argentina": "Argentina",
    "Brazil": "Brasil",
    "Colombia": "Colombia",
    "Ecuador": "Ecuador",
    "Paraguay": "Paraguay",
    "Uruguay": "Uruguay",

    # UEFA
    "Austria": "Austria",
    "Belgium": "Bélgica",
    "Bosnia and Herzegovina": "Bosnia y Herzegovina",
    "Bosnia & Herzegovina": "Bosnia y Herzegovina",
    "Croatia": "Croacia",
    "Czechia": "Chequia",
    "Czech Republic": "Chequia",
    "England": "Inglaterra",
    "France": "Francia",
    "Germany": "Alemania",
    "Netherlands": "Países Bajos",
    "Norway": "Noruega",
    "Portugal": "Portugal",
    "Scotland": "Escocia",
    "Spain": "España",
    "Sweden": "Suecia",
    "Switzerland": "Suiza",
    "Türkiye": "Turquía",
    "Turkey": "Turquía",

    # AFC
    "Australia": "Australia",
    "Iran": "Irán",
    "Iraq": "Iraq",
    "Japan": "Japón",
    "Jordan": "Jordania",
    "Qatar": "Catar",
    "Saudi Arabia": "Arabia Saudita",
    "South Korea": "Corea del Sur",
    "Uzbekistan": "Uzbekistán",

    # CAF
    "Algeria": "Argelia",
    "Cape Verde": "Cabo Verde",
    "DR Congo": "RD del Congo",
    "Egypt": "Egipto",
    "Ghana": "Ghana",
    "Ivory Coast": "Costa de Marfil",
    "Morocco": "Marruecos",
    "Senegal": "Senegal",
    "South Africa": "Sudáfrica",
    "Tunisia": "Túnez",

    # CONCACAF (Adicionales)
    "Curaçao": "Curazao",
    "Curacao": "Curazao",
    "Haiti": "Haití",
    "Panama": "Panamá",

    # OFC
    "New Zealand": "Nueva Zelanda"
}


class ProjectConfig:
    def __init__(self):
        # 1. 🟢 Vincular constantes de negocio directamente a la instancia para unificación
        self.LOCK_WINDOW_HOURS = LOCK_WINDOW_HOURS
        self.REVELATION_WINDOW_MINUTES = REVELATION_WINDOW_MINUTES
        self.FLAG_CDN_URL = FLAG_CDN_URL
        self.DEFAULT_FLAG_CODE = DEFAULT_FLAG_CODE
        self.TEAM_FLAGS = TEAM_FLAGS
        self.TEAM_TRANSLATIONS = TEAM_TRANSLATIONS

        # 2. 🟢 Resolución de ruta absoluta robusta para config.yaml
        # Subir un nivel de forma segura desde src/config.py a la raíz del proyecto
        base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        self.config_path = os.path.join(base_dir, "config.yaml")
        
        # Respaldo secundario si se ejecuta desde la raíz directamente
        if not os.path.exists(self.config_path):
            self.config_path = os.path.abspath("config.yaml")
            
        self._config_data = self._load_config()

    def _load_config(self) -> dict:
        """Lee el archivo YAML de configuración centralizada en memoria."""
        if not os.path.exists(self.config_path):
            print(f"[WARNING] No se encontró config.yaml en {self.config_path}. Usando respaldos dinámicos.")
            return {}
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"[CRÍTICO] Error al parsear config.yaml: {e}")
            return {}

    def get_section(self, section_name: str) -> dict:
        """
        Retorna una sección específica del archivo de configuración.
        Garantiza respaldos locales completos (fallbacks).
        """
        fallbacks = {
            "data_ingestion": {
                "opta_mundial_url": "https://theanalyst.com/competition/fifa-world-cup/stats",
                "selenium_timeout": 15,
                "selenium_window_size": "1400,1500"
            },
            "predictor_params": {
                "base_goals": 1.35,
                "max_goles_matriz": 5,
                "elo_divisor": 400.0,
                "elo_impact_factor": 0.2,
                "default_elo": 1600
            },
            "anti_collusion_audit": {
                "max_expert_consensus": 0.85,
                "similarity_alert_threshold": 0.80,
                "dbscan_eps": 0.20,
                "dbscan_min_samples": 2
            },
            "paths": {
                "fixtures_to_predict": "data/raw/jornada_fixtures.csv",
                "output_predictions": "data/processed/predicciones_quiniela.csv",
                "interim_data": "data/interim"
            }
        }
        
        # Extrae del archivo YAML, si es nulo o no existe, usa la contingencia local
        return self._config_data.get(section_name, fallbacks.get(section_name, {}))

# 🔥 Instancia global única (Singleton) limpia para importar en todo el software
config = ProjectConfig()