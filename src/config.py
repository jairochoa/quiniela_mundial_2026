# Ruta del archivo: src/config.py

# --- REGLAS DE TIEMPO (LÓGICA DE NEGOCIO) ---
LOCK_WINDOW_HOURS = 1          # Tiempo antes del juego para bloquear la edición del usuario
REVELATION_WINDOW_MINUTES = 30  # Tiempo antes del primer juego del día para revelar los votos del grupo

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
    "Curacao": "cw",
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
    "DR Congo": "República Democrática del Congo",
    "Egypt": "Egipto",
    "Ghana": "Ghana",
    "Ivory Coast": "Costa de Marfil",
    "Morocco": "Marruecos",
    "Senegal": "Senegal",
    "South Africa": "Sudáfrica",
    "Tunisia": "Túnez",

    # CONCACAF (Adicionales)
    "Curacao": "Curazao",
    "Haiti": "Haití",
    "Panama": "Panamá",

    # OFC
    "New Zealand": "Nueva Zelanda"
}