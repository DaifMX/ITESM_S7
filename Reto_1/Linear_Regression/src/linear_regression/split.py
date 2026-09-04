"""Partición estratificada y reproducible train / val / test.

Se usa `np.random.default_rng(SEED)` sólo como fuente de aleatoriedad (permitido: no es
aprendizaje ni estadística). Dentro de cada clase se baraja y se reparte 70 / 15 / 15;
el resultado se materializa en la columna `split` del CSV para que nadie tenga que
volver a barajar.
"""

import numpy as np

from .common import SEED, SPLIT_FRACTIONS

SPLIT_NAMES = ("train", "val", "test")


def stratified_split(labels: np.ndarray, seed: int = SEED,
                     fractions: dict[str, float] = SPLIT_FRACTIONS) -> np.ndarray:
    """Devuelve un arreglo de cadenas `train`/`val`/`test` alineado con `labels`.

    Para cada clase: se permutan sus índices, los primeros `round(f_train · n)` van a
    train, los siguientes `round(f_val · n)` a val y el resto a test.
    """
    labels = np.asarray(labels)
    rng = np.random.default_rng(seed)
    out = np.empty(len(labels), dtype="<U5")
    for cls in np.unique(labels):
        idx = np.flatnonzero(labels == cls)
        idx = idx[rng.permutation(len(idx))]
        n = len(idx)
        n_train = round(fractions["train"] * n)
        n_val = round(fractions["val"] * n)
        out[idx[:n_train]] = "train"
        out[idx[n_train:n_train + n_val]] = "val"
        out[idx[n_train + n_val:]] = "test"
    return out
