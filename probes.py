import pandas as pd
import requests
import json
import time

# Carregar CSV
df = pd.read_csv("resultados-processados_traceroute.csv")

probe_ids = df["prb_id"].dropna().unique().tolist()
print(f"Total de probes no CSV: {len(probe_ids)}")


# API RIPE Atlas
def get_probe_metadata(prb_id):
    url = f"https://atlas.ripe.net/api/v2/probes/{prb_id}/"

    try:
        r = requests.get(url, timeout=10)

        if r.status_code != 200:
            print(f"Probe {prb_id} não encontrada (status {r.status_code})")
            return None

        data = r.json()

        return {
            "prb_id": data.get("id"),
            "country_code": data.get("country_code"),
            "asn_v4": data.get("asn_v4"),
            "asn_v6": data.get("asn_v6"),
        }

    except Exception as e:
        print(f"Erro na probe {prb_id}: {e}")
        return None


# Coleta das probes
probes_metadata = []

for i, prb_id in enumerate(probe_ids):
    print(f"[{i+1}/{len(probe_ids)}] Buscando probe {prb_id}")

    meta = get_probe_metadata(prb_id)

    if meta:
        probes_metadata.append(meta)

    time.sleep(0.2)


# Salvar JSON
with open("probes_metadata.json", "w", encoding="utf-8") as f:
    json.dump(probes_metadata, f, indent=2, ensure_ascii=False)

print("Arquivo probes_metadata.json salvo")