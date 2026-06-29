import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import json
import os

# Configuração
BASE_DIR = "graficos"

df = pd.read_csv("resultados-processados_traceroute.csv")
df["latencia_ms"] = pd.to_numeric(df["latencia_ms"], errors="coerce")
df["num_saltos"] = pd.to_numeric(df["num_saltos"], errors="coerce")
df["data"] = pd.to_datetime(df["timestamp"], unit="s").dt.tz_localize("UTC").dt.tz_convert("America/Sao_Paulo").dt.tz_localize(None)

with open("probes_metadata.json", "r", encoding="utf-8") as f:
    probes = json.load(f)

probes_df = pd.DataFrame(probes)

df = df.merge(
    probes_df[["prb_id", "country_code"]],
    on="prb_id",
    how="left"
)

CODE_TO_INFO = {
    "BR": ("Brazil", "South America"),
    "AR": ("Argentina", "South America"),
    "CL": ("Chile", "South America"),
    "US": ("United States", "North America"),
    "CA": ("Canada", "North America"),
    "MX": ("Mexico", "North America"),
    "DE": ("Germany", "Europe"),
    "FR": ("France", "Europe"),
    "PT": ("Portugal", "Europe"),
    "JP": ("Japan", "Asia"),
    "IN": ("India", "Asia"),
    "KR": ("South Korea", "Asia"),
    "ZA": ("South Africa", "Africa"),
    "KE": ("Kenya", "Africa"),
    "EG": ("Egypt", "Africa"),
}

df["country"] = df["country_code"].map(lambda x: CODE_TO_INFO.get(x, ("Unknown", "Unknown"))[0])
df["continent"] = df["country_code"].map(lambda x: CODE_TO_INFO.get(x, ("Unknown", "Unknown"))[1])
df["hora"] = df["data"].dt.floor("h") # Arredonda para hora cheia para agrupar o eixo X por hora

os.makedirs(BASE_DIR, exist_ok=True)

# Plotar gráfico
def plot_multiline(pivot_df, title, xlabel, ylabel, outpath):
    """
    pivot_df: DataFrame com índice = hora, colunas = países ou continentes,
    valores = métrica média
    """
    fig, ax = plt.subplots(figsize=(14, 6))

    for col in pivot_df.columns:
        ax.plot(pivot_df.index, pivot_df[col], marker="o", linewidth=2, markersize=4, label=col)

    ax.set_title(title, fontsize=13)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(True, alpha=0.3)

    # 24h a partir do primeiro timestamp
    inicio = pivot_df.index.min()
    fim = inicio + pd.Timedelta(hours=24)
    ax.set_xlim(inicio, fim)

    # Mostra um tick a cada hora, formato HH:MM
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

   # Legenda abaixo do gráfico com espaço
    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.22),  # quanto mais negativo, mais distante do eixo X
        ncol=4,
        fontsize=8,
        framealpha=0,
        edgecolor="none"
    )

    plt.savefig(outpath, dpi=300, transparent=True, bbox_inches="tight")
    plt.close()


# Processamento
destinos = df["dst_name"].unique()

for destino in destinos:

    dest_df = df[df["dst_name"] == destino]
    dest_slug = destino.lower().replace(" ", "_").replace("/", "_")

    lat_dir = os.path.join(BASE_DIR, dest_slug, "latencia")
    hop_dir = os.path.join(BASE_DIR, dest_slug, "saltos")

    os.makedirs(lat_dir, exist_ok=True)
    os.makedirs(hop_dir, exist_ok=True)

    # ─────────────────────────────────────────
    # LATÊNCIA — Gráficos 1-4
    # ─────────────────────────────────────────

    # Gráfico 1 – Latência por país (IPv4)
    # Gráfico 2 – Latência por país (IPv6)
    for af in [4, 6]:
        subset = dest_df[dest_df["af"] == af]
        if subset.empty:
            continue

        pivot = (
            subset
            .groupby(["hora", "country"])["latencia_ms"]
            .mean()
            .unstack("country")
        )

        plot_multiline(
            pivot,
            title=f"Latência por país - IPv{af} - {destino}",
            xlabel="Hora",
            ylabel="Latência (ms)",
            outpath=os.path.join(lat_dir, f"latencia_pais_ipv{af}.png")
        )

    # Gráfico 3 – Latência por continente (IPv4)
    # Gráfico 4 – Latência por continente (IPv6)
    for af in [4, 6]:
        subset = dest_df[dest_df["af"] == af]
        if subset.empty:
            continue

        pivot = (
            subset
            .groupby(["hora", "continent"])["latencia_ms"]
            .mean()
            .unstack("continent")
        )

        plot_multiline(
            pivot,
            title=f"Latência por continente - IPv{af} - {destino}",
            xlabel="Hora",
            ylabel="Latência (ms)",
            outpath=os.path.join(lat_dir, f"latencia_continente_ipv{af}.png")
        )

    # ─────────────────────────────────────────
    # SALTOS — Gráficos 5-8
    # ─────────────────────────────────────────

    # Gráfico 5 – Saltos por país (IPv4)
    # Gráfico 6 – Saltos por país (IPv6)
    for af in [4, 6]:
        subset = dest_df[dest_df["af"] == af]
        if subset.empty:
            continue

        pivot = (
            subset
            .groupby(["hora", "country"])["num_saltos"]
            .mean()
            .unstack("country")
        )

        plot_multiline(
            pivot,
            title=f"Saltos por país - IPv{af} - {destino}",
            xlabel="Hora",
            ylabel="Número de saltos",
            outpath=os.path.join(hop_dir, f"saltos_pais_ipv{af}.png"),
        )

    # Gráfico 7 – Saltos por continente (IPv4)
    # Gráfico 8 – Saltos por continente (IPv6)
    for af in [4, 6]:
        subset = dest_df[dest_df["af"] == af]
        if subset.empty:
            continue

        pivot = (
            subset
            .groupby(["hora", "continent"])["num_saltos"]
            .mean()
            .unstack("continent")
        )

        plot_multiline(
            pivot,
            title=f"Saltos por continente - IPv{af} - {destino}",
            xlabel="Hora",
            ylabel="Número de saltos",
            outpath=os.path.join(hop_dir, f"saltos_continente_ipv{af}.png")
        )

print("Gráficos gerados")