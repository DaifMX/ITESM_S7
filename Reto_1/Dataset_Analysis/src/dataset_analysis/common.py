"""Utilidades compartidas por los pasos del reto.

Reúne las rutas, las constantes del dataset (paso 4), los tokens de estilo de
las figuras y las funciones de carga que usan los pasos 8 a 13.

Nota importante sobre el relleno de ceros: las repeticiones están estandarizadas
a 880 pasos rellenando con ceros al final (paso 4). Ese relleno **no es señal**,
así que `concat_channel` lo descarta antes de concatenar; de lo contrario las
medias y los histogramas se sesgarían artificialmente hacia 0.
"""

from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
# `Data/` vive junto a `Dataset_Analysis/`, no dentro.
DATA_DIR = ROOT.parent / "Data"
FIG_DIR = ROOT / "figures"

FS_HZ = 50
N_STEPS = 880
MOVEMENTS = [f"{i:03d}" for i in range(16)]

CHANNELS_S1 = ["Pitch1", "Yaw1", "Roll1", "Pitch2", "Yaw2", "Roll2"]
CHANNELS_S2 = ["f1", "f2", "f3", "f4", "f5", "pitch3"]

# Tokens de estilo (paleta categórica validada; slots 1 y 2).
SERIES_1 = "#2a78d6"
SERIES_2 = "#eb6834"
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
SURFACE = "#fcfcfb"


def channel_names(sensor: str) -> list[str]:
    """Nombres de los seis canales según el sensor ('1' o '2')."""
    return CHANNELS_S1 if str(sensor) == "1" else CHANNELS_S2


def trailing_zero_steps(sample: np.ndarray) -> int:
    """Pasos de tiempo rellenados con ceros al final de una repetición."""
    silent = np.all(sample == 0, axis=1)
    n = 0
    while n < len(silent) and silent[-1 - n]:
        n += 1
    return n


def load_movement(movement: str, sensor: str = "1") -> np.ndarray:
    """Carga `<movement>_<sensor>.npy` con forma (repeticiones, 880, 6)."""
    return np.load(DATA_DIR / f"{movement}_{sensor}.npy")


def concat_channel(movement: str, channel: int, sensor: str = "1",
                   drop_padding: bool = True) -> np.ndarray:
    """Concatena un canal a lo largo de todas las repeticiones de un movimiento.

    Con `drop_padding=True` (por defecto) se recorta el relleno de ceros final
    de cada repetición antes de concatenar.
    """
    array = load_movement(movement, sensor)
    if not drop_padding:
        return array[:, :, channel].ravel()
    pieces = [rep[: len(rep) - trailing_zero_steps(rep), channel] for rep in array]
    return np.concatenate(pieces)


def style_axes(ax, title: str, xlabel: str, ylabel: str) -> None:
    """Aplica el estilo común: rejilla discreta, sin marco superior/derecho."""
    ax.grid(axis="y", color=TEXT_SECONDARY, alpha=0.15, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.set_title(title, color=TEXT_PRIMARY, fontsize=12, loc="left", pad=12)
    ax.set_xlabel(xlabel, color=TEXT_SECONDARY, fontsize=10)
    ax.set_ylabel(ylabel, color=TEXT_SECONDARY, fontsize=10)
    ax.tick_params(colors=TEXT_SECONDARY, labelsize=9)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(TEXT_SECONDARY)
        ax.spines[side].set_alpha(0.4)


def new_figure(*args, **kwargs):
    """`plt.subplots` con la superficie del proyecto ya aplicada."""
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(*args, **kwargs)
    fig.patch.set_facecolor(SURFACE)
    for ax in np.atleast_1d(np.asarray(axes)).ravel():
        ax.set_facecolor(SURFACE)
    return fig, axes


def save_figure(fig, name: str) -> Path:
    """Guarda la figura en `figures/` y devuelve la ruta."""
    FIG_DIR.mkdir(exist_ok=True)
    out = FIG_DIR / name
    fig.savefig(out, facecolor=SURFACE)
    print(f"\nFigura guardada en: {out.relative_to(ROOT)}")
    return out
