# MNIST MLP: scikit-learn, Keras y PyTorch

Este proyecto entrena la misma red neuronal multicapa sobre MNIST con tres
frameworks. La arquitectura común es `784 → 128 (ReLU) → 64 (ReLU) → 10`, con
Adam (`lr=0.001`), lotes de 64 y 10 épocas.

## Preparación

Se recomienda Python 3.10 o 3.11, ya que TensorFlow no publica paquetes para
todas las versiones nuevas de Python.

```bash
python3.10 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m ipykernel install --user --name mnist-venv --display-name "MNIST (.venv)"
```

Coloca los cuatro archivos IDX sin comprimir en `data/`:

- `train-images.idx3-ubyte`
- `train-labels.idx1-ubyte`
- `t10k-images.idx3-ubyte`
- `t10k-labels.idx1-ubyte`

## Ejecución

Abre Jupyter desde la raíz y ejecuta, en cualquier orden, los notebooks de
entrenamiento:

```bash
jupyter lab
```

- `src/pytorch.ipynb`
- `src/sklearn.ipynb`
- `src/keras.ipynb`

Cada notebook valida y visualiza los datos, entrena el modelo, muestra su curva
de pérdida y matriz de confusión, y guarda métricas en `results/`. Después de
ejecutar los tres, ejecuta `src/comparison.ipynb` para generar la gráfica y tabla
comparativas.

Los datos, el entorno virtual y los resultados generados no se versionan.
