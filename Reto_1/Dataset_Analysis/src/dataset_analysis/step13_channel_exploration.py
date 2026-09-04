"""Paso 13: ¿sirven los histogramas para diferenciar actividades?

Barre las 120 parejas de actividades × los 6 canales del sensor 1 y mide, para
cada combinación, el traslape entre histogramas (intersección de densidades
normalizadas: 0 = separables, 1 = indistinguibles). Con eso se puede responder
la pregunta con números en vez de con impresiones.

Produce:
  - `figures/step13_rejilla_histogramas.png`: seis ejemplos ordenados del par
    más separable al más traslapado, con la media de cada actividad marcada.
  - `figures/step13_traslape_min.png`: matriz 16×16 con el traslape del *mejor*
    canal para cada pareja de actividades.

Uso: uv run python -m dataset_analysis.step13_channel_exploration
"""

import numpy as np

from dataset_analysis.common import (
    CHANNELS_S1,
    MOVEMENTS,
    N_STEPS,
    SERIES_1,
    SERIES_2,
    SURFACE,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    concat_channel,
    load_movement,
    new_figure,
    save_figure,
    style_axes,
    trailing_zero_steps,
)

SENSOR = "1"
NBINS = 200
PCT_LO, PCT_HI = 0.1, 99.9
N_EJEMPLOS = 6


def densidades_por_canal(channel: int):
    """Histogramas de densidad de las 16 actividades sobre una rejilla común.

    La rejilla se define con los percentiles 0.1 y 99.9 del conjunto de los 16
    movimientos, no con el mínimo y el máximo: Yaw y Roll no están envueltos a
    ±180° y arrastran colas de hasta ±1,200° que, con una rejilla min–max,
    aplastarían toda la distribución en dos o tres bins. Los valores fuera de
    rango se recortan al bin extremo, así que la masa total se conserva y el
    índice de traslape sigue siendo comparable entre canales.
    """
    datos = [concat_channel(mov, channel, SENSOR) for mov in MOVEMENTS]
    pool = np.concatenate(datos)
    lo, hi = np.percentile(pool, [PCT_LO, PCT_HI])
    edges = np.linspace(lo, hi, NBINS + 1)
    dens = np.stack([np.histogram(np.clip(d, lo, hi), bins=edges, density=True)[0]
                     for d in datos])
    medias = np.array([d.mean() for d in datos])
    # Cuánto se sale del rango físico de un ángulo envuelto (±180°) y hasta dónde.
    cola = (float(np.mean(np.abs(pool) > 180)), float(pool.min()), float(pool.max()))
    return dens, edges, medias, cola


def matriz_traslape(dens: np.ndarray, edges: np.ndarray) -> np.ndarray:
    """Traslape (intersección) entre cada par de actividades para un canal."""
    w = np.diff(edges)
    n = len(dens)
    m = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            v = float(np.sum(np.minimum(dens[i], dens[j]) * w))
            m[i, j] = m[j, i] = v
    np.fill_diagonal(m, 1.0)
    return m


def diagnostico_calidad(min_run: int = 25) -> None:
    """Artefactos que se ven como picos aislados en los histogramas.

    Dos cosas ensucian las densidades y conviene tenerlas presentes al juzgar
    el traslape: repeticiones enteramente en cero (no aportan nada) y tramos
    con el sensor congelado en un mismo valor durante medio segundo o más, que
    concentran mucha masa en un solo bin.
    """
    vacias, total_rep = 0, 0
    congeladas = np.zeros(len(CHANNELS_S1))
    muestras = np.zeros(len(CHANNELS_S1))
    for mov in MOVEMENTS:
        array = load_movement(mov, SENSOR)
        total_rep += array.shape[0]
        for rep in array:
            pad = trailing_zero_steps(rep)
            if pad == N_STEPS:
                vacias += 1
                continue
            util = rep[: len(rep) - pad]
            for c in range(len(CHANNELS_S1)):
                x = util[:, c]
                cortes = np.flatnonzero(np.diff(x) != 0)
                largos = np.diff(np.r_[0, cortes + 1, x.size])
                congeladas[c] += largos[largos >= min_run].sum()
                muestras[c] += x.size

    print(f"\nDiagnóstico de calidad (sensor {SENSOR}):")
    print(f"  repeticiones totalmente en cero: {vacias} de {total_rep}"
          f" ({vacias / total_rep:.1%}) — se descartan al concatenar")
    print(f"  muestras dentro de tramos constantes >= {min_run} pasos"
          f" ({min_run / 50:.1f} s), por canal:")
    print("  " + ", ".join(f"{n} {congeladas[c] / muestras[c]:.2%}"
                           for c, n in enumerate(CHANNELS_S1)))


def panel_histograma(ax, i: int, j: int, channel: int, dens, edges, medias) -> None:
    """Dibuja en `ax` los histogramas de dos actividades y sus medias."""
    centros = (edges[:-1] + edges[1:]) / 2
    w = edges[1] - edges[0]
    for k, color in ((i, SERIES_1), (j, SERIES_2)):
        ax.bar(centros, dens[k], width=w, color=color, alpha=0.55, linewidth=0,
               label=f"act. {MOVEMENTS[k]}", zorder=3)
    for k, color in ((i, SERIES_1), (j, SERIES_2)):
        ax.axvline(medias[k], color=color, linewidth=1.8, linestyle=(0, (4, 3)), zorder=5)
    ax.set_xlim(edges[0], edges[-1])
    leg = ax.legend(frameon=False, fontsize=8, loc="upper right", handlelength=1.2)
    for t in leg.get_texts():
        t.set_color(TEXT_SECONDARY)


