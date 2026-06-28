# Ruta del archivo: src/seed_users.py
import streamlit as st
from database import supabase
# IMPORTANTE: Forzamos la simetría usando tu función oficial del proyecto
from auth import hash_password 

TEMP_PASSWORD = "Mundial2026!"
# Lista de tus 9 amigos (Edita los nombres y usuarios a tu gusto)
# REGLA: El username debe ser en minúsculas y sin espacios
FRIENDS_LIST = [
    #{"username": "gerson", "name": "Gerson"},
    #{"username": "tony", "name": "Tony"},
    #{"username": "carlos", "name": "Carlos"},
    #{"username": "merwis", "name": "Merwis"},
    #{"username": "yiyo", "name": "Yiyo"},
    #{"username": "vaca", "name": "Vaca"},
    #{"username": "guefo", "name": "Guefo"},
    #{"username": "julian", "name": "Julian"},
    #{"username": "marcelino", "name": "Marcelino"}
    {"username": "neudy", "name": "Neudy"}
]

def register_friends():
    print("⏳ Generando hashes simétricos y registrando en Supabase...")
    
    # Usamos exactamente tu función del proyecto
    hashed_password = hash_password(TEMP_PASSWORD)
    
    for friend in FRIENDS_LIST:
        user_data = {
            "username": friend["username"].lower().strip(), # Asegurar minúsculas libres de espacios
            "password_hash": hashed_password,
            "name": friend["name"],
            "is_admin": False
        }
        
        try:
            supabase.table("users").insert(user_data).execute()
            print(f"✅ {friend['name']} registrado con éxito (Usuario: {friend['username']})")
        except Exception as e:
            print(f"❌ Error al registrar a {friend['name']}: {e}")
            
    print("🚀 ¡Todos los jugadores sincronizados con el mismo algoritmo!")

if __name__ == "__main__":
    register_friends()