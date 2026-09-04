"""Los 14 estadísticos por ventana, escritos a mano.

Regla de oro (sección 1 de la especificación): NumPy se usa sólo como contenedor de
arreglos y para operaciones elementales (`sum`, `sort`, `abs`, `sqrt`, `diff`,
`argmax`, comparaciones). No se usa `np.median`, `np.percentile`, `np.var`, `np.std`,
`np.histogram` ni nada que calcule el estadístico por nosotros.

Todas las funciones aceptan un vector `(n,)` o una matriz `(n, c)` (una columna por
canal) y operan a lo largo del eje 0; con un vector devuelven un escalar y con una
matriz un vector `(c,)`. Notación de las docstrings: `x` es la ventana, `n` su
longitud, `x₍ᵢ₎` el i-ésimo valor ordenado (empezando en 1).
"""

import numpy as np

from .common import MODE_BINS

STAT_NAMES = [
    "mean", "median", "mode", "std", "var", "cv",
    "min", "max", "range", "q1", "q3", "iqr", "mad_diff", "rms",
]

STAT_DESCRIPTIONS = {
    "mean": "media aritmética Σxᵢ / n",
    "median": "mediana: x₍n/2₎, o promedio de los dos valores centrales si n es par",
    "mode": f"moda: centro del bin más poblado de un histograma de {MODE_BINS} bins entre mín y máx (empates → bin más bajo)",
    "std": "desviación estándar poblacional √(Σ(xᵢ − mean)² / n)",
    "var": "varianza poblacional (std²)",
    "cv": "coeficiente de variación std / máx(|mean|, 1.0); el denominador se acota a 1° para que no explote con media ≈ 0",
    "min": "mínimo x₍₁₎",
    "max": "máximo x₍ₙ₎",
    "range": "recorrido max − min (amplitud articular)",
    "q1": "primer cuartil x₍⌊n/4⌋₎ (índice inferior, sin interpolación)",
    "q3": "tercer cuartil x₍⌊3n/4⌋₎ (índice inferior, sin interpolación)",
    "iqr": "rango intercuartílico q3 − q1",
    "mad_diff": "diferencia absoluta media entre pasos consecutivos Σ|xᵢ₊₁ − xᵢ| / (n − 1): velocidad angular media (°/paso)",
    "rms": "raíz cuadrática media √(Σxᵢ² / n)",
}


def _as_matrix(x) -> tuple[np.ndarray, bool]:
    """Convierte la entrada a `(n, c)` float y recuerda si era un vector."""
    x = np.asarray(x, dtype=float)
    if x.ndim == 1:
        return x[:, None], True
    if x.ndim != 2:
        raise ValueError("se esperaba un vector (n,) o una matriz (n, c)")
    return x, False


def _out(values: np.ndarray, was_vector: bool):
    return float(values[0]) if was_vector else values


def mean(x):
    """Σxᵢ / n."""
    m, v = _as_matrix(x)
    return _out(np.sum(m, axis=0) / m.shape[0], v)


