import json
import time
import requests
import pandas as pd

GAMMA = "https://gamma-api.polymarket.com"


def descargar_eventos(tag_slug="ufc", limite=100, max_paginas=50):
    """Descarga eventos cerrados de una etiqueta, paginando."""
    eventos = []
    for pagina in range(max_paginas):
        params = {
            "tag_slug": tag_slug,
            "closed": "true",
            "limit": limite,
            "offset": pagina * limite,
        }
        r = requests.get(f"{GAMMA}/events", params=params, timeout=15)
        if r.status_code == 422:
            print("Límite de paginación alcanzado, paro aquí.")
            break
        r.raise_for_status()
        lote = r.json()
        if not lote:
            break
        eventos.extend(lote)
        time.sleep(0.3)
    return eventos


def parsear(m):
    """Devuelve una fila de pelea o None si el mercado no sirve."""
    try:
        outcomes = json.loads(m["outcomes"])
        precios = [float(p) for p in json.loads(m["outcomePrices"])]
        tokens = json.loads(m["clobTokenIds"])
    except (KeyError, TypeError, ValueError):
        return None

    # Solo mercados de pelea: dos peleadores (no Yes/No ni Over/Under)
    palabras = {o.lower() for o in outcomes}
    if len(outcomes) != 2 or palabras & {"yes", "no", "over", "under"}:
        return None

    # Resuelto con claridad: un lado ~1 y el otro ~0
    if max(precios) < 0.99:
        return None

    return {
        "pregunta": m["question"],
        "peleador_a": outcomes[0],
        "peleador_b": outcomes[1],
        "token_a": tokens[0],
        "resultado_a": 1 if precios[0] > 0.5 else 0,  # 1 = ganó el peleador A
        "fecha_fin": m.get("endDate"),
    }


if __name__ == "__main__":
    eventos = descargar_eventos("ufc")
    print("Eventos descargados:", len(eventos))

    mercados = [m for e in eventos for m in e.get("markets", [])]
    print("Mercados dentro de esos eventos:", len(mercados))

    filas = [parsear(m) for m in mercados]
    filas = [f for f in filas if f]
    print("Peleas resueltas y válidas:", len(filas))

    if not filas:
        raise SystemExit("No se encontraron peleas válidas.")

    df = pd.DataFrame(filas)
    print(df.head(10).to_string())
    df.to_csv("data/mercados_ufc.csv", index=False)