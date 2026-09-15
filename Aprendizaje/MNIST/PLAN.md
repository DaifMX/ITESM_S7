# MNIST MLP — Plan de implementación

Tres implementaciones del mismo MLP (scikit-learn, Keras, PyTorch) sobre el dataset MNIST en formato IDX.
Marca cada casilla al terminar la tarea.

---

## Paso 0 — Preparar el entorno

- [X] Crear un entorno virtual dentro del proyecto (`python3 -m venv .venv`) y activarlo.
- [X] Instalar dependencias: `numpy`, `torch`, `scikit-learn`, `tensorflow` (incluye Keras), `matplotlib`, `jupyter`.
- [X] Verificar que `import torch`, `import sklearn` e `import tensorflow` funcionan desde el kernel del notebook.
- [X] Agregar `.venv/` al `.gitignore`.
- [X] Seleccionar el kernel de `.venv` en los tres notebooks de `src/`.

## Paso 1 — Limpiar la carpeta `data/`

Cada archivo está duplicado: una copia suelta (`train-images.idx3-ubyte`) y otra dentro de una carpeta con el mismo nombre (`train-images-idx3-ubyte/train-images-idx3-ubyte`). Es un residuo de descomprimir los `.gz`.

- [x] Conservar solo una copia de cada uno de los 4 archivos (recomendado: los sueltos con punto, `*.idx3-ubyte` / `*.idx1-ubyte`).
- [x] Borrar las 4 carpetas duplicadas y el `.DS_Store`.
- [x] Confirmar tamaños: imágenes train 47,040,016 bytes, labels train 60,008, imágenes test 7,840,016, labels test 10,008.

## Paso 2 — Entender y leer el formato IDX

El formato es un encabezado de enteros big-endian de 32 bits seguido de bytes crudos (un byte por pixel o por etiqueta).

| Archivo | Encabezado | Cuerpo |
|---|---|---|
| `*-images.idx3-ubyte` | 16 bytes: magic (2051), N, filas (28), columnas (28) | N × 28 × 28 bytes, valores 0–255 |
| `*-labels.idx1-ubyte` | 8 bytes: magic (2049), N | N bytes, valores 0–9 |

- [X] Crear `src/mnist_loader.py` con dos funciones: `load_images(path)` y `load_labels(path)`.
- [x] En cada función: abrir en modo binario, leer el encabezado con `struct.unpack` usando formato big-endian (`>IIII` para imágenes, `>II` para etiquetas).
- [x] Validar el número mágico (2051 / 2049) con un `assert`.
- [x] Leer el resto con `np.frombuffer(..., dtype=np.uint8)` y hacer `reshape` a `(N, 784)` en el caso de imágenes.
- [x] Devolver copias escribibles (`.copy()`), porque `frombuffer` produce arrays de solo lectura y PyTorch se queja.
- [x] Agregar una función `load_mnist(data_dir)` que devuelva `X_train, y_train, X_test, y_test`.
- [x] Probar el loader: `X_train.shape == (60000, 784)`, `y_train.shape == (60000,)`, `X_test.shape == (10000, 784)`.
- [x] Graficar 10 imágenes con su etiqueta usando `matplotlib` para confirmar visualmente que la lectura es correcta.

## Paso 3 — Preprocesamiento (idéntico en las 3 implementaciones)

- [x] Convertir píxeles a `float32` y dividir entre 255 para dejarlos en el rango [0, 1].
- [x] Mantener las imágenes aplanadas como vectores de 784 (un MLP recibe vectores, no matrices 28×28).
- [x] Dejar las etiquetas como enteros 0–9 (Keras y PyTorch aceptan enteros con la pérdida correcta; sklearn también).
- [x] Definir una semilla global (`SEED = 42`) y usarla en las tres implementaciones.

## Paso 4 — Definir la arquitectura común

Se debe usar exactamente la misma en las 3 implementaciones para que los resultados sean comparables. Anotarla aquí:

| Elemento | Valor |
|---|---|
| Entrada | 784 |
| Capa oculta 1 | 128, ReLU |
| Capa oculta 2 | 64, ReLU |
| Salida | 10 (logits / softmax según framework) |
| Optimizador | Adam, lr = 0.001 |
| Pérdida | Cross-entropy |
| Batch size | 64 |
| Épocas | 10 |

