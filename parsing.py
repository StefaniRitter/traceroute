# Cada resultado do traceroute tem uma lista de saltos (hops), onde cada salto tem 3 amostras de Round Trip Time (tentativas). Algumas amostras podem ser "*", o que significa Timeout.

# A medição chegou ao destino?
# Se chegou, em qual hop? (número de saltos)
# Qual foi a latência? RTT do salto

# EXEMPLO:

'''
hop 1: from=10.0.1.x  -> não é o destino, continua
hop 2: from=10.0.2.x  -> não é o destino, continua
...
hop 8: from=198.51.100.10  -> é o destino! 
       → num_saltos = 8
       → latencia = RTT desse hop
       → chegou_ao_destino = True
'''

import json

# ARQUIVO_DADOS = "./dados_ficticios_ripe_atlas/raw_data/measurement_70000001_destino-A_ipv4.json"
ARQUIVO_DADOS = "./medições/ipv4/dazn-RIPE-Atlas-measurement-183792599-1782348180-to-1782434580.json"
dados = []

with open(ARQUIVO_DADOS, 'r', encoding='utf-8') as arquivo:
    for linha in arquivo:

        linha = linha.strip()

        if linha:
            dados.append(json.loads(linha))

    tabela_final = []

    # Aqui pega a medição completa pra cada probe 
    # Exemplo: Probe 1
    # {"dst_addr", "af": 4, ... , result [  -> usado em for hop in resultado["result"]
    #                   { "hop": 1,
    #                     "result": [       -> usado em for amostra in hop["result"]
    #                                 {"from", "ttl", "size":,"rtt"} #tentativa 1
    #                                 {"from", "ttl", "size":,"rtt"} #tentativa 2
    #                                 {"from", "ttl", "size":,"rtt"} #tentativa 2
    #                               ]
    #                   }
    #                   { "hop": X,
    #                     "result": [
    #                                 {"from", "ttl", "size":,"rtt"} #tentativa 1
    #                                 {"from", "ttl", "size":,"rtt"} #tentativa 2
    #                                 {"from", "ttl", "size":,"rtt"} #tentativa 2
    #                               ]
    #                   }
    #              ]
    for resultado in dados:
        prb_id = resultado["prb_id"]
        timestamp = resultado["timestamp"]
        dst_addr = resultado.get("dst_addr")
        af = resultado["af"]

        chegou_ao_destino = False
        num_saltos = None
        latencia = None

        # Percorre os hops em ordem, do 1 até o último, para cada probe
        for hop in resultado["result"]:
            numero_hop = hop.get("hop")
            if numero_hop is None:
                continue

            # Dentro de cada hop, são 3 amostras de RTT -> precisa achar a(s) amostra(s) válidas (que não sejam timeout "*") onde "from" seja igual ao destino
            rtts_validos_do_destino = []
            for amostra in hop["result"]:
                if "from" not in amostra:
                    continue
                if amostra["from"] == dst_addr:
                    if "rtt" in amostra:
                        rtts_validos_do_destino.append(amostra["rtt"])

            if rtts_validos_do_destino:
                chegou_ao_destino = True
                if numero_hop == 255:
                    num_saltos = None
                else:
                    num_saltos = numero_hop
                    
                latencia = min(rtts_validos_do_destino)
                break  # Não precisa olhar os hops seguintes

        # Salva a linha mesmo se não chegou, para calcular a taxa de falha depois
        tabela_final.append({
            "prb_id": prb_id,
            "timestamp": timestamp,
            "dst_addr": dst_addr,
            "af": af,
            "chegou_ao_destino": chegou_ao_destino,
            "num_saltos": num_saltos,
            "latencia_ms": latencia,
        })

print(f"Total de linhas processadas: {len(tabela_final)}")
print(f"Exemplo da primeira linha: {tabela_final[0]}")

    