def main() -> None:
    dens, edges, medias, colas, matrices = {}, {}, {}, {}, {}
    for c in range(len(CHANNELS_S1)):
        dens[c], edges[c], medias[c], colas[c] = densidades_por_canal(c)
        matrices[c] = matriz_traslape(dens[c], edges[c])

    iu = np.triu_indices(len(MOVEMENTS), k=1)
    print(f"Sensor {SENSOR} · traslape de histogramas sobre las 120 parejas de actividades")
    print("(0 % = distribuciones disjuntas, 100 % = indistinguibles)\n")
    print("| Canal | rango del 99.8 % central | traslape medio | mínimo (par más separable)"
          " | parejas con traslape < 50 % |")
    print("|---|---|---:|---|---:|")
    for c, name in enumerate(CHANNELS_S1):
        v = matrices[c][iu]
        k = v.argmin()
        par = f"{MOVEMENTS[iu[0][k]]}–{MOVEMENTS[iu[1][k]]}"
        rango = f"{edges[c][0]:.0f}° a {edges[c][-1]:.0f}°"
        print(f"| {name} | {rango} | {v.mean():.1%} | {v.min():.1%} ({par})"
              f" | {int((v < 0.5).sum())} / 120 |")
    print("\nÁngulos fuera del rango envuelto ±180° (Yaw y Roll no vienen envueltos):")
    print("| Canal | % de muestras con \\|x\\| > 180° | mínimo | máximo |")
    print("|---|---:|---:|---:|")
    for c, name in enumerate(CHANNELS_S1):
        frac, mn, mx = colas[c]
        print(f"| {name} | {frac:.3%} | {mn:.0f}° | {mx:.0f}° |")

    # Para cada pareja, el mejor canal (el de menor traslape).
    apiladas = np.stack([matrices[c] for c in range(len(CHANNELS_S1))])
    mejor = apiladas.min(axis=0)
    mejor_canal = apiladas.argmin(axis=0)
    v_mejor = mejor[iu]
    print(f"\nUsando el mejor canal de los 6 para cada pareja:")
    print(f"  traslape medio            : {v_mejor.mean():.1%}")
    print(f"  parejas con traslape < 50 %: {int((v_mejor < 0.5).sum())} / 120")
    print(f"  parejas con traslape > 80 %: {int((v_mejor > 0.8).sum())} / 120")
    peor = v_mejor.argmax()
    print(f"  pareja más difícil        : {MOVEMENTS[iu[0][peor]]}–{MOVEMENTS[iu[1][peor]]}"
          f" con {v_mejor.max():.1%} incluso en su mejor canal"
          f" ({CHANNELS_S1[mejor_canal[iu[0][peor], iu[1][peor]]]})")
    conteo = np.bincount(mejor_canal[iu], minlength=len(CHANNELS_S1))
    print("  canal más veces el mejor  : "
          + ", ".join(f"{n} {int(k)}×" for n, k in zip(CHANNELS_S1, conteo)))

    diagnostico_calidad()

    # --- Figura 1: seis ejemplos, del más separable al más traslapado --------
    orden = np.argsort(v_mejor)
    idx = np.linspace(0, len(orden) - 1, N_EJEMPLOS).round().astype(int)
    ejemplos = [(int(iu[0][orden[t]]), int(iu[1][orden[t]])) for t in idx]

    fig, axes = new_figure(2, 3, figsize=(15, 7), dpi=200)
    for ax, (i, j) in zip(axes.ravel(), ejemplos):
        c = int(mejor_canal[i, j])
        panel_histograma(ax, i, j, c, dens[c], edges[c], medias[c])
        style_axes(ax,
                   f"{MOVEMENTS[i]} vs {MOVEMENTS[j]} · {CHANNELS_S1[c]}"
                   f" · traslape {mejor[i, j]:.0%}",
                   f"{CHANNELS_S1[c]} (grados)", "densidad")
        ax.title.set_fontsize(10)
    fig.suptitle("Del par más separable al más traslapado (cada panel usa su mejor canal)",
                 color=TEXT_PRIMARY, fontsize=13, x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    save_figure(fig, "step13_rejilla_histogramas.png")

    # --- Figura 2: matriz de traslape del mejor canal ------------------------
    fig, ax = new_figure(figsize=(7.5, 6.4), dpi=200)
    m = mejor.copy()
    np.fill_diagonal(m, np.nan)
    im = ax.imshow(m, cmap="Blues", vmin=0, vmax=1)
    ax.set_xticks(range(len(MOVEMENTS)), MOVEMENTS, rotation=90)
    ax.set_yticks(range(len(MOVEMENTS)), MOVEMENTS)
    style_axes(ax, "Traslape entre actividades (mejor de los 6 canales)",
               "actividad", "actividad")
    ax.grid(False)
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("traslape de histogramas", color=TEXT_SECONDARY, fontsize=9)
    cbar.ax.tick_params(colors=TEXT_SECONDARY, labelsize=8)
    cbar.outline.set_visible(False)
    fig.tight_layout()
    save_figure(fig, "step13_traslape_min.png")


if __name__ == "__main__":
    main()
