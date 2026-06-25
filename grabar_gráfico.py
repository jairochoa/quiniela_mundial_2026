import os
import time
import cv2
from playwright.sync_api import sync_playwright
import numpy as np
from tqdm import tqdm  
import imageio

def grabar_grafico_perfecto_v2():
    html_name = "carrera_quiniela.html"
    html_path = os.path.abspath(html_name)
    file_url = f"file://{html_path}"
    
    # --- CALIBRACIÓN DE TIEMPOS ---
    # Al poner duracion_cuadro = 3000ms, la carrera total se vuelve más larga.
    # Ajusta 'duracion_real' al tiempo total aproximado que tarda en tu pantalla (ej. 25 segundos)
    duracion_real = 35  
    fps = 12            # BAJAMOS LOS FPS: Captura menos fotos por segundo para ralentizar el video
    total_frames = duracion_real * fps
    width, height = 1080, 720 

    frames_temp = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False) 
        context = browser.new_context(
            viewport={"width": width, "height": height},
            device_scale_factor=3  
        )
        page = context.new_page()
        
        print("\n[1/3] Cargando gráfico y preparando congelamiento...")
        page.goto(file_url)
        page.wait_for_selector(".js-plotly-plot")
        
        # TRUCO 1: Forzar alineación centrada
        page.evaluate("""
            var plot = document.querySelector('.js-plotly-plot');
            if (plot) {
                plot.style.margin = '0 auto';
                plot.style.display = 'block';
                plot.parentElement.style.display = 'flex';
                plot.parentElement.style.justifyContent = 'center';
                plot.parentElement.style.alignItems = 'center';
                plot.parentElement.style.height = '100vh';
            }
        """)
        
        # TRUCO 2: Forzar a Plotly a volver al cuadro 0 (Inicio absoluto) y pausar
        print("Reiniciando animación al cuadro 0...")
        page.evaluate("""
            var plot = document.querySelector('.js-plotly-plot');
            if (plot && plot.layout && plot.layout.sliders) {
                // Si usa slider de Plotly Express, saltamos al primer paso
                var firstStep = plot.layout.sliders[0].steps[0];
                Plotly.animate(plot, firstStep.args[0], firstStep.args[1]);
            }
        """)
        
        # Damos 3 segundos de espera en el cuadro inicial estático antes de grabar
        time.sleep(3)
        
        # Presionamos Play de forma sincronizada justo cuando arranca el bucle de Python
        try:
            page.click("text=Play", timeout=3000)
            print("¡Carrera iniciada desde el principio!")
        except:
            try:
                page.click(".slider-button", timeout=2000)
                print("¡Carrera iniciada!")
            except:
                print("Aviso: Capturando directamente.")

        print(f"[2/3] Capturando {total_frames} fotogramas ralentizados (Sincronización a {fps} FPS)...")
        
        tiempo_entre_frames = duracion_real / total_frames
        
        for i in tqdm(range(total_frames), desc="Capturando frames", unit="frame"):
            start_frame_time = time.time()
            
            # Captura exclusiva del objeto gráfico
            plot_element = page.locator(".js-plotly-plot")
            image_bytes = plot_element.screenshot(type="jpeg", quality=90)
            frames_temp.append(image_bytes)
            
            elapsed = time.time() - start_frame_time
            delay = max(0.001, tiempo_entre_frames - elapsed)
            time.sleep(delay)

        browser.close()

    print("\n[3/3] Procesando y guardando video MP4 a velocidad real...")
    video_name = "grafico_quiniela_perfecto.mp4"
    
    # Importante: imageio compilará el video a los mismos FPS bajos (12) para mantener la marcha lenta
    writer = imageio.get_writer(video_name, format='FFMPEG', mode='I', fps=fps, codec='libx264', quality=7)

    for img_bytes in tqdm(frames_temp, desc="Guardando MP4 Comprimido", unit="frame"):
        nparr = np.frombuffer(img_bytes, np.uint8)
        img_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img_np is not None:
            img_rgb = cv2.cvtColor(img_np, cv2.COLOR_BGR2RGB)
            writer.append_data(img_rgb)

    writer.close()
    print(f"\n¡Listo! Tu video ahora inicia en 0 y va al ritmo lento del HTML. Guardado como: {video_name}")

if __name__ == "__main__":
    grabar_grafico_perfecto_v2()