- [x] Confirmar o ajustar los valores de la tabla (si cambian, cambiarlos en los 3 notebooks).
- [x] Documentar la arquitectura al inicio de cada notebook en una celda de texto.

## Paso 5 — Implementación con PyTorch (`src/pytorch.ipynb`)

- [x] Importar el loader y cargar los datos ya preprocesados.
- [x] Convertir a tensores con `torch.from_numpy`; imágenes como `float32`, etiquetas como `int64` (`long`).
- [x] Crear un `TensorDataset` y un `DataLoader` para train (`shuffle=True`) y otro para test (`shuffle=False`).
- [x] Definir el modelo con `nn.Sequential` o una subclase de `nn.Module`: `Linear(784,128) → ReLU → Linear(128,64) → ReLU → Linear(64,10)`.
- [x] No poner softmax al final: `nn.CrossEntropyLoss` espera logits crudos.
- [x] Crear la función de pérdida (`nn.CrossEntropyLoss`) y el optimizador (`torch.optim.Adam`).
- [x] Escribir el ciclo de entrenamiento: por cada época y cada batch → `optimizer.zero_grad()` → forward → loss → `loss.backward()` → `optimizer.step()`.
- [x] Guardar la pérdida promedio por época en una lista.
- [x] Escribir la evaluación: `model.eval()`, `torch.no_grad()`, `argmax(dim=1)`, comparar con etiquetas y calcular accuracy.
- [x] Medir el tiempo de entrenamiento con `time.perf_counter()`.
- [x] Obtener las predicciones del test como array de NumPy para la matriz de confusión.
- [x] Verificar: accuracy en test ≈ 97–98 %. Si está muy por debajo de 90 %, revisar normalización, `zero_grad` y softmax accidental.

## Paso 6 — Implementación con scikit-learn (`src/sklearn.ipynb`)

- [x] Cargar los mismos datos con el loader.
- [x] Usar `MLPClassifier(hidden_layer_sizes=(128, 64), activation='relu', solver='adam', learning_rate_init=0.001, batch_size=64, max_iter=10, random_state=SEED)`.
- [x] Entrenar con `fit` y medir el tiempo.
- [x] Evaluar con `score` o `accuracy_score` sobre test.
- [x] Guardar `loss_curve_` para comparar con las otras implementaciones.
- [x] Obtener predicciones con `predict` para la matriz de confusión.

## Paso 7 — Implementación con Keras (`src/keras.ipynb`)

- [x] Cargar los mismos datos con el loader.
- [x] Definir `Sequential([Input(784), Dense(128, relu), Dense(64, relu), Dense(10, softmax)])`.
- [x] Compilar con `optimizer=Adam(0.001)`, `loss='sparse_categorical_crossentropy'`, `metrics=['accuracy']`.
- [x] Entrenar con `fit(epochs=10, batch_size=64)` y medir el tiempo.
- [x] Evaluar con `evaluate` sobre test.
- [x] Guardar `history.history['loss']` para la curva de pérdida.
- [x] Obtener predicciones con `predict` + `argmax` para la matriz de confusión.

## Paso 8 — Comparación de resultados

- [x] Recopilar de cada implementación: accuracy en test, tiempo de entrenamiento, curva de pérdida por época.
- [x] Generar una matriz de confusión por implementación con `sklearn.metrics.confusion_matrix`.
- [x] Graficar las tres curvas de pérdida en una misma figura.
- [x] Armar una tabla resumen (framework, accuracy, tiempo).
- [x] Escribir conclusiones: diferencias de accuracy, velocidad y facilidad de uso entre los tres frameworks.

## Paso 9 — Entrega

- [x] Limpiar las salidas innecesarias de los notebooks y ejecutarlos de principio a fin para confirmar que corren sin errores.
- [x] Escribir un `README.md` breve con cómo instalar y ejecutar.
- [x] Hacer commit de `src/`, `PLAN.md`, `README.md` y `.gitignore` (no de `data/` ni de `.venv/`).
