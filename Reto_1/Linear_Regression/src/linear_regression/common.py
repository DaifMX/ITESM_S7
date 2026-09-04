"""Rutas, constantes del dataset y funciones de carga compartidas.

Misma convención que `Dataset_Analysis/src/dataset_analysis/common.py`: `Data/` vive
junto a `Linear_Regression/`, no dentro. Las repeticiones están rellenadas con ceros al
final hasta 880 pasos (paso 4 del EDA); ese relleno **no es señal** y se descarta con
`valid_length` antes de calcular cualquier estadístico.
"""

from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT.parent / "Data"
DATASET_DIR = ROOT / "dataset"
MODELS_DIR = ROOT / "models"
RESULTS_DIR = ROOT / "results"

DATASET_CSV = DATASET_DIR / "rehab_windows.csv"
DATASET_DICT = DATASET_DIR / "DICCIONARIO.md"
DATASET_META = DATASET_DIR / "meta.json"
MODEL_FILE = MODELS_DIR / "linreg.npz"

# --- Dataset ---------------------------------------------------------------------
FS_HZ = 50
N_STEPS = 880
MOVEMENTS = [f"{i:03d}" for i in range(16)]
N_CLASSES = len(MOVEMENTS)

# Tabla 3 del artículo REHAB (ver docs/README.md).
MOVEMENT_NAMES = {
    0: "bobath handshake",
    1: "bobath flexion/extension",
    2: "bobath forward flexion/extension",
    3: "bobath anterior/posterior rotation",
    4: "elbow flexion and wrist compression",
    5: "wrist flexion and extension",
    6: "finger-to-finger training",
    7: "ball gripping",
    8: "shoulder joint internal and external",
    9: "breast expansion",
    10: "flexion-pressure rotation forward and backward",
    11: "elbow joint flexion and touch",
    12: "shoulder touch training",
    13: "ankle extension & knee internal/external rotation",
    14: "knee flexion and extension",
    15: "hip flexion and extension",
}

CHANNELS_S1 = ["pitch1", "yaw1", "roll1", "pitch2", "yaw2", "roll2"]
CHANNELS_S2 = ["f1", "f2", "f3", "f4", "f5", "pitch3"]
SENSORS = ("1", "2")

# --- Parámetros de construcción del dataset (sección 2 y 3 de la especificación) ---
N_WINDOWS = 4          # ventanas de igual longitud sobre la señal útil (más la completa, w0)
MIN_VALID_LEN = 40     # pasos útiles mínimos (0.8 s) en cada sensor para conservar la repetición
MODE_BINS = 20         # bins del histograma con el que se estima la moda de una señal continua
SEED = 7
SPLIT_FRACTIONS = {"train": 0.70, "val": 0.15, "test": 0.15}

# --- Tokens de estilo para figuras (misma paleta que Dataset_Analysis) --------------
SERIES_1 = "#2a78d6"
SERIES_2 = "#eb6834"
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
SURFACE = "#fcfcfb"


def channel_names(sensor: str) -> list[str]:
    """Nombres de los seis canales según el sensor ('1' o '2')."""
    return CHANNELS_S1 if str(sensor) == "1" else CHANNELS_S2


def trailing_zero_steps(sample: np.ndarray) -> int:
    """Pasos finales con los 6 canales exactamente en 0 (relleno). Misma regla que el EDA."""
    silent = np.all(sample == 0, axis=1)
    n = 0
    while n < len(silent) and silent[-1 - n]:
        n += 1
    return n


def valid_length(sample: np.ndarray) -> int:
    """Longitud útil de una repetición `(880, 6)`: pasos totales menos el relleno final."""
    return len(sample) - trailing_zero_steps(sample)


def load_movement(movement: str | int, sensor: str = "1") -> np.ndarray:
    """Carga `<movement>_<sensor>.npy` con forma `(repeticiones, 880, 6)`."""
    movement = f"{int(movement):03d}"
    return np.load(DATA_DIR / f"{movement}_{sensor}.npy")


def load_pair(movement: str | int) -> tuple[np.ndarray, np.ndarray]:
    """Carga los dos flujos (`_1` IMU del miembro, `_2` guante) de un movimiento."""
    return load_movement(movement, "1"), load_movement(movement, "2")


def partner_file(path: Path) -> tuple[Path, Path]:
    """Dado `<mov>_1.npy` o `<mov>_2.npy` devuelve la pareja `(ruta_1, ruta_2)`."""
    stem = path.stem
    if not (len(stem) == 5 and stem[3] == "_" and stem[4] in SENSORS):
        raise ValueError(f"Nombre inesperado '{path.name}'; se esperaba '<mov>_1.npy' o '<mov>_2.npy'")
    base = stem[:3]
    return path.with_name(f"{base}_1.npy"), path.with_name(f"{base}_2.npy")


def movement_from_filename(path: Path) -> int | None:
    """Rótulo codificado en el nombre (`007_1.npy` → 7) o `None` si no es numérico."""
    prefix = path.stem[:3]
    return int(prefix) if prefix.isdigit() and int(prefix) < N_CLASSES else None


def style_axes(ax, title: str, xlabel: str, ylabel: str) -> None:
    """Estilo común de las figuras: rejilla discreta, sin marco superior/derecho."""
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
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(*args, **kwargs)
    fig.patch.set_facecolor(SURFACE)
    for ax in np.atleast_1d(np.asarray(axes)).ravel():
        ax.set_facecolor(SURFACE)
    return fig, axes


def save_figure(fig, name: str) -> Path:
    """Guarda la figura en `results/` y devuelve la ruta."""
    RESULTS_DIR.mkdir(exist_ok=True)
    out = RESULTS_DIR / name
    fig.savefig(out, facecolor=SURFACE, dpi=150, bbox_inches="tight")
    print(f"Figura guardada en: {out.relative_to(ROOT)}")
    return out
