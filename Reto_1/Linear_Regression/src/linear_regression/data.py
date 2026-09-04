"""Lectura del CSV generado, sin pandas.

Devuelve las características como matriz `float64`, el rótulo, el índice de repetición y
la partición de cada fila, más los nombres de las columnas de características.
"""

import csv
from pathlib import Path

import numpy as np

from .common import DATASET_CSV

ID_COLUMNS = ["movement", "movement_name", "rep_index", "split"]


def load_dataset(path: Path = DATASET_CSV) -> dict:
    """Lee `rehab_windows.csv` y separa identificación de características."""
    if not path.exists():
        raise FileNotFoundError(
            f"No existe {path}. Genera el dataset primero con "
            "`uv run python -m linear_regression.build_dataset`.")
    with open(path, encoding="utf-8", newline="") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        id_pos = [header.index(c) for c in ID_COLUMNS]
        feat_pos = [i for i in range(len(header)) if i not in id_pos]
        labels, reps, splits, rows = [], [], [], []
        for row in reader:
            labels.append(int(row[id_pos[0]]))
            reps.append(int(row[id_pos[2]]))
            splits.append(row[id_pos[3]])
            rows.append([row[i] for i in feat_pos])
    X = np.array(rows, dtype=float)
    return {
        "X": X,
        "y": np.array(labels),
        "rep": np.array(reps),
        "split": np.array(splits),
        "names": [header[i] for i in feat_pos],
    }


def subset(data: dict, split: str, columns: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray]:
    """`(X, y)` de una partición, opcionalmente restringido a una máscara de columnas."""
    mask = data["split"] == split
    X = data["X"][mask]
    if columns is not None:
        X = X[:, columns]
    return X, data["y"][mask]
