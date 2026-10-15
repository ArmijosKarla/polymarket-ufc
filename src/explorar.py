import requests

url = "https://gamma-api.polymarket.com/markets"
params = {"closed": "true", "limit": 100}
mercados = requests.get(url, params=params, timeout=15).json()

for m in mercados:
    if "ufc" in m.get("question", "").lower():
        print(m["question"])
        print("  outcomes:", m.get("outcomes"))
        print("  precios:", m.get("outcomePrices"))
        print("  tokens:", m.get("clobTokenIds"))
        print()
