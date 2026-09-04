"""Pasos 11 y 12: histogramas superpuestos de dos actividades, con su media.

Se toman dos movimientos, se concatenan todas sus repeticiones (sin el relleno
de ceros) para el canal elegido y se dibujan ambos histogramas en los mismos
ejes con la misma rejilla de bins, para poder leer el traslape. Sobre cada
histograma se traza una línea vertical punteada en la media de esa actividad
(paso 12).

Se reporta además un índice de traslape: la intersección de histogramas
(suma de los mínimos de las dos densidades normalizadas), que va de 0 (sin
solape) a 1 (distribuciones idénticas).

Uso: uv run python -m dataset_analysis.step11_histograms [movA] [movB] [canal]
"""

import sys

import numpy as np

from dataset_analysis.common import (
    SERIES_1,
    SERIES_2,
    SURFACE,
    TEXT_SECONDARY,
    channel_names,
    concat_channel,
    new_figure,
    save_figure,
    style_axes,
)

SENSOR = "1"
MOV_A = "001"
MOV_B = "013"
CHANNEL = 0
BINS = 80


def overlap_index(a: np.ndarray, b: np.ndarray, edges: np.ndarray) -> float:
    """Intersección de histogramas normalizados: 0 = disjuntos, 1 = idénticos."""
    pa, _ = np.histogram(a, bins=edges, density=True)
    pb, _ = np.histogram(b, bins=edges, density=True)
    widths = np.diff(edges)
    return float(np.sum(np.minimum(pa, pb) * widths))


def plot_pair(mov_a: str, mov_b: str, channel: int, sensor: str = SENSOR,
              bins: int = BINS, save: bool = True):
    """Dibuja los dos histogramas y devuelve (fig, ax, traslape)."""
    name = channel_names(sensor)[channel]
    a = concat_channel(mov_a, channel, sensor)
    b = concat_channel(mov_b, channel, sensor)
    edges = np.histogram_bin_edges(np.concatenate([a, b]), bins=bins)
    traslape = overlap_index(a, b, edges)

    fig, ax = new_figure(figsize=(10, 4.6), dpi=200)
    for datos, mov, color in ((a, mov_a, SERIES_1), (b, mov_b, SERIES_2)):
        ax.hist(datos, bins=edges, density=True, color=color, alpha=0.55,
                label=f"actividad {mov}  (n={datos.size:,})", zorder=3)

    # Paso 12: una línea vertical en la media de cada actividad. Las etiquetas
    # van abajo (el borde superior lo ocupa la leyenda) y se alinean hacia
    # adentro cuando la media queda cerca de un extremo del eje.
    span = edges[-1] - edges[0]
    medias = [a.mean(), b.mean()]
    posiciones = [(m - edges[0]) / span for m in medias]
    # Si las dos medias caen casi encima, se escalona la segunda etiqueta.
    juntas = abs(posiciones[0] - posiciones[1]) < 0.18
    for k, (mov, color) in enumerate(((mov_a, SERIES_1), (mov_b, SERIES_2))):
        media, pos = medias[k], posiciones[k]
        ax.axvline(media, color=color, linewidth=2.2, linestyle=(0, (4, 3)), zorder=5)
        ha = "left" if pos < 0.15 else "right" if pos > 0.85 else "center"
        dy = 6 + (16 if juntas and k else 0)
        ax.annotate(f"media {mov}: {media:.1f}°", xy=(media, 0.0),
                    xycoords=("data", "axes fraction"), xytext=(0, dy),
                    textcoords="offset points", ha=ha, va="bottom",
                    fontsize=8, color=TEXT_SECONDARY, zorder=6,
                    bbox=dict(boxstyle="round,pad=0.25", facecolor=SURFACE,
                              edgecolor="none", alpha=0.85))

    style_axes(ax,
               f"Actividades {mov_a} vs {mov_b} · sensor {sensor}, canal {name}"
               f"  ·  traslape {traslape:.0%}",
               f"{name} (grados)", "densidad")
    leg = ax.legend(frameon=False, fontsize=9, loc="upper right")
    for texto in leg.get_texts():
        texto.set_color(TEXT_SECONDARY)
    ax.set_xlim(edges[0], edges[-1])
    ax.set_ylim(0, ax.get_ylim()[1] * 1.12)

    fig.tight_layout()
    if save:
        save_figure(fig, f"step11_{mov_a}_vs_{mov_b}_s{sensor}_{name}.png")
    return fig, ax, traslape


def main() -> None:
    args = sys.argv[1:]
    mov_a = args[0] if len(args) > 0 else MOV_A
    mov_b = args[1] if len(args) > 1 else MOV_B
    channel = int(args[2]) if len(args) > 2 else CHANNEL
    name = channel_names(SENSOR)[channel]

    a = concat_channel(mov_a, channel, SENSOR)
    b = concat_channel(mov_b, channel, SENSOR)
    print(f"Sensor {SENSOR}, canal {channel} ({name})")
    for datos, mov in ((a, mov_a), (b, mov_b)):
        print(f"  actividad {mov}: n={datos.size:,}  media={datos.mean():7.2f}°"
              f"  mediana={np.median(datos):7.2f}°  desv={datos.std(ddof=0):6.2f}°"
              f"  rango=[{datos.min():.1f}, {datos.max():.1f}]")

    _, _, traslape = plot_pair(mov_a, mov_b, channel)
    print(f"\n  separación de medias: {abs(a.mean() - b.mean()):.2f}°")
    print(f"  traslape (intersección de histogramas): {traslape:.1%}")


if __name__ == "__main__":
    main()
