# Linear_Regression · Redefinición de los datos + regresión lineal sin framework

Entrega del *Momento de retroalimentación: redefinición de los datos*

A partir de las señales crudas del dataset REHAB (`Data/*.npy`, 16 ejercicios de
rehabilitación vistos por dos IMU del miembro y un guante) se construye un **nuevo dataset
tabular** con una fila por repetición y estadísticos descriptivos por ventana temporal
calculados a mano, y sobre él se entrena una **regresión lineal multisalida** escrita desde
cero en NumPy que predice cuál
de los 16 ejercicios es una repetición.

Todo corre desde esta carpeta con `uv`: `make` regenera dataset → entrenamiento;
`make predict FILE=../Data/007_1.npy REP=5` predice una repetición y `make predict-all`
evalúa las repeticiones de test de los 16 movimientos (`make help` lista los atajos).

## Estructura del proyecto

```
Linear_Regression/
├── Makefile                  # dataset, train, predict, predict-all, clean, help
├── pyproject.toml            # numpy + matplotlib
├── dataset/
│   ├── rehab_windows.csv     # 4,532 filas × 846 columnas (24 MB)
│   ├── DICCIONARIO.md        # diccionario de datos generado
│   └── meta.json             # parámetros, descartes, conteos y partición por repetición
├── models/linreg.npz         # W (843×16), mu, sigma, nombres de columnas, hiperparámetros
├── results/                  # metrics.md, curva_aprendizaje.png, matriz_confusion.png
└── src/linear_regression/
    ├── common.py             # rutas, constantes, nombres, carga y longitud útil
    ├── stats.py              # 14 estadísticos a mano
    ├── features.py           # ventanas + vector de 842 características (único punto de verdad)
    ├── split.py              # partición estratificada reproducible
    ├── data.py               # lectura del CSV sin pandas
    ├── metrics.py            # exactitud, F1, confusión, MSE, R² a mano
    ├── model.py              # LinearRegression: fit (GD + iteración de potencia), predict, save/load
    ├── build_dataset.py      # CLI: Data/*.npy → dataset/
    ├── train.py              # CLI: barrido de λ, evaluación, figuras, métricas
    └── predict.py            # CLI: repetición cruda → actividad
```

`Data/` (372 MB) está en `.gitignore`; se descarga del DOI del artículo
(10.1038/s41597-026-07802-2). El CSV derivado sí se sube: es el entregable.

## El nuevo dataset: `dataset/rehab_windows.csv`

### Qué cambió respecto a los datos originales

El dataset original es una serie de tiempo: cada repetición es un bloque `(880 pasos, 6
canales)` en `<mov>_1.npy` (dos IMU del miembro) y otro `(880, 6)` en `<mov>_2.npy`
(guante), que son **el mismo intento** visto por sensores distintos, con relleno de ceros
al final cuando la repetición dura menos de 880 pasos.

El nuevo dataset colapsa cada repetición a **una sola fila tabular** de características
numéricas de tamaño fijo, apta para un modelo lineal. Para cada repetición:

1. Se recorta el **relleno de ceros** final de cada flujo (58 % de las repeticiones lo
   tienen). La longitud útil `L` se calcula **por sensor**, porque los dos flujos se
   segmentaron por separado.
2. La señal útil se corta en **4 ventanas de igual longitud** (`w1`…`w4`, bordes
   `round(k·L/4)`) y se conserva además la señal completa (`w0`). Ninguna ventana contiene
   relleno.
3. En cada ventana y cada canal se calculan **14 estadísticos** a mano
   ([`stats.py`](src/linear_regression/stats.py)).
4. Se concatenan: 2 sensores × 6 canales × 5 ventanas × 14 estadísticos = **840**
   características, más las dos longitudes útiles = **842 columnas numéricas**.

Se descartan **84 de 4,616** repeticiones (1.8 %): 74 totalmente en cero en alguno de los
dos sensores y 10 con menos de 40 pasos útiles (0.8 s). Quedan **4,532 filas**. La lista
exacta de descartes y la partición de cada repetición están en `dataset/meta.json`.

### Columnas (846 en total)

| Columna | Descripción |
|---|---|
| `movement` | **Rótulo**, 0–15 (Tabla 3 del artículo) |
| `movement_name` | Nombre del ejercicio, sólo para lectura |
| `rep_index` | Índice de la repetición en el `.npy` original (permite volver a la señal cruda) |
| `split` | `train` / `val` / `test` (70 / 15 / 15, estratificado por movimiento, semilla 7) |
| `valid_len_s1`, `valid_len_s2` | Pasos útiles de cada flujo (50 pasos = 1 s) |
| `s<sensor>_<canal>_w<k>_<estadístico>` | 840 características, p. ej. `s1_pitch1_w2_median` |

| Sensor | Canales | Qué es |
|---|---|---|
| `s1` | `pitch1`, `yaw1`, `roll1`, `pitch2`, `yaw2`, `roll2` | Ángulos de Euler (°) de las dos IMU del miembro: antebrazo/brazo en `000`–`012`, pantorrilla/muslo en `013`–`015` |
| `s2` | `f1`…`f5`, `pitch3` | Guante: flexión (°) de cada dedo y pitch de la muñeca |

| Estadístico | Definición |
|---|---|
| `mean`, `median`, `mode` | media; mediana (promedio de los centrales si `n` par); centro del bin más poblado de un histograma de 20 bins |
| `std`, `var`, `cv` | desviación y varianza poblacionales; `std / máx(|mean|, 1)` |
| `min`, `max`, `range` | extremos y amplitud del recorrido articular |
| `q1`, `q3`, `iqr` | `s[⌊n/4⌋]`, `s[⌊3n/4⌋]` del vector ordenado, y su diferencia |
| `mad_diff` | `Σ|xᵢ₊₁ − xᵢ| / (n − 1)`: velocidad angular media, el único descriptor dinámico |
| `rms` | raíz cuadrática media |

Ejemplo: `s1_pitch1_w2_median` es la mediana del pitch de la IMU 1 en el segundo cuarto de
la repetición; `s2_f3_w0_iqr` es el rango intercuartílico de la flexión del dedo medio en
toda la repetición. Los valores están redondeados a 4 decimales.

El diccionario completo generado está en [`dataset/DICCIONARIO.md`](dataset/DICCIONARIO.md).
Se regenera con `make dataset` (≈ 10 s) a partir de `Data/*.npy`.
