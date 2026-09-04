"""De una repetición cruda a una fila del dataset.

Este módulo es el **único** lugar que sabe cómo convertir una repetición (`(880, 6)` del
flujo `_1` más `(880, 6)` del flujo `_2`) en el vector de 842 características. Lo usan
tanto `build_dataset` (todas las repeticiones) como `predict` (una sola), de modo que la
predicción nunca puede calcular algo distinto de lo que vio el entrenamiento.

Orden del vector (`feature_names()`):

1. `valid_len_s1`, `valid_len_s2`
2. `s<sensor>_<canal>_w<k>_<estadístico>` anidado en ese orden: sensor (1, 2) → canal
   (6) → ventana (w0 = señal útil completa, w1…wN = tramos consecutivos) → estadístico
   (los 14 de `stats.STAT_NAMES`).
"""

import numpy as np

from .common import N_WINDOWS, SENSORS, channel_names, valid_length
from .stats import STAT_NAMES, describe


def window_bounds(length: int, n_windows: int = N_WINDOWS) -> list[tuple[int, int]]:
    """Bordes `[e_{k-1}, e_k)` de `n_windows` tramos iguales sobre `length` pasos.

    `e_k = round(k · length / n_windows)`, así que las ventanas difieren a lo sumo en
    un paso y cubren exactamente `[0, length)`.
    """
    edges = [round(k * length / n_windows) for k in range(n_windows + 1)]
    return [(edges[k - 1], edges[k]) for k in range(1, n_windows + 1)]


def sensor_windows(sample: np.ndarray, n_windows: int = N_WINDOWS) -> list[np.ndarray]:
    """Lista `[w0, w1, …, wN]` de recortes `(nᵢ, 6)` de una repetición sin relleno."""
    length = valid_length(sample)
    useful = sample[:length]
    return [useful] + [useful[a:b] for a, b in window_bounds(length, n_windows)]


def sensor_features(sample: np.ndarray, n_windows: int = N_WINDOWS) -> np.ndarray:
    """Estadísticos de un flujo: arreglo `(6 canales, n_windows + 1, 14)`."""
    per_window = [describe(w) for w in sensor_windows(sample, n_windows)]  # cada uno (14, 6)
    stacked = np.stack(per_window)                                           # (W, 14, 6)
    return np.transpose(stacked, (2, 0, 1))                                  # (6, W, 14)


def repetition_features(rep_s1: np.ndarray, rep_s2: np.ndarray,
                        n_windows: int = N_WINDOWS) -> np.ndarray:
    """Vector de características de una repetición vista por ambos sensores."""
    lengths = [float(valid_length(rep_s1)), float(valid_length(rep_s2))]
    blocks = [sensor_features(rep_s1, n_windows).ravel(),
              sensor_features(rep_s2, n_windows).ravel()]
    return np.concatenate([np.array(lengths)] + blocks)


def feature_names(n_windows: int = N_WINDOWS) -> list[str]:
    """Nombres de las columnas en el mismo orden que `repetition_features`."""
    names = ["valid_len_s1", "valid_len_s2"]
    for sensor in SENSORS:
        for channel in channel_names(sensor):
            for k in range(n_windows + 1):
                for stat in STAT_NAMES:
                    names.append(f"s{sensor}_{channel}_w{k}_{stat}")
    return names


def sensor1_mask(names: list[str]) -> np.ndarray:
    """Máscara booleana de las columnas que dependen sólo del flujo `_1` (ablación)."""
    return np.array([n == "valid_len_s1" or n.startswith("s1_") for n in names])
