"""Regresión lineal multisalida ajustada por descenso de gradiente (sección 4).

Modelo: `Ŷ = X̃ W`, donde `X̃` son las características estandarizadas (z-score con la
media y la desviación **del conjunto de entrenamiento**) más una columna de unos, y
`Y` es la codificación one-hot del rótulo. La clase predicha es `argmax` de las 16
salidas.

Pérdida y gradiente (sin regularizar el sesgo):

    J(W) = (1/2n) ‖X̃W − Y‖²_F + (λ/2n) ‖W_sin_sesgo‖²_F
    ∇J   = (1/n) X̃ᵀ(X̃W − Y) + (λ/n) W_sin_sesgo
    W   ← W − α ∇J

Como el gradiente es lineal en `W`, `X̃ᵀX̃/n` y `X̃ᵀY/n` se calculan una sola vez y cada
época cuesta un producto `(p×p)·(p×16)`; es exactamente el mismo gradiente completo
(batch), sólo que sin repetir el producto con `X̃`.

La tasa de aprendizaje por defecto es `α = 1 / λ_max`, con `λ_max` el mayor valor propio
de `X̃ᵀX̃/n + (λ/n)I` estimado por **iteración de potencia** escrita a mano; así el
descenso converge sin ajustar a ojo (con α = 0.05 diverge en la 2.ª época).
"""

import json
from pathlib import Path

import numpy as np

from .common import MODEL_FILE, N_CLASSES
from .metrics import one_hot

DEFAULT_LAMBDA = 1.0
DEFAULT_EPOCHS = 3000
LOG_EVERY = 50


def power_iteration(matrix: np.ndarray, iterations: int = 100, seed: int = 0) -> float:
    """Mayor valor propio de una matriz simétrica semidefinida positiva.

    `v ← M v / ‖M v‖` repetido `iterations` veces; el cociente de Rayleigh `vᵀMv`
    converge al mayor valor propio.
    """
    rng = np.random.default_rng(seed)
    v = rng.standard_normal(matrix.shape[0])
    v = v / np.sqrt(np.sum(v ** 2))
    for _ in range(iterations):
        mv = matrix @ v
        norm = np.sqrt(np.sum(mv ** 2))
        if norm == 0:
            return 0.0
        v = mv / norm
    return float(v @ (matrix @ v))


class LinearRegression:
    """Regresión lineal multisalida con L2, entrenada por descenso de gradiente."""

    def __init__(self, lam: float = DEFAULT_LAMBDA, alpha: float | None = None,
                 epochs: int = DEFAULT_EPOCHS, feature_names: list[str] | None = None):
        self.lam = float(lam)
        self.alpha = alpha
        self.epochs = int(epochs)
        self.feature_names = list(feature_names) if feature_names is not None else None
        self.mu: np.ndarray | None = None
        self.sigma: np.ndarray | None = None
        self.W: np.ndarray | None = None
        self.history: dict[str, list] = {"epoch": [], "train": [], "val": []}

    # --- Preparación de datos ---------------------------------------------------
    def _design(self, X: np.ndarray) -> np.ndarray:
        """Estandariza con `mu`/`sigma` del entrenamiento y añade la columna de unos."""
        Z = (np.asarray(X, dtype=float) - self.mu) / self.sigma
        return np.concatenate([np.ones((Z.shape[0], 1)), Z], axis=1)

    def _fit_scaler(self, X: np.ndarray) -> None:
        n = X.shape[0]
        self.mu = np.sum(X, axis=0) / n
        var = np.sum((X - self.mu) ** 2, axis=0) / n
        sigma = np.sqrt(var)
        self.sigma = np.where(sigma > 0, sigma, 1.0)  # columnas constantes → no dividir por 0

    # --- Pérdida --------------------------------------------------------------
    def loss(self, X: np.ndarray, y, W: np.ndarray | None = None) -> float:
        """J(W) sobre un conjunto (con `y` como rótulos enteros o ya en one-hot)."""
        W = self.W if W is None else W
        Xd = self._design(X)
        Y = one_hot(y) if np.ndim(y) == 1 else np.asarray(y, dtype=float)
        n = Xd.shape[0]
        residual = Xd @ W - Y
        reg = self.lam * np.sum(W[1:] ** 2)
        return float((np.sum(residual ** 2) + reg) / (2 * n))

    # --- Entrenamiento ----------------------------------------------------------
    def fit(self, X: np.ndarray, y: np.ndarray, X_val: np.ndarray | None = None,
            y_val: np.ndarray | None = None, log_every: int = LOG_EVERY,
            verbose: bool = False) -> "LinearRegression":
        """Descenso de gradiente completo desde `W = 0`; registra `J` cada `log_every`."""
        X = np.asarray(X, dtype=float)
        self._fit_scaler(X)
        Xd = self._design(X)
        Y = one_hot(y)
        n, p = Xd.shape

        gram = Xd.T @ Xd / n                     # (p, p)
        cross = Xd.T @ Y / n                     # (p, 16)
        reg_mask = np.ones((p, 1))
        reg_mask[0, 0] = 0.0                     # no se regulariza el sesgo
        hessian = gram + (self.lam / n) * np.diag(reg_mask[:, 0])

        if self.alpha is None:
            self.alpha = 1.0 / power_iteration(hessian)

        W = np.zeros((p, N_CLASSES))
        self.history = {"epoch": [], "train": [], "val": []}
        for epoch in range(1, self.epochs + 1):
            grad = gram @ W - cross + (self.lam / n) * (reg_mask * W)
            W = W - self.alpha * grad
            if epoch % log_every == 0 or epoch == 1 or epoch == self.epochs:
                self.history["epoch"].append(epoch)
                self.history["train"].append(self.loss(X, Y, W))
                if X_val is not None:
                    self.history["val"].append(self.loss(X_val, y_val, W))
                if verbose and epoch % (log_every * 10) == 0:
                    val_txt = f"  J_val = {self.history['val'][-1]:.5f}" if X_val is not None else ""
                    print(f"  época {epoch:5d}  J_train = {self.history['train'][-1]:.5f}{val_txt}")
        self.W = W
        return self

    # --- Predicción -------------------------------------------------------------
    def decision_function(self, X: np.ndarray) -> np.ndarray:
        """Salidas continuas `Ŷ = X̃W`, forma `(n, 16)`."""
        return self._design(X) @ self.W

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Clase predicha: `argmax` de las 16 salidas."""
        return np.argmax(self.decision_function(X), axis=1)

    # --- Persistencia -----------------------------------------------------------
    def save(self, path: Path = MODEL_FILE) -> Path:
        """Guarda pesos, estandarización, nombres de columnas e hiperparámetros."""
        path.parent.mkdir(parents=True, exist_ok=True)
        np.savez(
            path,
            W=self.W, mu=self.mu, sigma=self.sigma,
            feature_names=np.array(self.feature_names or [], dtype=str),
            hyper=json.dumps({"lambda": self.lam, "alpha": self.alpha, "epochs": self.epochs}),
            history=json.dumps(self.history),
        )
        return path

    @classmethod
    def load(cls, path: Path = MODEL_FILE) -> "LinearRegression":
        """Reconstruye el modelo desde `linreg.npz`."""
        data = np.load(path, allow_pickle=False)
        hyper = json.loads(str(data["hyper"]))
        model = cls(lam=hyper["lambda"], alpha=hyper["alpha"], epochs=hyper["epochs"],
                    feature_names=[str(s) for s in data["feature_names"]])
        model.W = data["W"]
        model.mu = data["mu"]
        model.sigma = data["sigma"]
        model.history = json.loads(str(data["history"]))
        return model
