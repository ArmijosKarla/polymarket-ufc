import os

import matplotlib
matplotlib.use("Agg") 
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss

df = pd.read_csv("data/dataset_calibracion.csv")
print("Peleas en el dataset:", len(df))

# 1. Limpieza: sin duplicados y sin peleas con probabilidad exacta de 0.5
df = df.drop_duplicates(subset=["pregunta", "fecha_fin"])
df = df[df["prob_a"] != 0.5].copy()

# 2. Un lado por pelea: el favorito
df["prob_fav"] = np.maximum(df["prob_a"], 1 - df["prob_a"])
df["gano_fav"] = np.where(df["prob_a"] > 0.5, df["resultado_a"], 1 - df["resultado_a"])
print("Peleas usadas en el análisis:", len(df))
print("Favoritos que ganaron:", f"{df['gano_fav'].mean():.1%}")
print("Probabilidad media asignada a favoritos:", f"{df['prob_fav'].mean():.1%}")

# 3. Brier score (más bajo = mejor)
y, p = df["gano_fav"].to_numpy(), df["prob_fav"].to_numpy()
brier = brier_score_loss(y, p)
brier_ingenuo = brier_score_loss(y, np.full(len(y), 0.5))


def bootstrap_brier(y, p, n=2000, seed=42):
    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(n):
        idx = rng.integers(0, len(y), len(y))
        vals.append(brier_score_loss(y[idx], p[idx]))
    return np.percentile(vals, [2.5, 97.5])

def wilson(k, n, z=1.96):
    """Intervalo de confianza de Wilson para una proporción."""
    p = k / n
    centro = (p + z**2 / (2 * n)) / (1 + z**2 / n)
    margen = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / (1 + z**2 / n)
    return centro - margen, centro + margen

ic = bootstrap_brier(y, p)
print(f"\nBrier mercado : {brier:.4f}  (IC 95%: {ic[0]:.4f} a {ic[1]:.4f})")
print(f"Brier ingenuo : {brier_ingenuo:.4f}  (predecir siempre 50%)")

# 4. Tabla de calibración por grupos de igual tamaño
df["grupo"] = pd.qcut(df["prob_fav"], q=5, duplicates="drop")
tabla = df.groupby("grupo", observed=True).agg(
    peleas=("gano_fav", "size"),
    victorias=("gano_fav", "sum"),
    prob_media=("prob_fav", "mean"),
    freq_real=("gano_fav", "mean"),
)
ics = [wilson(k, n) for k, n in zip(tabla["victorias"], tabla["peleas"])]
tabla["ic_inf"] = [i[0] for i in ics]
tabla["ic_sup"] = [i[1] for i in ics]
print("\n", tabla.round(3))

# 5. Gráfico de calibración
os.makedirs("figuras", exist_ok=True)
plt.figure(figsize=(6, 6))
plt.plot([0.5, 1], [0.5, 1], "--", color="gray", label="Calibración perfecta")
err_inf = tabla["freq_real"] - tabla["ic_inf"]
err_sup = tabla["ic_sup"] - tabla["freq_real"]
plt.errorbar(
    tabla["prob_media"], tabla["freq_real"],
    yerr=[err_inf, err_sup], fmt="o-", capsize=4,
    label="Polymarket UFC (IC 95 %)",
)
plt.xlabel("Probabilidad del mercado (favorito)")
plt.ylabel("Frecuencia real de victoria")
plt.title(f"Calibración de Polymarket en UFC (n={len(df)})")
plt.legend()
plt.grid(alpha=0.3)
plt.savefig("figuras/calibracion.png", dpi=150, bbox_inches="tight")
print("\nGráfico guardado en figuras/calibracion.png")