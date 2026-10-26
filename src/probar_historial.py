from datetime import datetime, timedelta

import pandas as pd
import requests

CLOB = "https://clob.polymarket.com"

df = pd.read_csv("data/mercados_ufc.csv", dtype={"token_a": str})
print("Peleas en el CSV:", len(df))


def pedir(token, **extra):
    params = {"market": token, **extra}
    r = requests.get(f"{CLOB}/prices-history", params=params, timeout=15)
    if r.status_code != 200:
        return f"HTTP {r.status_code}"
    return len(r.json().get("history", []))


for _, fila in df.head(5).iterrows():
    fin = datetime.fromisoformat(fila["fecha_fin"].replace("Z", "+00:00"))
    inicio_ts = int((fin - timedelta(days=7)).timestamp())
    fin_ts = int(fin.timestamp())

    print(fila["pregunta"])
    print("  max, cada 60 min   :", pedir(fila["token_a"], interval="max", fidelity=60))
    print("  max, cada 1440 min :", pedir(fila["token_a"], interval="max", fidelity=1440))
    print("  7 días, cada 60 min:", pedir(fila["token_a"], startTs=inicio_ts, endTs=fin_ts, fidelity=60))