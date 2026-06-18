import json
import streamlit as st
from supabase import create_client

# 1. CARGA AUTOMÁTICA DE SECRETS (Sin quemar credenciales)
try:
    # Streamlit se encarga de buscar y parsear el bloque [supabase] del secrets.toml
    SUPABASE_URL = st.secrets["supabase"]["url"]
    SUPABASE_KEY = st.secrets["supabase"]["key"]
except Exception as e:
    print("❌ ERROR: No se pudieron leer las credenciales de secrets.toml.")
    print("💡 NOTA: Asegúrate de ejecutar este script parado desde la RAÍZ del proyecto")
    print("   para que Streamlit pueda ubicar la carpeta oculta '.streamlit/'\n")
    raise e

# Inicializamos el cliente de Supabase de forma segura
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def cargar_historico():
    print("🚀 Iniciando siembra de datos históricos desde el pasado...")
    
    # 2. Descargamos usuarios para armar el mapa de traducción (Nombre -> ID UUID)
    try:
        users_db = supabase.table("users").select("id, username").execute().data
        mapa_usuarios = {u["username"].strip().lower(): u["id"] for u in users_db}
    except Exception as e:
        print(f"❌ Error al conectar con Supabase para listar usuarios: {e}")
        return

    # 3. LEER EL ARCHIVO JSON RENOMBRADO
    # Al ejecutarse desde la raíz, buscará el archivo en la raíz del proyecto
    json_filename = "pronosticos_anteriores.json"
    
    try:
        with open(json_filename, "r", encoding="utf-8") as f:
            pronosticos_json = json.load(f)
    except FileNotFoundError:
        print(f"❌ ERROR: No se encontró el archivo '{json_filename}' en la raíz del proyecto.")
        print("👉 Recuerda guardar el JSON en la raíz principal (afuera de la carpeta 'src').")
        return

    registros_a_subir = []
    errores = 0

    # 4. Traducimos Nombres a IDs y empaquetamos el lote
    for p in pronosticos_json:
        nombre_clean = p["usuario"].strip().lower()
        
        if nombre_clean in mapa_usuarios:
            user_id = mapa_usuarios[nombre_clean]
            registros_a_subir.append({
                "user_id": user_id,
                "match_id": p["match_id"],
                "home_score": p["home_score"],
                "away_score": p["away_score"]
            })
        else:
            print(f"⚠️ Alerta: El jugador '{p['usuario']}' no está registrado en la App. Saltando fila.")
            errores += 1

# 5. Inyección Inteligente (Upsert / Ignorar Duplicados)
    if registros_a_subir:
        print(f"📦 Preparando paquete masivo con {len(registros_a_subir)} registros...")
        try:
            # 🟢 CAMBIO AQUÍ: Usamos .upsert() especificando el conflicto
            res = supabase.table("predictions_log").upsert(
                registros_a_subir, 
                on_conflict="user_id,match_id"
            ).execute()
            
            if res.data:
                print(f"✅ ¡ÉXITO! El lote ha sido procesado de forma inteligente.")
                print(f"💡 Los registros nuevos se crearon y los existentes se actualizaron/mantuvieron.")
                if errores > 0:
                    print(f"👀 Nota: Se saltaron {errores} registros por nombres mal escritos.")
        except Exception as e:
            print(f"❌ Error crítico al procesar el lote (upsert) en Supabase: {e}")
    else:
        print("🤷‍♂️ No se generó ningún registro válido para subir al servidor.")

if __name__ == "__main__":
    cargar_historico()