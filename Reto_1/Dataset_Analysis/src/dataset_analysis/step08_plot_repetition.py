"""Paso 8: grafica en el tiempo un canal de una repetición de una actividad.

Selección (paso 7: se trabaja con el **sensor 1**, los ángulos de Euler de las
dos IMU del miembro afectado):

  - actividad   : movimiento 000
  - repetición  : índice 0 (sin relleno de ceros, ver paso 4)
  - canal       : 0 -> Pitch1 (IMU S1, antebrazo)

El eje X está en segundos: 880 pasos a 50 Hz = 17.6 s. Si la repetición
elegida tuviera relleno de ceros al final, se sombrea esa zona para no
confundirla con señal real.

Uso: uv run python -m dataset_analysis.step08_plot_repetition
"""

import numpy as np

from dataset_analysis.common import (
    CHANNELS_S1,
    FS_HZ,
    SERIES_1 as SERIES,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    load_movement,
    new_figure,
    save_figure,
    trailing_zero_steps,
)

SENSOR = "1"
MOVEMENT = "000"
REPETITION = 0
CHANNEL = 0


def main() -> None:
    array = load_movement(MOVEMENT, SENSOR)
    rep = array[REPETITION]
    y = rep[:, CHANNEL]
    t = np.arange(len(y)) / FS_HZ
    pad = trailing_zero_steps(rep)
    name = CHANNELS_S1[CHANNEL]

    valid = y[: len(y) - pad] if pad else y
    print(f"Archivo: {MOVEMENT}_{SENSOR}.npy  {array.shape}")
    print(f"Repetición {REPETITION}, canal {CHANNEL} ({name})")
    print(f"  duración      : {len(y) / FS_HZ:.1f} s ({len(y)} pasos a {FS_HZ} Hz)")
    print(f"  relleno ceros : {pad} pasos ({pad / FS_HZ:.1f} s)")
    print(f"  rango         : {valid.min():.1f}° a {valid.max():.1f}°")
    print(f"  media / desv. : {valid.mean():.1f}° / {valid.std():.1f}°")

    fig, ax = new_figure(figsize=(10, 4), dpi=200)

    ax.axhline(0, color=TEXT_SECONDARY, linewidth=0.8, alpha=0.35, zorder=1)
    ax.grid(axis="y", color=TEXT_SECONDARY, alpha=0.15, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.plot(t, y, color=SERIES, linewidth=2, solid_capstyle="round", zorder=3)

    if pad:
        ax.axvspan((len(y) - pad) / FS_HZ, t[-1], color=TEXT_SECONDARY, alpha=0.08, zorder=2)
        ax.text((len(y) - pad / 2) / FS_HZ, ax.get_ylim()[1], "relleno de ceros",
                ha="center", va="top", fontsize=8, color=TEXT_SECONDARY)

    ax.set_title(f"Movimiento {MOVEMENT} · repetición {REPETITION} · sensor {SENSOR}, canal {name}",
                 color=TEXT_PRIMARY, fontsize=12, loc="left", pad=12)
    ax.set_xlabel("tiempo (s)", color=TEXT_SECONDARY, fontsize=10)
    ax.set_ylabel(f"{name} (grados)", color=TEXT_SECONDARY, fontsize=10)
    ax.set_xlim(0, t[-1])
    ax.tick_params(colors=TEXT_SECONDARY, labelsize=9)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(TEXT_SECONDARY)
        ax.spines[side].set_alpha(0.4)

    fig.tight_layout()
    save_figure(fig, f"step08_{MOVEMENT}_s{SENSOR}_rep{REPETITION}_{name}.png")


if __name__ == "__main__":
    main()
