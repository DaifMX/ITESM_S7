# Resultados · regresión lineal multisalida por descenso de gradiente

Generado por `python -m linear_regression.train`. Dataset: 4532 filas × 842 características, particiones {'train': 3172, 'val': 681, 'test': 679}.

## Hiperparámetros

| Parámetro | Valor |
|---|---|
| λ (L2) | 0.01 (elegido en val, ver barrido) |
| α (tasa de aprendizaje) | 0.00764 = 1 / λ_max por iteración de potencia |
| épocas | 3000 (gradiente completo) |
| inicialización | W = 0 |

## Barrido de λ (macro-F1 en val; test no se toca)

| λ | exact. val | macro-F1 val | J_train final | tiempo |
|---:|---:|---:|---:|---:|
| 0.01 | 0.877 | 0.873 | 0.1453 | 1.1 s **←** |
| 0.1 | 0.877 | 0.873 | 0.1454 | 1.2 s |
| 1 | 0.877 | 0.873 | 0.1456 | 1.1 s |
| 10 | 0.875 | 0.872 | 0.1477 | 1.2 s |
| 100 | 0.874 | 0.871 | 0.1643 | 1.3 s |

## Métricas del modelo final (λ elegido)

| Conjunto | exactitud | macro-F1 | MSE one-hot | R² one-hot |
|---|---:|---:|---:|---:|
| train | 0.944 | 0.944 | 0.0182 | 0.689 |
| val | 0.877 | 0.873 | 0.0258 | 0.559 |
| test | 0.882 | 0.877 | 0.0247 | 0.578 |

Brecha exactitud train − test: **6.2 puntos**.

## Comparaciones en test

| Modelo | exactitud | macro-F1 |
|---|---:|---:|
| Clase mayoritaria (`007`) | 0.084 | — |
| Sensor 1 solo (421 caract., mismo λ) | 0.788 | 0.774 |
| **Ambos sensores (842 caract.)** | **0.882** | **0.877** |

## Recall, precisión y F1 por clase (test)

| Actividad | Ejercicio | n | recall | precisión | F1 |
|---|---|---:|---:|---:|---:|
| `000` | bobath handshake | 35 | 0.91 | 1.00 | 0.96 |
| `001` | bobath flexion/extension | 30 | 0.77 | 0.77 | 0.77 |
| `002` | bobath forward flexion/extension | 40 | 0.82 | 0.97 | 0.89 |
| `003` | bobath anterior/posterior rotation | 37 | 0.89 | 1.00 | 0.94 |
| `004` | elbow flexion and wrist compression | 42 | 0.93 | 0.95 | 0.94 |
| `005` | wrist flexion and extension | 42 | 0.98 | 0.93 | 0.95 |
| `006` | finger-to-finger training | 38 | 0.63 | 0.80 | 0.71 |
| `007` | ball gripping | 57 | 0.96 | 0.87 | 0.92 |
| `008` | shoulder joint internal and external | 45 | 0.80 | 0.84 | 0.82 |
| `009` | breast expansion | 46 | 0.91 | 0.79 | 0.85 |
| `010` | flexion-pressure rotation forward and backward | 46 | 1.00 | 0.94 | 0.97 |
| `011` | elbow joint flexion and touch | 33 | 0.97 | 0.86 | 0.91 |
| `012` | shoulder touch training | 42 | 0.62 | 0.68 | 0.65 |
| `013` | ankle extension & knee internal/external rotation | 45 | 0.87 | 0.93 | 0.90 |
| `014` | knee flexion and extension | 54 | 1.00 | 0.89 | 0.94 |
| `015` | hip flexion and extension | 47 | 0.94 | 0.90 | 0.92 |

Más difíciles (recall): `012` (0.62), `006` (0.63), `001` (0.77). Más fáciles: `014` (1.00), `010` (1.00), `005` (0.98).

## Matriz de confusión (test; filas = real, columnas = predicha)

| real \ pred | `000` | `001` | `002` | `003` | `004` | `005` | `006` | `007` | `008` | `009` | `010` | `011` | `012` | `013` | `014` | `015` |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `000` | **32** | · | · | · | · | 1 | · | · | 2 | · | · | · | · | · | · | · |
| `001` | · | **23** | 1 | · | · | · | · | · | · | 2 | 1 | 2 | · | · | 1 | · |
| `002` | · | 5 | **33** | · | · | · | · | · | · | · | · | · | 1 | 1 | · | · |
| `003` | · | 2 | · | **33** | · | 2 | · | · | · | · | · | · | · | · | · | · |
| `004` | · | · | · | · | **39** | · | · | 1 | · | · | 1 | · | · | · | · | 1 |
| `005` | · | · | · | · | 1 | **41** | · | · | · | · | · | · | · | · | · | · |
| `006` | · | · | · | · | · | · | **24** | 2 | · | · | · | · | 11 | 1 | · | · |
| `007` | · | · | · | · | · | · | · | **55** | · | · | · | 2 | · | · | · | · |
| `008` | · | · | · | · | · | · | 1 | · | **36** | 8 | · | · | · | · | · | · |
| `009` | · | · | · | · | · | · | · | · | 4 | **42** | · | · | · | · | · | · |
| `010` | · | · | · | · | · | · | · | · | · | · | **46** | · | · | · | · | · |
| `011` | · | · | · | · | · | · | · | 1 | · | · | · | **32** | · | · | · | · |
| `012` | · | · | · | · | 1 | · | 4 | 4 | · | 1 | · | 1 | **26** | 1 | · | 4 |
| `013` | · | · | · | · | · | · | · | · | · | · | · | · | · | **39** | 6 | · |
| `014` | · | · | · | · | · | · | · | · | · | · | · | · | · | · | **54** | · |
| `015` | · | · | · | · | · | · | 1 | · | 1 | · | 1 | · | · | · | · | **44** |

Pares más confundidos (suma de ambos sentidos): `006`↔`012` (15), `008`↔`009` (12), `013`↔`014` (6), `001`↔`002` (6), `012`↔`015` (4).

## Criterios de aceptación (sección 6 de la especificación)

| Criterio | Valor | ¿Cumple? |
|---|---:|:---:|
| exactitud en test ≥ 80 % | 0.882 | ✅ |
| macro-F1 en test ≥ 0.78 | 0.877 | ✅ |
| brecha train − test ≤ 8 puntos | 6.2 pts | ✅ |
| R² one-hot en test ≥ 0.45 | 0.578 | ✅ |
| J(train) decreciente en toda la curva | — | ✅ |

Figuras: `curva_aprendizaje.png`, `matriz_confusion.png`.

> Nota: `Rehab_exercise` no trae ID de paciente, así que repeticiones de un mismo paciente pueden caer en train y en test. Las métricas son optimistas respecto a un paciente nunca visto.