def median(x):
    """x₍n/2₎ si n es impar; promedio de los dos centrales si n es par."""
    m, v = _as_matrix(x)
    s = np.sort(m, axis=0)
    n = s.shape[0]
    if n % 2 == 1:
        med = s[n // 2]
    else:
        med = (s[n // 2 - 1] + s[n // 2]) / 2.0
    return _out(med, v)


def mode(x, bins: int = MODE_BINS):
    """Centro del bin más poblado de un histograma de `bins` bins entre mín y máx.

    Una señal continua no tiene moda "exacta" (casi ningún valor se repite), así que se
    discretiza. Los conteos se obtienen comparando el índice de bin de cada muestra con
    cada bin y sumando (sin `np.histogram` ni `np.bincount`). En empate gana el bin más
    bajo (`argmax` devuelve la primera ocurrencia). Si la ventana es constante, la moda
    es ese valor.
    """
    m, v = _as_matrix(x)
    lo = minimum(m)
    hi = maximum(m)
    width = (hi - lo) / bins
    safe_width = np.where(width > 0, width, 1.0)
    idx = np.floor((m - lo) / safe_width).astype(int)
    idx = np.where(idx >= bins, bins - 1, idx)          # el máximo cae en el último bin
    counts = np.sum(idx[:, :, None] == np.arange(bins)[None, None, :], axis=0)  # (c, bins)
    best = np.argmax(counts, axis=1)
    centre = lo + (best + 0.5) * width
    centre = np.where(width > 0, centre, lo)
    return _out(centre, v)


def variance(x):
    """Σ(xᵢ − mean)² / n (poblacional, ddof = 0)."""
    m, v = _as_matrix(x)
    mu = np.sum(m, axis=0) / m.shape[0]
    return _out(np.sum((m - mu) ** 2, axis=0) / m.shape[0], v)


def std(x):
    """√varianza."""
    m, v = _as_matrix(x)
    return _out(np.sqrt(variance(m)), v)


def cv(x):
    """std / máx(|mean|, 1.0). El denominador se acota para ventanas con media ≈ 0."""
    m, v = _as_matrix(x)
    mu = mean(m)
    denom = np.where(np.abs(mu) > 1.0, np.abs(mu), 1.0)
    return _out(std(m) / denom, v)


def minimum(x):
    """x₍₁₎, calculado con el vector ordenado."""
    m, v = _as_matrix(x)
    return _out(np.sort(m, axis=0)[0], v)


def maximum(x):
    """x₍ₙ₎, calculado con el vector ordenado."""
    m, v = _as_matrix(x)
    return _out(np.sort(m, axis=0)[-1], v)


def value_range(x):
    """max − min."""
    m, v = _as_matrix(x)
    return _out(maximum(m) - minimum(m), v)


def quartile(x, which: int):
    """Cuartil `which` ∈ {1, 3}: `s[⌊which·n/4⌋]` del vector ordenado `s` (índice base 0).

    Método "índice inferior", sin interpolación: para `[1, 2, 2, 3, 10]` da q1 = 2 y
    q3 = 3. El índice se acota a `n − 1` por seguridad.
    """
    if which not in (1, 3):
        raise ValueError("which debe ser 1 o 3")
    m, v = _as_matrix(x)
    s = np.sort(m, axis=0)
    return _out(s[_quartile_index(s.shape[0], which)], v)


def _quartile_index(n: int, which: int) -> int:
    return min((which * n) // 4, n - 1)


def q1(x):
    """Primer cuartil."""
    return quartile(x, 1)


def q3(x):
    """Tercer cuartil."""
    return quartile(x, 3)


def iqr(x):
    """q3 − q1."""
    m, v = _as_matrix(x)
    return _out(quartile(m, 3) - quartile(m, 1), v)


def mad_diff(x):
    """Σ|xᵢ₊₁ − xᵢ| / (n − 1): velocidad media del cambio entre pasos (0 si n = 1)."""
    m, v = _as_matrix(x)
    n = m.shape[0]
    if n < 2:
        return _out(np.zeros(m.shape[1]), v)
    return _out(np.sum(np.abs(np.diff(m, axis=0)), axis=0) / (n - 1), v)


def rms(x):
    """√(Σxᵢ² / n)."""
    m, v = _as_matrix(x)
    return _out(np.sqrt(np.sum(m ** 2, axis=0) / m.shape[0]), v)


def describe(x) -> np.ndarray:
    """Los 14 estadísticos de `STAT_NAMES`, en ese orden, para cada columna.

    Devuelve una matriz `(14, c)` (o un vector `(14,)` si la entrada era un vector).
    Calcula una sola vez lo que comparten varios estadísticos (ordenamiento, media).
    """
    m, v = _as_matrix(x)
    n = m.shape[0]
    s = np.sort(m, axis=0)
    mu = np.sum(m, axis=0) / n
    var = np.sum((m - mu) ** 2, axis=0) / n
    sd = np.sqrt(var)
    lo, hi = s[0], s[-1]
    med = s[n // 2] if n % 2 == 1 else (s[n // 2 - 1] + s[n // 2]) / 2.0
    first = s[_quartile_index(n, 1)]
    third = s[_quartile_index(n, 3)]
    denom = np.where(np.abs(mu) > 1.0, np.abs(mu), 1.0)
    rows = np.stack([
        mu,
        med,
        mode(m),
        sd,
        var,
        sd / denom,
        lo,
        hi,
        hi - lo,
        first,
        third,
        third - first,
        mad_diff(m),
        np.sqrt(np.sum(m ** 2, axis=0) / n),
    ])
    return rows[:, 0] if v else rows
