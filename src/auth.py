# Ruta del archivo: src/auth.py
import bcrypt
import streamlit as st
from src.database import fetch_user_by_username

def check_password(password: str, hashed_password: str) -> bool:
    """Verifica si la contraseña ingresada coincide con el hash almacenado."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def hash_password(password: str) -> str:
    """Genera un hash seguro para almacenar contraseñas nuevas (Útil para el Admin)."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def authenticate_user():
    """Maneja el estado y renderiza la interfaz móvil de Login."""
    # Inicializar variables de sesión si no existen
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.user_info = None

    # Si ya inició sesión, no mostrar el formulario
    if st.session_state.authenticated:
        return True

    # Interfaz de Login optimizada para móvil
    st.markdown("<h2 style='text-align: center;'>🏆 Quiniela 2026</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>Ingresa tus credenciales</p>", unsafe_allow_html=True)

    with st.form("login_form", clear_on_submit=False):
        username_input = st.text_input("Usuario", placeholder="ej: juanperez").strip()
        password_input = st.text_input("Contraseña", type="password", placeholder="••••••••")
        submit_button = st.form_submit_button("Iniciar Sesión", use_container_width=True)

        if submit_button:
            if not username_input or not password_input:
                st.error("Por favor, llena todos los campos.")
                return False

            user = fetch_user_by_username(username_input)
            
            if user and check_password(password_input, user["password_hash"]):
                st.session_state.authenticated = True
                st.session_state.user_info = {
                    "id": user["id"],
                    "username": user["username"],
                    "name": user["name"],
                    "is_admin": user["is_admin"]
                }
                st.success(f"¡Bienvenido, {user['name']}!")
                st.rerun() # Refresca inmediatamente para mostrar la app real
            else:
                st.error("Usuario o contraseña incorrectos.")
    
    return False