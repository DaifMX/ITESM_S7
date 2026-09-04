# Diccionario de datos · `rehab_windows.csv`

Generado por `python -m linear_regression.build_dataset`. Una fila por repetición de un ejercicio del dataset REHAB (`Rehab_exercise`), vista por los dos grupos de sensores (`_1` IMU del miembro, `_2` guante).

## Columnas de identificación

| Columna | Tipo | Descripción |
|---|---|---|
| `movement` | int 0–15 | **Rótulo.** Actividad según la Tabla 3 del artículo |
| `movement_name` | str | Nombre del ejercicio, sólo para lectura humana |
| `rep_index` | int | Índice de la repetición dentro del `.npy` original (permite volver a la señal cruda) |
| `split` | str | `train` / `val` / `test`, partición estratificada fija (semilla en `meta.json`) |

## Columnas de características (842)

| Columna | Tipo | Descripción |
|---|---|---|
| `valid_len_s1` | int | Pasos útiles del flujo `_1` (880 − relleno de ceros); 50 pasos = 1 s |
| `valid_len_s2` | int | Pasos útiles del flujo `_2` |
| `s<sensor>_<canal>_w<k>_<estadístico>` | float | 12 canales × 5 ventanas × 14 estadísticos = 840 columnas (ver abajo) |

### `<sensor>` y `<canal>`

| Sensor | Canales | Qué es |
|---|---|---|
| `s1` | `pitch1`, `yaw1`, `roll1`, `pitch2`, `yaw2`, `roll2` | Ángulos de Euler (°) de las dos IMU del miembro que se ejercita: antebrazo/brazo en `000`–`012`, pantorrilla/muslo en `013`–`015` |
| `s2` | `f1`, `f2`, `f3`, `f4`, `f5`, `pitch3` | Guante: flexión (°) de cada dedo y pitch de la muñeca |

### `<k>`: ventana

| Ventana | Tramo |
|---|---|
| `w0` | Toda la señal útil `x[0:L]` (`L` = `valid_len_s*` del sensor correspondiente) |
| `w1` | Tramo 1 de 4: `x[round((1-1)·L/4) : round(1·L/4)]` |
| `w2` | Tramo 2 de 4: `x[round((2-1)·L/4) : round(2·L/4)]` |
| `w3` | Tramo 3 de 4: `x[round((3-1)·L/4) : round(3·L/4)]` |
| `w4` | Tramo 4 de 4: `x[round((4-1)·L/4) : round(4·L/4)]` |

Las ventanas se cortan sobre la longitud útil de **cada sensor por separado** (no sobre los 880 pasos), de modo que ninguna ventana contiene relleno de ceros.

### `<estadístico>` (los 14, escritos a mano en `stats.py`)

| Nombre | Definición |
|---|---|
| `mean` | media aritmética Σxᵢ / n |
| `median` | mediana: x₍n/2₎, o promedio de los dos valores centrales si n es par |
| `mode` | moda: centro del bin más poblado de un histograma de 20 bins entre mín y máx (empates → bin más bajo) |
| `std` | desviación estándar poblacional √(Σ(xᵢ − mean)² / n) |
| `var` | varianza poblacional (std²) |
| `cv` | coeficiente de variación std / máx(|mean|, 1.0); el denominador se acota a 1° para que no explote con media ≈ 0 |
| `min` | mínimo x₍₁₎ |
| `max` | máximo x₍ₙ₎ |
| `range` | recorrido max − min (amplitud articular) |
| `q1` | primer cuartil x₍⌊n/4⌋₎ (índice inferior, sin interpolación) |
| `q3` | tercer cuartil x₍⌊3n/4⌋₎ (índice inferior, sin interpolación) |
| `iqr` | rango intercuartílico q3 − q1 |
| `mad_diff` | diferencia absoluta media entre pasos consecutivos Σ|xᵢ₊₁ − xᵢ| / (n − 1): velocidad angular media (°/paso) |
| `rms` | raíz cuadrática media √(Σxᵢ² / n) |

Ejemplo: `s1_pitch1_w2_median` es la mediana del pitch de la IMU 1 en el segundo cuarto de la repetición; `s2_f3_w0_iqr` es el rango intercuartílico de la flexión del dedo medio en toda la repetición. Los valores están redondeados a 4 decimales. La moda usa 20 bins.
