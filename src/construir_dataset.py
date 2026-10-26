import time
from datetime import datetime, timedelta

import pandas as pd

import requests

CLOB = "https://clob.polymarket.com"
HORAS_ANTES = 24        # probabilidad medida 24 h antes del cierre
MAX_ANTIGUEDAD_H = 24   # si el último precio es más viejo, se descarta
MUESTRA = None           # prueba con 20 peleas; pon None para usar todas


def historial(token, inicio_ts, fin_ts):
    params = {"market": token, "startTs": inicio_ts, "endTs": fin_ts, "fidelity": 60}
    for _ in range(3):  # hasta 3 intentos
        try:
            r = requests.get(f"{CLOB}/prices-history", params=params, timeout=15)
            if r.status_code == 200:
                return r.json().get("history", [])
        except requests.RequestException:
            pass
        time.sleep(1)
    return []


def punto_previo(hist, objetivo_ts):
    """Último precio con t <= objetivo, o None si no hay uno suficientemente reciente."""
    previos = [h for h in hist if h["t"] <= objetivo_ts]
    if not previos:
        return None
    ultimo = max(previos, key=lambda h: h["t"])
    if objetivo_ts - ultimo["t"] > MAX_ANTIGUEDAD_H * 3600:
        return None
    return ultimo


df = pd.read_csv("data/mercados_ufc.csv", dtype={"token_a": str})
if MUESTRA:
    df = df.head(MUESTRA)

filas = []
for i, fila in enumerate(df.itertuples(index=False), start=1):
    if pd.isna(fila.fecha_fin):
        continue
    fin = datetime.fromisoformat(fila.fecha_fin.replace("Z", "+00:00"))
    objetivo = fin - timedelta(hours=HORAS_ANTES)

    hist = historial(
        fila.token_a,
        int((fin - timedelta(days=10)).timestamp()),
        int(fin.timestamp()),
    )
    punto = punto_previo(hist, int(objetivo.timestamp()))

    if punto:
        filas.append({
            "pregunta": fila.pregunta,
            "peleador_a": fila.peleador_a,
            "peleador_b": fila.peleador_b,
            "prob_a": punto["p"],
            "resultado_a": fila.resultado_a,
            "fecha_fin": fila.fecha_fin,
        })

    if i % 50 == 0:
        print(f"Procesadas {i}/{len(df)} | con probabilidad: {len(filas)}")
    time.sleep(0.2)  # no saturar la API

out = pd.DataFrame(filas)
out.to_csv("data/dataset_calibracion.csv", index=False)

print("\nPeleas procesadas:", len(df))
print("Peleas con probabilidad previa:", len(out))
print(out.head(10).to_string())
print("\nResumen de prob_a:")
print(out["prob_a"].describe())