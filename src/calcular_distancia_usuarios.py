
import os
import time
import toml
import pandas as pd
import plotly.express as px
from supabase import create_client

print("🔌 Conectando a Supabase a través de secrets.toml...")
try:
    secrets = toml.load(".streamlit/secrets.toml")
    SUPABASE_URL = secrets["supabase"]["url"]
    SUPABASE_KEY = secrets["supabase"]["key"]
except Exception as e:
    print("❌ Error al leer .streamlit/secrets.toml.")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 2. DESCARGA DE DATOS CRUDOS
print("📥 Descargando datos de juego...")
pronosticos = supabase.table("predictions_log").select("*").execute().data
matches = supabase.table("matches").select("*").execute().data
users = supabase.table("users").select("id, name").execute().data
jugadores = [u for u in users if not u.get("is_admin", False) and u["name"].strip().lower() != "admin"]




