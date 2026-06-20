import os
from moviepy import VideoClip, AudioClip
# En las versiones modernas de MoviePy importamos los lectores de archivos directamente
from moviepy import VideoFileClip, AudioFileClip
from tqdm import tqdm

def emparejar_video_con_audio():
    video_original = "carrera_puntos_quiniela_valle_grande.mp4"  # Tu video HD lento
    archivo_musica = "du_hast.mp3"                  # <--- CAMBIA ESTO por el nombre de tu canción
    video_final = "quiniela_con_musica.mp4"
    
    # Comprobar que los archivos existan para evitar errores
    if not os.path.exists(video_original):
        print(f"Error: No se encuentra el video '{video_original}'. ¡Generalo primero!")
        return
    if not os.path.exists(archivo_musica):
        print(f"Error: No se encuentra el archivo de música '{archivo_musica}'.")
        print("Asegúrate de copiar tu archivo MP3 en esta misma carpeta.")
        return

    print("\n[1/2] Cargando pistas de video y audio...")
    # Cargar el video generado
    video_clip = VideoFileClip(video_original)
    
    # Cargar la canción MP3
    audio_clip = AudioFileClip(archivo_musica)
    
    # --- AJUSTE AUTOMÁTICO DE DURACIÓN ---
    # Si la música dura más que el video, la recortamos exactamente al tiempo del video
    if audio_clip.duration > video_clip.duration:
        print(f"La música es más larga que el video. Recortando a los {round(video_clip.duration, 2)} segundos exactos.")
        audio_clip = audio_clip.subclipped(0, video_clip.duration)
        
    # Asignamos el audio recortado al clip de video
    video_con_audio = video_clip.with_audio(audio_clip)
    
    print("\n[2/2] Fusionando pistas y exportando video final...")
    # Guardamos el archivo final usando el compresor H.264 para que pese muy poco
    video_con_audio.write_videofile(
        video_final,
        codec="libx264",
        audio_codec="aac",     # Códec de audio estándar compatible con tu Infinix
        bitrate="1500k",       # Mantenemos el bajo peso que logramos antes
        logger="bar"           # Barra de progreso visual
    )
    
    # Cerramos los archivos para liberar la memoria de la computadora
    video_clip.close()
    audio_clip.close()
    video_con_audio.close()
    
    print(f"\n¡Éxito total! Tu video musicalizado listo para el Infinix se guardó como: {video_final}")

if __name__ == "__main__":
    emparejar_video_con_audio()
