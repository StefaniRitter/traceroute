# Medições de Rotas e Comparação de Desempenho entre IPV4 e IPV6 

## Conceitos

### Probe
É o aparelho físico (ou virtual) num lugar específico do mundo. Cada probe tem um ID único (prb_id) e metadados associados: em que país está, em que continente, qual a rede/provedor (ASN) dela, etc.

### Measurement (medição)
Traceroute IPv4 pro destino X, repetido a cada 60 minutos, durante 24 horas, usando 45 probes" = UM measurement.
Para 3 destinos × 2 famílias (IPv4 e IPv6), 6 measurements no total (um pra cada combinação destino+família).

### Measurement ID (msm_id)
É número único que identifica cada measurement criado. ID que será usado pra buscar os resultados depois, e também entregar na lista de IDs pedida no trabalho.

### Result (resultado)
Cada vez que uma probe executa a tarefa do measurement (uma "rodada"), ela gera um resultado. Como existem 45 probes rodando a cada 60min por 24h (25 rodadas, contando a inicial), cada measurement vai ter 45 × 25 = 1125 resultados.
Cada resultado individual contém: qual probe gerou (prb_id), em que momento (timestamp), pra qual destino (dst_addr), e o traceroute completo até lá (ou até onde conseguiu chegar).

### Traceroute
É a técnica de rede: ela descobre o caminho (a sequência de roteadores) que os pacotes percorrem desde a probe até o destino. Cada roteador no caminho é chamado de hop (salto).
Para cada hop, o traceroute manda 3 pacotes de teste e mede o tempo de resposta de cada um (o RTT, ou Round Trip Time, ida e volta, em milissegundos). É daí que vem a "latência" que será analisada.

### AF (Address Family)
É o campo que diz se aquele measurement/resultado é IPv4 (af: 4) ou IPv6 (af: 6). Mesmo destino, mesmas probes, mas duas "versões" da medição, por isso que são 6 measurements (3 destinos × 2 famílias) em vez de 3.

### Tratamento
- 1 arquivo JSON = 1 measurement inteiro (todas as probes e todas as rodadas daquele destino+família);

- Pra "chegar ao destino", é necessário checar se o from do último hop é igual ao dst_addr. Se não for (ou se só tiver *), aquela medição falhou e não deve entrar no gráfico de latência/saltos daquele momento;

- A latência que será plotada geralmente é o RTT do hop final (o que chegou no destino);

- O número de saltos é simplesmente quantos hops existem no array result até bater no destino.

### No total

45 probes (fixas, distribuídas por todos os continentes), disparando 25 vezes
(a cada 60 minutos durante 24h)

```text
├──► Destino 1 (IPv4) → 1.125 resultados
├──► Destino 1 (IPv6) → 1.125 resultados
├──► Destino 2 (IPv4) → 1.125 resultados
├──► Destino 2 (IPv6) → 1.125 resultados
├──► Destino 3 (IPv4) → 1.125 resultados
└──► Destino 3 (IPv6) → 1.125 resultados
                        ───────────────────────
                        Total: 6.750 resultados
```
