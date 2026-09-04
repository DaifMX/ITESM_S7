"""Métricas de clasificación y de regresión, escritas a mano.

Las de clasificación (exactitud, matriz de confusión, recall y F1 por clase, macro-F1)
describen la utilidad real del clasificador; las de regresión (MSE y R² sobre la
codificación one-hot) son las que corresponden a la técnica usada.
"""

import numpy as np

from .common import N_CLASSES


def one_hot(labels: np.ndarray, n_classes: int = N_CLASSES) -> np.ndarray:
    """Matriz `(n, n_classes)` con un 1 en la columna del rótulo."""
    labels = np.asarray(labels, dtype=int)
    return (labels[:, None] == np.arange(n_classes)[None, :]).astype(float)


def accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Proporción de aciertos."""
    return float(np.sum(np.asarray(y_true) == np.asarray(y_pred)) / len(y_true))


def confusion_matrix(y_true: np.ndarray, y_pred: np.ndarray,
                     n_classes: int = N_CLASSES) -> np.ndarray:
    """`C[i, j]` = repeticiones de la clase real `i` predichas como `j`."""
    cm = np.zeros((n_classes, n_classes), dtype=int)
    for t, p in zip(np.asarray(y_true, dtype=int), np.asarray(y_pred, dtype=int)):
        cm[t, p] += 1
    return cm


def per_class_scores(cm: np.ndarray) -> dict[str, np.ndarray]:
    """Precisión, recall y F1 por clase a partir de la matriz de confusión."""
    tp = np.diag(cm).astype(float)
    fp = np.sum(cm, axis=0) - tp
    fn = np.sum(cm, axis=1) - tp
    precision = np.where(tp + fp > 0, tp / np.where(tp + fp > 0, tp + fp, 1), 0.0)
    recall = np.where(tp + fn > 0, tp / np.where(tp + fn > 0, tp + fn, 1), 0.0)
    denom = precision + recall
    f1 = np.where(denom > 0, 2 * precision * recall / np.where(denom > 0, denom, 1), 0.0)
    return {"precision": precision, "recall": recall, "f1": f1}


def macro_f1(y_true: np.ndarray, y_pred: np.ndarray, n_classes: int = N_CLASSES) -> float:
    """Promedio simple del F1 de cada clase (robusto al desbalance 1.82:1)."""
    return float(np.sum(per_class_scores(confusion_matrix(y_true, y_pred, n_classes))["f1"]) / n_classes)


def mse(y_true: np.ndarray, y_hat: np.ndarray) -> float:
    """Error cuadrático medio sobre todas las entradas de la matriz."""
    diff = np.asarray(y_true) - np.asarray(y_hat)
    return float(np.sum(diff ** 2) / diff.size)


def r2(y_true: np.ndarray, y_hat: np.ndarray) -> float:
    """R² = 1 − SS_res / SS_tot, con SS_tot alrededor de la media de cada columna."""
    y_true = np.asarray(y_true)
    y_hat = np.asarray(y_hat)
    ss_res = np.sum((y_true - y_hat) ** 2)
    col_mean = np.sum(y_true, axis=0) / y_true.shape[0]
    ss_tot = np.sum((y_true - col_mean) ** 2)
    return float(1.0 - ss_res / ss_tot)


def classification_report(y_true: np.ndarray, y_hat: np.ndarray) -> dict:
    """Todas las métricas de un conjunto a partir de la salida continua `y_hat`."""
    y_pred = np.argmax(y_hat, axis=1)
    y_true = np.asarray(y_true, dtype=int)
    cm = confusion_matrix(y_true, y_pred)
    scores = per_class_scores(cm)
    y_oh = one_hot(y_true)
    return {
        "accuracy": accuracy(y_true, y_pred),
        "macro_f1": float(np.sum(scores["f1"]) / N_CLASSES),
        "mse": mse(y_oh, y_hat),
        "r2": r2(y_oh, y_hat),
        "confusion": cm,
        "per_class": scores,
    }
