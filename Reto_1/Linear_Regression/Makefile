# Makefile · Linear_Regression
#
# Atajos para las etapas del proyecto. Todo corre con `uv run`, que crea el entorno
# (Python >= 3.14, NumPy, Matplotlib) la primera vez.
#
#   make            → todo el flujo (dataset → entrenamiento)
#   make dataset    → Data/*.npy → dataset/rehab_windows.csv + DICCIONARIO.md + meta.json
#   make train      → dataset → models/linreg.npz + results/
#   make predict FILE=../Data/007_1.npy REP=5
#   make predict-all                              (repeticiones de test de los 16 movimientos)
#   make predict-all FILE=../Data/007_1.npy      (sólo las repeticiones de test de ese archivo)
#   make clean      → borra lo generado (dataset/, models/, results/)

UV      ?= uv run --no-sync
PYTHON  := $(UV) python
PKG     := linear_regression

DATA_DIR    := ../Data
DATASET_CSV := dataset/rehab_windows.csv
MODEL       := models/linreg.npz
RESULTS     := results/metrics.md

SRC := $(wildcard src/$(PKG)/*.py)

# Parámetros de `predict`.
FILE ?= $(DATA_DIR)/007_1.npy
REP  ?= 5

.PHONY: all sync dataset train predict predict-all clean help

all: train

## Instala/actualiza el entorno virtual.
sync:
	uv sync

## Genera el dataset por ventanas (sólo si cambió el código o falta el CSV).
dataset: $(DATASET_CSV)

$(DATASET_CSV): src/$(PKG)/build_dataset.py src/$(PKG)/features.py src/$(PKG)/stats.py src/$(PKG)/split.py src/$(PKG)/common.py
	$(PYTHON) -m $(PKG).build_dataset

## Entrena, evalúa y guarda pesos, métricas y figuras.
train: $(RESULTS)

$(RESULTS) $(MODEL): $(DATASET_CSV) src/$(PKG)/train.py src/$(PKG)/model.py src/$(PKG)/metrics.py src/$(PKG)/data.py
	$(PYTHON) -m $(PKG).train

## Predice una repetición: make predict FILE=../Data/007_1.npy REP=5
predict: $(MODEL)
	$(PYTHON) -m $(PKG).predict --file $(FILE) --rep $(REP)

## Predice las repeticiones de test de todos los movimientos (o sólo de FILE si se pasa).
predict-all: $(MODEL)
ifeq ($(origin FILE),command line)
	$(PYTHON) -m $(PKG).predict --file $(FILE) --all-test
else
	@for f in $(DATA_DIR)/*_1.npy; do \
		echo "== $$f"; \
		$(PYTHON) -m $(PKG).predict --file $$f --all-test | tail -n 1; \
	done
endif

## Borra todo lo generado. Se regenera con `make`.
clean:
	rm -rf dataset models results .pytest_cache
	find . -name __pycache__ -type d -prune -exec rm -rf {} +

## Muestra esta ayuda.
help:
	@grep -E '^## ' -A1 $(MAKEFILE_LIST) | grep -E '^(##|[a-z-]+:)' | sed -E 'N;s/^## (.*)\n([a-z-]+):.*/  \2\t\1/' | expand -t 16
