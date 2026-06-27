"""
gerar_dados_ficticios.py

Gera arquivos JSON fictícios no MESMO FORMATO retornado pela API do RIPE Atlas
para medições de traceroute (https://atlas.ripe.net/api/v2/measurements/{id}/results/?format=json).

Objetivo: permitir o desenvolvimento e teste do pipeline de parsing/análise
ANTES de ter acesso aos dados reais da medição do grupo.

IMPORTANTE: estes dados são 100% fictícios (latências e rotas geradas
aleatoriamente, porém de forma realista). Quando os dados reais chegarem,
basta substituir os arquivos em /raw_data/ pelos JSONs reais do RIPE Atlas
-- o parsing.py não precisa mudar, pois o formato é idêntico.
"""

import json
import random
import os
from datetime import datetime, timedelta

random.seed(42)  # reprodutibilidade

# ---------------------------------------------------------------------------
# 1) Definição das 45 probes fictícias (5 continentes x 3 países x 3 probes)
# ---------------------------------------------------------------------------

ESTRUTURA_GEO = {
    "South America": ["Brazil", "Argentina", "Chile"],
    "North America": ["United States", "Canada", "Mexico"],
    "Europe": ["Germany", "France", "Portugal"],
    "Asia": ["Japan", "India", "South Korea"],
    "Africa": ["South Africa", "Kenya", "Egypt"],
}

# Faixas de latência "base" por continente em relação a um destino fictício
# hospedado no Brasil -- só para os dados ficarem plausíveis (mais distante
# geograficamente => maior RTT base). Cada destino tem seu próprio
# multiplicador.
LATENCIA_BASE_MS = {
    "South America": 25,
    "North America": 110,
    "Europe": 190,
    "Asia": 280,
    "Africa": 230,
}

probes = []
prb_id = 10000
for continente, paises in ESTRUTURA_GEO.items():
    for pais in paises:
        for i in range(3):
            probes.append({
                "prb_id": prb_id,
                "country_code": pais[:2].upper(),
                "country": pais,
                "continent": continente,
                "asn_v4": random.randint(1000, 65000),
                "asn_v6": random.randint(1000, 65000),
            })
            prb_id += 1

assert len(probes) == 45, f"Esperado 45 probes, gerado {len(probes)}"

# Salva o "mapa" probe -> país/continente, que normalmente viria de uma
# chamada separada à API (/api/v2/probes/{id}/) e que vocês vão precisar
# para fazer os agregados por país/continente.
with open("probes_metadata.json", "w", encoding="utf-8") as f:
    json.dump(probes, f, indent=2, ensure_ascii=False)

# ---------------------------------------------------------------------------
# 2) Definição dos destinos fictícios (3 destinos relacionados, ex: DNS
#    públicos -- só de exemplo, troquem pelos destinos reais do grupo)
# ---------------------------------------------------------------------------

DESTINOS = [
    {"nome": "destino-A", "ipv4": "198.51.100.10", "ipv6": "2001:db8:aaaa::10"},
    {"nome": "destino-B", "ipv4": "198.51.100.20", "ipv6": "2001:db8:bbbb::20"},
    {"nome": "destino-C", "ipv4": "198.51.100.30", "ipv6": "2001:db8:cccc::30"},
]

# ---------------------------------------------------------------------------
# 3) Geração das medições: 24h, a cada 60 min => 25 timestamps
# ---------------------------------------------------------------------------

INICIO = datetime(2026, 6, 1, 0, 0, 0)
N_RODADAS = 25  # 0h, 1h, 2h, ..., 24h
INTERVALO_MIN = 60

MSM_ID_BASE = 70000000  # ID fictício de measurement, só para preencher o campo


def gerar_hop(rtt_base, hop_num, chegou):
    """Gera um hop de traceroute com 3 amostras de RTT (padrão RIPE Atlas)."""
    amostras = []
    for _ in range(3):
        if random.random() < 0.05:  # 5% de chance de timeout naquela amostra
            amostras.append({"x": "*"})
        else:
            rtt = max(0.1, rtt_base + random.gauss(0, rtt_base * 0.08))
            amostras.append({
                "from": f"10.0.{hop_num}.{random.randint(1,254)}",
                "ttl": 64 - hop_num,
                "size": 28,
                "rtt": round(rtt, 3),
            })
    return amostras


