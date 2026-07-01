import json
import pandas as pd

# A medição chegou ao destino?
# Se chegou, em qual hop? (número de saltos)
# Qual foi a latência? RTT do salto

'''
LOOPS: 
NÍVEL 1: arquivo          →  1 destino + 1 protocolo
NÍVEL 2: linha            →  1 probe × 1 rodada  
NÍVEL 3: hop              →  1 roteador no caminho
NÍVEL 4: amostra          →  1 das 3 tentativas de RTT
'''

# Lista dos 6 arquivos de medição (3 destinos × 2 protocolos)
# Cada entrada tem: nome do destino, família de endereço (4=IPv4, 6=IPv6) e caminho do arquivo
ARQUIVOS = [
    {"af": 4, "dst_name": "dazn",  "path": "medições 24-06\ipv4\dazn-4-RIPE-Atlas-measurement-183792599-1782331200-to-1782424800.json"},
    {"af": 6, "dst_name": "dazn",   "path": "medições 24-06\ipv6\dazn-6-RIPE-Atlas-measurement-183792600-1782331200-to-1782424800.json"},
    {"af": 4, "dst_name": "disney", "path": "medições 24-06\ipv4\disney-4-RIPE-Atlas-measurement-183792601-1782331200-to-1782424800.json"},
    {"af": 6, "dst_name": "disney", "path": "medições 24-06\ipv6\disney-6-RIPE-Atlas-measurement-183792602-1782331200-to-1782424800.json"},
    {"af": 4, "dst_name": "youtube", "path": "medições 24-06\ipv4\youtube-4-RIPE-Atlas-measurement-183792597-1782331200-to-1782424800.json"},
    {"af": 6, "dst_name": "youtube", "path": "medições 24-06\ipv6\youtube-6-RIPE-Atlas-measurement-183792598-1782331200-to-1782424800.json"},
]

# Lista para todas as linhas processadas de todos os arquivos
tabela_final = []

# Itera sobre cada arquivo
for arquivo_info in ARQUIVOS:
    with open(arquivo_info["path"], 'r', encoding='utf-8') as arquivo:

        # Cada linha é um resultado independente (1 linha = 1 probe em 1 rodada específica)
        for linha in arquivo:
            linha = linha.strip()
            if not linha:
                continue # Ignora linhas vazias

            # Converte a linha de texto pra um dicionário
            resultado = json.loads(linha)

            # Extrai os metadados 
            prb_id    = resultado["prb_id"] # ID da probe que gerou o resultado
            timestamp = resultado["timestamp"] # Quando foi gerado
            dst_addr  = resultado.get("dst_addr") # IP do destino
            af        = resultado["af"] # Protocolo: 4 para IPv4 e 6 para IPv6

            # Valores que serão preenchidos ao percorrer os hops
            chegou_ao_destino = False
            num_saltos        = None # Quantos hops até chegar ao destino
            latencia          = None # # RTT mínimo do hop que chegou no destino (pois cada hop tem 3 tentativas)

            # Percorre os hops do traceroute em ordem
            # Cada hop é 1 roteador no caminho até o destino
            for hop in resultado["result"]:
                numero_hop = hop.get("hop")
                if numero_hop is None:
                    continue # Pula se tiver hop malformado

                # Em cada hop, tem 3 amostras de RTT
                # Filtra as amostras válidas onde "from" == destino e 
                rtts_validos = []
                for amostra in hop["result"]:
                    if "from" not in amostra: # exclui timeouts (só têm {"x":"*"})
                        continue
                    if amostra["from"] == dst_addr and "rtt" in amostra: # Só conta se respondeu o IP destino e exclui amostras sem RTT
                            rtts_validos.append(amostra["rtt"]) 

                # Se pelo menos 1 amostra do hop for válida:
                if rtts_validos:
                    chegou_ao_destino = True
                    if numero_hop == 255:
                        num_saltos = None # O número de saltos fica None porque não representa o caminho real
                    else:
                        num_saltos = numero_hop
                    
                    # Usa o menor RTT entre as amostras válidas como latência
                    latencia   = min(rtts_validos)

                    # Como já achou o destino, não precisa olhar os próximos hops
                    break

            # Salva a linha (Probe X Rodada) mesmo se não chegou, para calcular a taxa de falha depois
            tabela_final.append({
                "dst_name":          arquivo_info["dst_name"], # dazn, disney, youtube
                "prb_id":            prb_id,
                "timestamp":         timestamp,
                "dst_addr":          dst_addr,
                "af":                af,
                "chegou_ao_destino": chegou_ao_destino,
                "num_saltos":        num_saltos,
                "latencia_ms":       latencia,
            })

# Converte a lista de dicionários em DataFrame para facilitar análises e gráficos
df = pd.DataFrame(tabela_final)

# Salva o DataFrame em CSV
df.to_csv("resultados-processados_traceroute.csv", index=False, encoding="utf-8")
print("CSV salvo")

# Verificação de sanidade: conta resultados por destino e protocolo
# Esperado: ~1125 por combinação (45 probes × 25 rodadas)
# Valores muito menores indicam arquivo incompleto ou probes offline
print(f"Total de resultados: {len(df)} \n")
print(df.groupby(["dst_name", "af"])[["chegou_ao_destino"]].count())