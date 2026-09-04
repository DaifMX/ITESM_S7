"""Paso 9: conteo de repeticiones por actividad.

Gráfica de barras con una barra por movimiento (000–015) cuya altura es el
número de repeticiones disponibles, usando todos los datos. Se imprime además
un diagnóstico de balance (mín., máx., razón máx./mín. y desviación respecto al
reparto uniforme).

El conteo es el mismo para el sensor 1 y el 2 (verificado en el paso 4), así que
la gráfica describe el dataset completo, no sólo el sensor elegido.

Uso: uv run python -m dataset_analysis.step09_repetition_counts
"""

import numpy as np

from dataset_analysis.common import (
    MOVEMENTS,
    SERIES_1,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    load_movement,
    new_figure,
    save_figure,
    style_axes,
)

SENSOR = "1"


def main() -> None:
    counts = np.array([load_movement(m, SENSOR).shape[0] for m in MOVEMENTS])
    counts_s2 = np.array([load_movement(m, "2").shape[0] for m in MOVEMENTS])
    total = int(counts.sum())
    uniform = total / len(counts)
    ratio = counts.max() / counts.min()

    print("Repeticiones por actividad (sensor 1):")
    for mov, n in zip(MOVEMENTS, counts):
        print(f"  {mov}: {n:4d}   ({n / total:5.1%})")
    print(f"\n  total          : {total}")
    print(f"  mínimo / máximo: {counts.min()} (mov. {MOVEMENTS[counts.argmin()]})"
          f" / {counts.max()} (mov. {MOVEMENTS[counts.argmax()]})")
    print(f"  razón máx/mín  : {ratio:.2f}")
    print(f"  media / mediana: {counts.mean():.1f} / {np.median(counts):.1f}")
    print(f"  desv. estándar : {counts.std(ddof=0):.1f}")
    print(f"  reparto uniforme sería {uniform:.1f} por actividad")
    print(f"  ¿mismos conteos en el sensor 2?: {np.array_equal(counts, counts_s2)}")

    fig, ax = new_figure(figsize=(10, 4.5), dpi=200)
    bars = ax.bar(MOVEMENTS, counts, color=SERIES_1, width=0.72,
                  linewidth=0, zorder=3)
    ax.bar_label(bars, padding=3, fontsize=8, color=TEXT_SECONDARY)

    ax.plot([-0.6, len(MOVEMENTS) - 0.4], [uniform, uniform], color=TEXT_PRIMARY,
            linewidth=1.2, linestyle=(0, (5, 4)), alpha=0.55, zorder=4)
    ax.text(len(MOVEMENTS) - 0.2, uniform, f"reparto uniforme\n({uniform:.0f})",
            ha="left", va="center", fontsize=8, color=TEXT_SECONDARY)

    style_axes(ax,
               f"Repeticiones por actividad · {total:,} repeticiones en 16 movimientos",
               "actividad (movementID)", "repeticiones")
    ax.set_ylim(0, counts.max() * 1.14)
    ax.set_xlim(-0.7, len(MOVEMENTS) + 1.6)

    fig.tight_layout()
    save_figure(fig, "step09_repeticiones_por_actividad.png")


if __name__ == "__main__":
    main()