def gerar_traceroute(prb, destino, af, ts, msm_id):
    """Gera um único resultado de traceroute fictício, no formato RIPE Atlas."""
    continente = prb["continent"]
    rtt_final_base = LATENCIA_BASE_MS[continente] * (1.0 if af == 4 else 1.15)
    # variação ao longo do tempo (ruído + leve tendência diurna)
    hora = ts.hour
    variacao_diurna = 5 * (1 + 0.3 * (hora % 12) / 12)
    rtt_final_base += variacao_diurna

    n_hops = random.randint(8, 16)

    # 92% das medições chegam ao destino; 8% falham (timeout antes do fim,
    # ou servidor não responde -- isso é PROPOSITAL, para que vocês
    # pratiquem a validação "chegou ao destino" pedida no enunciado).
    chegou_ao_destino = random.random() < 0.92
    # IPv6 tem uma chance um pouco maior de falhar, também de propósito
    if af == 6:
        chegou_ao_destino = random.random() < 0.85 and chegou_ao_destino

    dst_addr = destino["ipv4"] if af == 4 else destino["ipv6"]

    hops_resultado = []
    for h in range(1, n_hops + 1):
        rtt_hop = rtt_final_base * (h / n_hops) * random.uniform(0.85, 1.1)
        amostras = gerar_hop(rtt_hop, h, chegou_ao_destino)
        hops_resultado.append({"hop": h, "result": amostras})

    # Se chegou ao destino, o último hop deve ter "from" == dst_addr
    if chegou_ao_destino:
        ultimo = hops_resultado[-1]["result"]
        for amostra in ultimo:
            if "x" not in amostra:
                amostra["from"] = dst_addr
                amostra["rtt"] = round(rtt_final_base * random.uniform(0.98, 1.02), 3)
    # Se NÃO chegou, o último hop fica com um IP genérico (não é o destino)
    # simulando timeout/firewall -- e geralmente vem com *'s no fim também.

    epoch = int(ts.timestamp())

    return {
        "fw": 5020,
        "mver": "2.4.1",
        "lts": 50,
        "endtime": epoch + 5,
        "dst_name": dst_addr,
        "dst_addr": dst_addr,
        "src_addr": f"192.168.{prb['prb_id'] % 256}.1",
        "proto": "ICMP",
        "af": af,
        "size": 48,
        "paris_id": 8,
        "result": hops_resultado,
        "msm_id": msm_id,
        "prb_id": prb["prb_id"],
        "timestamp": epoch,
        "msm_name": "Traceroute",
        "from": f"192.168.{prb['prb_id'] % 256}.1",
        "type": "traceroute",
        "group_id": msm_id,
    }


# ---------------------------------------------------------------------------
# 4) Monta um arquivo JSON por (destino, família) -- exatamente como o RIPE
#    Atlas entrega: um array de resultados (todas as probes, todos os
#    timestamps) por measurement_id.
# ---------------------------------------------------------------------------

os.makedirs("raw_data", exist_ok=True)

msm_id_counter = MSM_ID_BASE
resumo_measurement_ids = []

for destino in DESTINOS:
    for af in (4, 6):
        msm_id_counter += 1
        resultados = []
        for rodada in range(N_RODADAS):
            ts = INICIO + timedelta(minutes=INTERVALO_MIN * rodada)
            for prb in probes:
                resultados.append(
                    gerar_traceroute(prb, destino, af, ts, msm_id_counter)
                )

        nome_arquivo = f"raw_data/measurement_{msm_id_counter}_{destino['nome']}_ipv{af}.json"
        with open(nome_arquivo, "w", encoding="utf-8") as f:
            json.dump(resultados, f, indent=2, ensure_ascii=False)

        resumo_measurement_ids.append({
            "msm_id": msm_id_counter,
            "destino": destino["nome"],
            "af": af,
            "arquivo": nome_arquivo,
            "n_resultados": len(resultados),
        })
        print(f"Gerado: {nome_arquivo}  ({len(resultados)} resultados)")

with open("resumo_measurements.json", "w", encoding="utf-8") as f:
    json.dump(resumo_measurement_ids, f, indent=2, ensure_ascii=False)

print("\nConcluído. Arquivos em ./raw_data/, metadados em probes_metadata.json")
