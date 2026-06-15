# Ruta del archivo: src/seed_users.py
import bcrypt
from database import supabase

# Contraseña genérica temporal para todos tus amigos
TEMP_PASSWORD = "Mundial2026!"

# Lista de tus 9 amigos (Edita los nombres y usuarios a tu gusto)
# REGLA: El username debe ser en minúsculas y sin espacios
FRIENDS_LIST = [
    {"username": "Gerson", "name": "Gerson"},
    {"username": "Tony", "name": "Tony"},
    {"username": "Carlos", "name": "Carlos"},
    {"username": "Merwis", "name": "Merwis"},
    {"username": "Yiyo", "name": "Yiyo"},
    {"username": "Vaca", "name": "Vaca"},
    {"username": "Guefo", "name": "Guefo"},
    {"username": "Julian", "name": "Julian"},
    {"username": "Marcelino", "name": "Marcelino"}
]

def register_friends():
    print("⏳ Encriptando contraseñas y registrando amigos en Supabase...")
    
    # Generar el hash seguro de la contraseña temporal
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(TEMP_PASSWORD.encode('utf-8'), salt).decode('utf-8')
    
    for friend in FRIENDS_LIST:
        user_data = {
            "username": friend["username"],
            "password_hash": hashed_password,
            "name": friend["name"],
            "is_admin": False
        }
        
        try:
            # Insertar en Supabase. eq() evita duplicar si el usuario ya existe
            check = supabase.table("users").select("id").eq("username", friend["username"]).execute()
            if not check.data:
                supabase.table("users").insert(user_data).execute()
                print(f"✅ {friend['name']} registrado con éxito (Usuario: {friend['username']})")
            else:
                print(f"🟡 {friend['name']} ya estaba registrado. Saltando...")
        except Exception as e:
            print(f"❌ Error al registrar a {friend['name']}: {e}")
            
    print("🚀 ¡Todos los jugadores están listos para el Mundial!")

if __name__ == "__main__":
    register_friends()