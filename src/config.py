# Ruta del archivo: src/config.py

# --- REGLAS DE TIEMPO (LÓGICA DE NEGOCIO) ---
LOCK_WINDOW_HOURS = 1          # Tiempo antes del juego para bloquear la edición del usuario
REVELATION_WINDOW_MINUTES = 30  # Tiempo antes del primer juego del día para revelar los votos del grupo

# --- CONFIGURACIÓN DE PROVEEDORES EXTERNOS ---
FLAG_CDN_URL = "https://flagcdn.com/w40/{code}.png"
DEFAULT_FLAG_CODE = "un"       # Bandera por defecto (unknown) si un país no está mapeado

# --- DICCIONARIO MAESTRO DE BANDERAS (MUNDIAL 2026) ---
TEAM_FLAGS = {
    "México": "mx",
    "Marruecos": "ma",
    "Estados Unidos": "us",
    "Japón": "jp",
    "Canadá": "ca",
    "Italia": "it",
    "Argentina": "ar",
    "España": "es",
    "Brasil": "br",
    "Francia": "fr",
    "Alemania": "de",
    "Colombia": "co"
}