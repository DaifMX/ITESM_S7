# Reto 1 — Análisis del dataset REHAB (`Rehab_exercise`)

## Paso 4 — Corroboración de la estructura contra el artículo

**Artículo:** *A wearable sensor–based kinematic dataset collected under standardized
rehabilitation tasks from 120 post-stroke patients*, **Scientific Data** (2026),
[doi:10.1038/s41597-026-07802-2](https://doi.org/10.1038/s41597-026-07802-2).

**Verificación reproducible:** `uv run python -m dataset_analysis.step04_verify_structure`

### Lo que dice el artículo

El dataset REHAB se tomó de 120 pacientes post-ictus (109 completaron el estudio) con
4 IMU de nueve ejes (MPU9250) más un guante instrumentado, muestreando a **50 Hz**:

| Sensor | Colocación |
|---|---|
| S1 | antebrazo, ~10 cm sobre el pliegue dorsal de la muñeca |
| S2 | brazo, ~8 cm sobre el epicóndilo lateral |
| S3 | pierna, 10–20 cm bajo la rótula |
| S4 | muslo, sobre el recto femoral |
| S5 | guante en la mano afectada (sensores de flexión + IMU) |

Se divide en dos carpetas: `Rehab_assessment` (27 movimientos de evaluación, escala
Fugl-Meyer) y `Rehab_exercise` (**16 movimientos de entrenamiento**), que es la que se
usa en este reto. Para `Rehab_exercise/d02_processed_data` el artículo declara:

- Archivos `<movementID>_<sensorID>.npy`, con `movementID` 000–015 y `sensorID` 1 o 2.
- Dimensiones `d × 880 × 6` (repeticiones × pasos de tiempo × canales).
- 4,616 muestras totales (de 4,689 iniciales, tras eliminar muestras erróneas),
  entre 212 y 385 por movimiento.
- Señales truncadas o rellenadas con ceros hasta 880 puntos (8–10 ciclos de movimiento).
- Canales por `sensorID`:
  - `_1` → S1+S2 (miembro superior) o S3+S4 (miembro inferior): `Pitch1, Yaw1, Roll1, Pitch2, Yaw2, Roll2`
  - `_2` → S5 (guante): `f1, f2, f3, f4, f5, pitch3`
- Preprocesamiento: filtro de media móvil (ventana 10), normalización de media cero,
  estandarización de longitud e inspección manual de errores.

### Lo que se observa en `Data/`

| Afirmación del artículo | Observado | ¿Coincide? |
|---|---|---|
| 32 archivos `<mov>_<sensor>.npy` | 32 archivos, `movementID` 000–015, `sensorID` 1 y 2 | ✅ |
| Dimensiones `d × 880 × 6` | todos los archivos son `(d, 880, 6)`, `float64` | ✅ |
| Mismo `d` para ambos sensores | idéntico en los 16 movimientos | ✅ |
| 4,616 muestras totales | **4,616** | ✅ |
| `d` entre 212 y 385 | mín. 212 (mov. 001), máx. 385 (mov. 007), media 288.5 | ✅ |
| 50 Hz → 880 pasos | 880 / 50 Hz = **17.6 s** por repetición | ✅ |
| `_1` = ángulos de Euler de dos IMU | 6 canales con signo; rangos ±88 (Pitch1/Pitch2) y ±160–190 (Yaw/Roll) | ✅ |
| `_2` = guante `f1..f5, pitch3` | canales 0–4 **no negativos** (flexión), canal 5 con signo ±187 | ✅ |
| Relleno con ceros hasta 880 | mov. 000: 38/232 repeticiones con ceros al final (hasta 8.1 s); el resto llega truncado a 880 | ✅ |
| Normalización de media cero | mediana de \|media\| por repetición y canal = **12.1** (máx. 68.1) | ❌ |

**Conclusión:** la estructura de los archivos corresponde con lo que reporta el artículo
en nomenclatura, organización, dimensiones y conteos —incluido el total exacto de 4,616
muestras— por lo que la carpeta local es `Rehab_exercise/d02_processed_data`.

### Discrepancias y notas

1. **Media cero.** Los datos procesados **no** están centrados en cero por repetición
   (ni por canal completo). Aunque el artículo lista la normalización de media cero en
   su pipeline, las señales conservan el offset postural. Hay que tenerlo en cuenta en
   los pasos de estadísticos e histogramas: las medias por actividad son informativas,
   no artefactos de una normalización.
2. **Los sensores 1 y 2 no son redundantes.** `_1` son ángulos de Euler de dos IMU del
   miembro afectado y `_2` son los sensores de flexión del guante: miden cosas distintas
   y en unidades distintas. Esto es relevante para el paso 6.
3. El relleno de ceros difiere ligeramente entre `_1` y `_2` (38 vs. 39 repeticiones en
   el movimiento 000), es decir, cada flujo se segmentó por separado.
4. El artículo no publica la lista nominal de los 16 ejercicios; sólo indica que
   trabajan hombros, codos, brazos, caderas, muslos y rodillas.

---

## Paso 8 — Una actividad, una repetición, un canal en el tiempo

**Reproducible:** `uv run python -m dataset_analysis.step08_plot_repetition`

Selección (sensor **1**, elegido en el paso 7 — los ángulos de Euler de las dos IMU
del miembro afectado, que son la señal cinemática propiamente dicha):

| | |
|---|---|
| Actividad | movimiento `000` (`000_1.npy`, 232 repeticiones) |
| Repetición | índice 0 (sin relleno de ceros) |
| Canal | 0 → `Pitch1` (IMU S1, antebrazo) |

![Movimiento 000, repetición 0, canal Pitch1](figures/step08_000_s1_rep0_Pitch1.png)

Estadísticos de la repetición graficada:

| Métrica | Valor |
|---|---|
| Duración | 17.6 s (880 pasos a 50 Hz) |
| Relleno de ceros | 0 pasos |
| Rango | −69.4° a 38.3° |
| Media / desviación | −17.4° / 35.0° |

**Observaciones.** La señal es claramente periódica: se distinguen ~5 ciclos completos
de flexión–extensión en los 17.6 s (≈ 3.5 s por ciclo), consistente con los 8–10 ciclos
que menciona el artículo para el conjunto (esta repetición está en el extremo lento).
La curva es suave, sin ruido de alta frecuencia, efecto del filtro de media móvil de
ventana 10 del preprocesamiento. La oscilación no está centrada en 0° sino alrededor de
−17°, lo que confirma la discrepancia del paso 4: el offset postural se conserva.

El script sombrea automáticamente la zona de relleno con ceros si la repetición elegida
la tuviera, para no leerla como señal real; basta cambiar `MOVEMENT`, `REPETITION` y
`CHANNEL` en la cabecera del módulo para explorar otras combinaciones.

---

## Paso 9 — Repeticiones por actividad: ¿está balanceado?

**Reproducible:** `uv run python -m dataset_analysis.step09_repetition_counts`

![Repeticiones por actividad](figures/step09_repeticiones_por_actividad.png)

| Métrica | Valor |
|---|---|
| Total de repeticiones | 4,616 en 16 actividades |
| Mínimo | 212 (movimiento `001`) |
| Máximo | 385 (movimiento `007`) |
| Media / mediana | 288.5 / 293.0 |
| Desviación estándar | 44.1 |
| Razón máx./mín. | **1.82** |
| Reparto uniforme | 288.5 por actividad |

Los conteos son idénticos para el sensor 1 y el 2, así que la gráfica describe el
dataset completo y no sólo el flujo elegido en el paso 7.

**¿Se ven balanceados?** Sí, de forma razonable —no perfectamente. Ninguna actividad
domina ni queda marginada: todas aportan entre 4.6 % y 8.3 % del total, cuando el
reparto uniforme sería 6.25 %. La razón entre la clase más y la menos poblada es de
**1.82**, muy lejos de los desbalances severos (10:1 o más) que obligan a remuestrear o
a ponderar la función de pérdida. Trece de las 16 actividades caen dentro de ±20 % del
reparto uniforme (quedan fuera sólo `001`, `007` y `014`); los casos extremos son
`007` (+33 %) y `001` (−27 %).

En la práctica esto significa que un clasificador entrenado con estos datos no necesita
corrección de desbalance, pero sí conviene reportar métricas macro-promediadas (macro-F1
en lugar de exactitud) y estratificar las particiones de entrenamiento/prueba por
actividad, para que las clases pequeñas (`001`, `000`, `011`) no queden sub-representadas
por azar en el conjunto de prueba.

---

## Paso 10 — Media y mediana por actividad

**Reproducible:** `uv run python -m dataset_analysis.step10_stats_table [canal]`
· tabla en [`tables/step10_media_mediana_s1_Pitch1.md`](tables/step10_media_mediana_s1_Pitch1.md)

Canal elegido: **`Pitch1`** (canal 0 del sensor 1, la IMU S1 del antebrazo), el mismo
del paso 8. Para cada actividad se concatenaron **todas** sus repeticiones y se
calcularon los estadísticos sobre el vector resultante. El relleno de ceros se descarta
antes de concatenar (ver paso 4): incluirlo arrastraría todas las medias hacia 0° por un
artefacto del preprocesamiento, no por el movimiento.

| Actividad | Media (`Pitch1`, °) | Mediana (`Pitch1`, °) |
|---|---:|---:|
| 000 | −5.96 | −3.66 |
| 001 | −13.62 | −16.99 |
| 002 | −11.05 | −16.35 |
| 003 | 0.53 | −4.29 |
| 004 | −3.72 | −2.01 |
| 005 | −5.02 | −4.92 |
| 006 | 6.02 | 13.78 |
| 007 | −3.08 | −3.82 |
| 008 | −5.24 | −9.56 |
| 009 | −2.82 | −4.84 |
| 010 | −13.60 | −27.73 |
| 011 | −4.76 | −6.18 |
| 012 | 8.84 | 21.96 |
| 013 | **54.56** | **67.75** |
| 014 | **47.10** | **61.12** |
| 015 | **55.34** | **69.89** |

Total: 3,339,973 muestras (de 139,807 a 285,952 por actividad).

**Observaciones.**

1. **Hay dos grupos claramente distintos.** Las actividades `013`, `014` y `015` tienen
   medias de +47° a +55°, mientras que las otras trece se agrupan entre −14° y +9°. Esa
   brecha de ~50° es demasiado grande para ser variabilidad entre pacientes: apunta a
   que en esos tres ejercicios el sensor `_1` está colocado en el miembro inferior
   (S3/S4, pierna y muslo, según el artículo), donde la postura de reposo del segmento
   es completamente distinta a la del antebrazo. El nombre del canal (`Pitch1`) es el
   mismo, pero el segmento del cuerpo no.
2. **Media y mediana se separan bastante.** La diferencia llega a 14.6° (`015`) y a
   14.1° (`010`), lo cual indica distribuciones **asimétricas y bimodales**, no
   gaussianas: el movimiento pasa más tiempo en los extremos del recorrido articular
   que en el centro, así que la mediana se corre hacia el extremo más visitado. Esto se
   confirma en los histogramas del paso 11, donde se ven dos jorobas.
3. **La media sola discrimina poco entre las trece actividades del primer grupo.** La
   desviación de las 16 medias es de 22.8°, pero casi toda proviene del bloque
   `013`–`015`; dentro del resto las medias se apiñan en un rango de 22° con
   distribuciones mucho más anchas que esa distancia (desviación típica de 33–41° dentro
   de cada actividad). Un solo estadístico de un solo canal no basta para separarlas.

---

## Pasos 11 y 12 — Histogramas superpuestos con la media de cada actividad

**Reproducible:** `uv run python -m dataset_analysis.step11_histograms [movA] [movB] [canal]`

Ambos histogramas se calculan como densidad sobre la **misma rejilla de bins**, para
poder compararlos directamente, y sobre la concatenación de todas las repeticiones (sin
relleno de ceros). La línea punteada del color de cada serie marca su media (paso 12).

Para cuantificar el traslape se reporta la **intersección de histogramas**
(∑ mín(densidad₁, densidad₂) · ancho_bin): 0 % son distribuciones disjuntas, 100 %
distribuciones idénticas.

### Caso separable: `001` vs `013` (canal `Pitch1`)

![Histogramas 001 vs 013](figures/step11_001_vs_013_s1_Pitch1.png)

| | actividad 001 | actividad 013 |
|---|---:|---:|
| n | 164,925 | 220,654 |
| media | −13.62° | 54.56° |
| mediana | −16.99° | 67.75° |
| desviación | 33.07° | 41.11° |

Separación de medias 68.2°, **traslape 13.7 %**. Las dos masas principales caen en
regiones distintas del eje y las líneas de la media quedan cada una dentro de su propia
joroba. Aquí un umbral en `Pitch1` ≈ 40° clasificaría correctamente la gran mayoría de
las muestras.

### Caso traslapado: `008` vs `009` (mismo canal)

![Histogramas 008 vs 009](figures/step11_008_vs_009_s1_Pitch1.png)

| | actividad 008 | actividad 009 |
|---|---:|---:|
| n | 235,109 | 245,672 |
| media | −5.24° | −2.82° |
| mediana | −9.56° | −4.84° |
| desviación | 38.23° | 33.12° |

Separación de medias de sólo 2.41° y **traslape 82.9 %**. Las dos líneas de la media
prácticamente se tocan y las distribuciones comparten la misma forma bimodal. Es el par
más difícil de todo el dataset (ver paso 13).

El contraste entre los dos casos deja ver por qué la media por sí sola engaña: en el
segundo par las medias son casi iguales pero las distribuciones **sí** difieren un poco
en las colas (`008` tiene más masa más allá de ±45°), algo que la tabla del paso 10 no
puede mostrar.

---

## Paso 13 — ¿Sirven los histogramas para diferenciar actividades?

**Reproducible:** `uv run python -m dataset_analysis.step13_channel_exploration`

En lugar de probar combinaciones a ojo, se barrieron **las 120 parejas de actividades ×
los 6 canales del sensor 1** (720 comparaciones) midiendo el traslape en cada una.

### Traslape por canal (sobre las 120 parejas)

| Canal | Rango del 99.8 % central | Traslape medio | Mínimo (par más separable) | Parejas con traslape < 50 % |
|---|---|---:|---|---:|
| `Pitch1` | −84° a 88° | **47.5 %** | 3.6 % (004–013) | **64 / 120** |
| `Yaw1` | −342° a 265° | 61.5 % | 18.8 % (005–009) | 39 / 120 |
| `Roll1` | −348° a 210° | 60.2 % | 19.9 % (003–004) | 34 / 120 |
| `Pitch2` | −86° a 88° | **46.5 %** | 4.0 % (011–014) | **63 / 120** |
| `Yaw2` | −153° a 153° | 61.1 % | 28.7 % (005–008) | 39 / 120 |
| `Roll2` | −167° a 136° | 63.1 % | 31.8 % (005–008) | 32 / 120 |

Tomando para cada pareja el **mejor de los seis canales**:

- traslape medio **33.7 %**
- **94 de 120** parejas quedan por debajo del 50 % de traslape
- sólo **1 de 120** pasa del 80 %: `008`–`009`, con 81.5 % incluso en su mejor canal
- canal ganador más veces: `Pitch2` (39×) y `Pitch1` (35×); `Roll2` nunca es el mejor

![Rejilla de histogramas](figures/step13_rejilla_histogramas.png)

![Matriz de traslape](figures/step13_traslape_min.png)

En la matriz se ve estructura de bloques: `013`–`015` se separan de casi todo lo demás
(el bloque de miembro inferior del paso 10), mientras que `000`–`003` y `008`–`010`
forman zonas oscuras de parejas mutuamente confundibles.

### Respuesta

**Sí, pero sólo parcialmente, y nunca con un histograma de un solo canal.**

1. **Como filtro grueso funcionan bien.** Con el mejor canal, 78 % de las parejas quedan
   por debajo del 50 % de traslape, y los pares que involucran a `013`, `014` o `015` se
   separan de forma casi perfecta (hasta 3.6 % de traslape). Un histograma basta para
   decidir si el ejercicio es de miembro superior o inferior.
2. **Como clasificador fino, no.** El traslape medio del mejor canal sigue siendo 33.7 %,
   y hay parejas —`008`–`009` sobre todo, pero también `000`–`008`, `001`–`002` y
   `006`–`012`— que son prácticamente indistinguibles por su distribución de valores (las cinco
   parejas más difíciles después de `008`–`009` son `000`–`008` con 72.7 %, `001`–`002`
   con 71.0 %, `006`–`012` con 69.5 %, `000`–`009` con 68.9 % y `002`–`009` con 68.8 %).
   Además, ningún canal individual gana siempre: `Pitch1` y `Pitch2` reparten el 62 % de
   las victorias, así que el canal correcto depende de qué par se quiera separar.
3. **La razón es que el histograma tira el tiempo a la basura.** Al concatenar todas las
   repeticiones y contar valores, se pierde el orden temporal, y el orden temporal es
   justamente lo que distingue a dos ejercicios que recorren el mismo rango articular con
   distinta secuencia, velocidad o coordinación entre articulaciones. Dos movimientos que
   barren el mismo arco de flexión–extensión producen el mismo histograma aunque uno sea
   una flexión de codo y otro una elevación de hombro. Se ve en la forma bimodal
   compartida de `008` y `009` en el paso 11.
4. **Los canales de pitch son mucho mejores que los de yaw y roll.** `Pitch1` y `Pitch2`
   tienen ~47 % de traslape medio frente a 60–63 % de los demás. La razón es física: el
   pitch está acotado a ±90° y anclado a la gravedad, así que es comparable entre
   pacientes; el yaw depende de la orientación inicial del paciente respecto al norte y
   el roll acumula deriva, de modo que la misma actividad produce histogramas distintos
   según quién y cómo se colocó el sensor. Eso ensancha las distribuciones y las hace
   traslaparse.

**Conclusión práctica:** los histogramas sirven como característica de entrada y como
herramienta exploratoria, no como clasificador. Para separar las 16 actividades hará
falta combinar varios canales y, sobre todo, añadir descriptores que sí conserven la
dinámica —frecuencia dominante y espectro, autocorrelación, número de ciclos, velocidad
angular, correlación entre las dos IMU— o pasar directamente a un modelo que consuma la
serie de tiempo completa.

### Dos hallazgos de calidad de datos que salieron del barrido

1. **74 de las 4,616 repeticiones (1.6 %) están completamente en cero** en los 880 pasos
   y los 6 canales; se concentran en los movimientos `011` (16), `012` (13) y `005` (12).
   No aportan señal y quedan descartadas al concatenar, pero sí inflan los conteos del
   paso 9.
2. **`Yaw` y `Roll` no vienen envueltos a ±180°.** El 0.6–0.7 % de las muestras de
   `Yaw1`/`Roll1` los excede, con extremos de hasta **−1,178°**, señal de ángulos
   acumulados o de deriva de integración. Por eso las rejillas de este paso se definen
   con los percentiles 0.1 y 99.9 en lugar del mínimo y el máximo: con un rango min–max
   toda la distribución se aplastaría en dos o tres bins. `Pitch1` y `Pitch2`, en cambio,
   se mantienen limpiamente dentro de ±90°.
3. Los picos aislados que se ven en algunos paneles de la rejilla vienen de **tramos con
   el sensor congelado**: el 2.3–2.9 % de las muestras de la IMU 2 (`Pitch2`, `Yaw2`,
   `Roll2`) cae dentro de tramos de medio segundo o más con un valor idéntico repetido,
   frente a sólo 0.08–0.17 % en la IMU 1. Son artefactos, no fisiología, y conviene no
   leerlos como modas de la distribución.
