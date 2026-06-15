# Ruta del archivo: src/scoring.py

def calculate_match_points(pred_home: int, pred_away: int, real_home: int, real_away: int) -> int:
    """
    Calcula los puntos obtenidos en un partido basado en las reglas:
    - 5 puntos: Acierto exacto del marcador.
    - 3 puntos: Acierto de ganador o empate (pero no marcador exacto).
    - 0 puntos: No acertó nada.
    """
    # Caso 1: Marcador Exacto (Suma 5 puntos)
    if pred_home == real_home and pred_away == real_away:
        return 5
        
    # Determinar tendencias (Ganador Local, Ganador Visitante o Empate)
    real_trend = "H" if real_home > real_away else ("A" if real_away > real_home else "D")
    pred_trend = "H" if pred_home > pred_away else ("A" if pred_away > pred_home else "D")
    
    # Caso 2: Acertar la tendencia (Ganador o Empate no exacto)
    if real_trend == pred_trend:
        return 3
        
    # Caso 3: No acertó nada
    return 0