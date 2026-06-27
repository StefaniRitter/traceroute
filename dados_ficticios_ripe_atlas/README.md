# Dados fictícios — RIPE Atlas (para desenvolvimento do pipeline)

Estes arquivos foram gerados artificialmente, mas seguem **exatamente** o
mesmo formato que o RIPE Atlas retorna de verdade em
`/api/v2/measurements/{id}/results/?format=json`. A ideia é vocês poderem
escrever e testar o `parsing.py` e o `analise.py` agora, e depois só trocar
os arquivos da pasta `raw_data/` pelos JSONs reais — sem precisar mudar
nada no código.

## Estrutura dos arquivos

```
raw_data/
  measurement_70000001_destino-A_ipv4.json   (45 probes x 25 rodadas = 1125 resultados)
  measurement_70000002_destino-A_ipv6.json
  measurement_70000003_destino-B_ipv4.json
  measurement_70000004_destino-B_ipv6.json
  measurement_70000005_destino-C_ipv4.json
  measurement_70000006_destino-C_ipv6.json

probes_metadata.json    -> mapa prb_id -> país / continente (45 probes)
resumo_measurements.json -> lista dos measurement IDs fictícios e a quais
                             destino/família cada um corresponde
```

## Pontos importantes que foram simulados de propósito

1. **~8% das medições "não chegam ao destino"** (IPv4) e um pouco mais em
   IPv6 (~15% combinado) — isso é DE PROPÓSITO, porque o enunciado pede
   explicitamente para vocês verificarem se a medição chegou ao destino
   antes de usá-la nos gráficos. No parsing, vocês vão precisar checar se
   o `from` do último hop é igual ao `dst_addr`.

2. **Timeouts pontuais (`{"x": "*"}`)** em ~5% das amostras individuais de
   RTT dentro de cada hop — isso também acontece nos dados reais e o
   parsing precisa saber ignorar/tratar isso (ex: usar `min()` dos RTTs
   válidos daquele hop, descartando os `"*"`).

3. **Latências diferentes por continente** (proporcionais à distância
   "geográfica" simulada) e levemente maiores em IPv6 — só para os
   gráficos ficarem visualmente plausíveis durante os testes.

## Quando os dados reais chegarem

1. Apaguem o conteúdo de `raw_data/`
2. Coloquem os JSONs reais baixados do RIPE Atlas (mesma estrutura)
3. Atualizem `probes_metadata.json` com o país/continente real das 45
   probes que vocês efetivamente selecionaram (podem pegar isso na página
   de detalhes de cada probe, ou com uma chamada simples a
   `https://atlas.ripe.net/api/v2/probes/{id}/`)
4. Rodem o pipeline normalmente — nenhuma mudança de código deve ser
   necessária

## Reprodutibilidade

O script `gerar_dados_ficticios.py` usa `random.seed(42)`, então rodar de
novo gera sempre os mesmos dados. Se quiserem variar os cenários (mais
falhas, mais timeouts, outro período), é só ajustar os parâmetros no topo
do script.
