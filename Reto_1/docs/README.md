# Estructura de `Data/` (REHAB · `Rehab_exercise/d02_processed_data`)

Fuente: artículo REHAB, *Scientific Data* (2026), doi:10.1038/s41597-026-07802-2,
secciones "Rehab_exercise structure" y Tablas 3, 8, 9 y 10. Verificado contra los
archivos locales con `Dataset_Analysis/src/dataset_analysis/step04_verify_structure.py`.

## Por qué hay 32 archivos (16 + 16)

El nombre de cada archivo es `<movimiento>_<sensorID>.npy`:

| Parte del nombre | Valores | Qué es |
|---|---|---|
| `<movimiento>` | `000` … `015` | Uno de los **16 ejercicios de entrenamiento** (Tabla 3 del artículo) |
| `<sensorID>` | `1` o `2` | **Qué grupo de sensores** contiene el archivo (no es "sensor 1" y "sensor 2" físicos) |

16 movimientos × 2 grupos de sensores = **32 archivos**. Los "16 archivos" son las
16 actividades: `000_1.npy` … `015_1.npy` son las 16 actividades vistas por el grupo 1,
y `000_2.npy` … `015_2.npy` las mismas 16 actividades vistas por el grupo 2.

## Dispositivos físicos vs. archivos

El sistema tiene **5 dispositivos físicos** (S1–S5), pero en cada ejercicio sólo se
activan **3**, y sus señales se reparten en **2 archivos**:

| Dispositivo | Dónde va | ¿Cuándo se activa? | ¿En qué archivo cae? |
|---|---|---|---|
| S1 | antebrazo (~10 cm sobre la muñeca) | ejercicios de miembro superior (`000`–`012`) | `_1` |
| S2 | brazo (~8 cm sobre el codo) | ejercicios de miembro superior (`000`–`012`) | `_1` |
| S3 | pantorrilla (10–20 cm bajo la rótula) | ejercicios de miembro inferior (`013`–`015`) | `_1` |
| S4 | muslo (recto femoral) | ejercicios de miembro inferior (`013`–`015`) | `_1` |
| S5 | guante en la mano afectada | **siempre** | `_2` |

S1–S4 son IMU de nueve ejes (MPU9250). S5 es un guante con 5 sensores de flexión
piezorresistivos (uno por dedo) más una IMU en el dorso. Todo muestrea a 50 Hz.

## Qué captura cada archivo

### `<mov>_1.npy` → las **dos IMU del miembro que se ejercita** (6 canales)

Tres ángulos de Euler de cada una de las dos IMU:

| Canal | Nombre | Qué mide | Rango observado |
|---|---|---|---|
| 0 | `pitch1` | inclinación arriba/abajo de la **IMU 1** (S1 antebrazo, o S3 pantorrilla) | ±90° |
| 1 | `yaw1` | giro izquierda/derecha de la IMU 1 | no acotado (hasta ±1,178°, deriva) |
| 2 | `roll1` | rodamiento de la IMU 1 | no acotado |
| 3 | `pitch2` | inclinación arriba/abajo de la **IMU 2** (S2 brazo, o S4 muslo) | ±90° |
| 4 | `yaw2` | giro izquierda/derecha de la IMU 2 | no acotado |
| 5 | `roll2` | rodamiento de la IMU 2 | no acotado |

Ojo: el sufijo `1`/`2` del canal es "primera IMU / segunda IMU", y **qué IMU es
depende del ejercicio**. En `000`–`012` es antebrazo/brazo; en `013`–`015` es
pantorrilla/muslo. Por eso `pitch1` de `013` tiene una media ~50° distinta a la de
`000`: es otro segmento del cuerpo.

### `<mov>_2.npy` → el **guante S5** (6 canales)

| Canal | Nombre | Qué mide | Rango observado |
|---|---|---|---|
| 0 | `f1` | flexión del pulgar | 0° a ~117° |
| 1 | `f2` | flexión del índice | 0° a ~114° |
| 2 | `f3` | flexión del medio | 0° a ~114° |
| 3 | `f4` | flexión del anular | 0° a ~113° |
| 4 | `f5` | flexión del meñique | 0° a ~115° |
| 5 | `pitch3` | inclinación de la muñeca (IMU del guante) | ±188° |

Los cinco canales de flexión son **no negativos** (se comprobó en los 16 archivos);
sólo `pitch3` tiene signo. Esto confirma cuál archivo es cuál.

## Forma de cada archivo

Todos son `(d, 880, 6)` en `float64`:

- `d` = repeticiones (muestras) de ese ejercicio. Es **igual** en `_1` y `_2` del
  mismo movimiento: la repetición `k` de `000_1` y de `000_2` son el mismo intento
  del mismo paciente, visto por sensores distintos.
- `880` = pasos de tiempo a 50 Hz = 17.6 s. Las señales más largas se truncaron y las
  más cortas se rellenaron con ceros al final.
- `6` = canales de la tabla correspondiente.

| Movimiento | Ejercicio (Tabla 3) | Grupo | `d` |
|---|---|---|---:|
| 000 | bobath handshake | miembro superior combinado | 232 |
| 001 | bobath flexion/extension | miembro superior combinado | 212 |
| 002 | bobath forward flexion/extension | miembro superior combinado | 267 |
| 003 | bobath anterior/posterior rotation | miembro superior combinado | 250 |
| 004 | elbow flexion and wrist compression | miembro superior combinado | 287 |
| 005 | wrist flexion and extension | mano | 293 |
| 006 | finger-to-finger training | mano | 260 |
| 007 | ball gripping | mano | 385 |
| 008 | shoulder joint internal and external | hombro | 299 |
| 009 | breast expansion | hombro | 307 |
| 010 | flexion-pressure rotation forward and backward | brazo | 311 |
| 011 | elbow joint flexion and touch | brazo | 235 |
| 012 | shoulder touch training | brazo | 293 |
| 013 | ankle extension & knee internal/external rotation | miembro inferior | 313 |
| 014 | knee flexion and extension | miembro inferior | 359 |
| 015 | hip flexion and extension | miembro inferior | 313 |
| | **Total** | | **4,616** |

## Resumen en una línea

Dos archivos por ejercicio: `_1` es *cómo se mueve el brazo (o la pierna)* con dos IMU,
`_2` es *qué hace la mano* con el guante. Los 16 de cada tipo son los 16 ejercicios.
