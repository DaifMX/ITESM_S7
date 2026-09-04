"""Uso (desde `Linear_Regression/`):

    uv run python -m linear_regression.predict --file ../Data/007_1.npy --rep 12
    uv run python -m linear_regression.predict --file ../Data/007_1.npy --all-test
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np

from .common import DATASET_META, MODEL_FILE, MOVEMENT_NAMES, movement_from_filename, partner_file
from .features import feature_names, repetition_features
from .model import LinearRegression


def load_model(path: Path) -> LinearRegression:
    if not path.exists():
        sys.exit(f"No existe el modelo {path}. Entrena primero con "
                 "`uv run python -m linear_regression.train`.")
    model = LinearRegression.load(path)
    if model.feature_names != feature_names():
        sys.exit("Los nombres de columna del modelo no coinciden con `features.py`; "
                 "vuelve a generar el dataset y a entrenar.")
    return model


def load_repetitions(file: Path) -> tuple[np.ndarray, np.ndarray]:
    try:
        path_1, path_2 = partner_file(file)
    except ValueError as exc:
        sys.exit(str(exc))
    for p in (path_1, path_2):
        if not p.exists():
            sys.exit(f"Falta el archivo pareja {p.name}: se necesitan ambos flujos "
                     f"({path_1.name} y {path_2.name}) para construir la fila.")
    reps_1, reps_2 = np.load(path_1), np.load(path_2)
    if reps_1.shape != reps_2.shape:
        sys.exit(f"{path_1.name} y {path_2.name} tienen formas distintas: {reps_1.shape} vs {reps_2.shape}")
    return reps_1, reps_2


def predict_one(model: LinearRegression, rep_1: np.ndarray, rep_2: np.ndarray) -> tuple[int, np.ndarray]:
    """Devuelve la clase predicha y las 16 salidas continuas."""
    x = repetition_features(rep_1, rep_2)[None, :]
    scores = model.decision_function(x)[0]
    return int(np.argmax(scores)), scores


def describe_prediction(pred: int, scores: np.ndarray, truth: int | None) -> str:
    top = np.argsort(scores)[::-1][:3]
    lines = [f"  Actividad predicha: {pred:03d} · {MOVEMENT_NAMES[pred]}",
             "  Tres salidas más altas: " + ", ".join(f"{c:03d} ({scores[c]:+.3f})" for c in top)]
    if truth is not None:
        lines.append(f"  Rótulo real: {truth:03d} · {MOVEMENT_NAMES[truth]} → "
                     + ("✅ acierto" if pred == truth else "❌ fallo"))
    return "\n".join(lines)


def test_indices(movement: int) -> list[int]:
    if not DATASET_META.exists():
        sys.exit(f"No existe {DATASET_META}; genera el dataset para saber qué repeticiones son de test.")
    meta = json.loads(DATASET_META.read_text(encoding="utf-8"))
    return meta["splits"][f"{movement:03d}"]["test"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--file", type=Path, required=True, help="ruta a <mov>_1.npy o <mov>_2.npy")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--rep", type=int, help="índice de la repetición dentro del archivo")
    group.add_argument("--all-test", action="store_true",
                       help="predecir todas las repeticiones de test de ese archivo")
    parser.add_argument("--model", type=Path, default=MODEL_FILE)
    args = parser.parse_args()

    model = load_model(args.model)
    reps_1, reps_2 = load_repetitions(args.file)
    truth = movement_from_filename(args.file)

    if args.all_test:
        if truth is None:
            sys.exit("--all-test requiere que el archivo lleve el rótulo en el nombre (p. ej. 007_1.npy).")
        indices = test_indices(truth)
        hits = 0
        for k in indices:
            pred, _ = predict_one(model, reps_1[k], reps_2[k])
            hits += pred == truth
            print(f"  rep {k:3d} → {pred:03d} {'✅' if pred == truth else '❌ (' + MOVEMENT_NAMES[pred] + ')'}")
        print(f"\n{args.file.name}: {hits}/{len(indices)} aciertos en test ({100 * hits / len(indices):.1f} %)")
        return

    if not 0 <= args.rep < len(reps_1):
        sys.exit(f"--rep debe estar entre 0 y {len(reps_1) - 1} para {args.file.name}")
    pred, scores = predict_one(model, reps_1[args.rep], reps_2[args.rep])
    print(f"{args.file.name} · repetición {args.rep}")
    print(describe_prediction(pred, scores, truth))


if __name__ == "__main__":
    main()
