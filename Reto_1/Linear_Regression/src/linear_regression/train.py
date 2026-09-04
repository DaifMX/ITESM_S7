"""CLI: CSV → selecciona λ en val, evalúa en test, guarda pesos, métricas y figuras.

Protocolo (secciones 4.4 y 6 de la especificación):

1. Barrido de λ ∈ {0.01, 0.1, 1, 10, 100} entrenando en `train` y mirando macro-F1 en `val`.
2. Con el λ ganador se evalúa **una sola vez** en `test`.
3. Línea base "clase mayoritaria" y ablación con el sensor 1 solo (mismo λ).
4. Se guardan `models/linreg.npz`, `results/metrics.md`, `results/curva_aprendizaje.png`
   y `results/matriz_confusion.png`.

Uso (desde `Linear_Regression/`):

    uv run python -m linear_regression.train [--epochs 3000] [--lambdas 0.01 0.1 1 10 100] [--alpha α]
"""

import argparse
import time

import numpy as np

from . import common
from .common import MODEL_FILE, MOVEMENT_NAMES, MOVEMENTS, N_CLASSES, RESULTS_DIR, SERIES_1, SERIES_2
from .data import load_dataset, subset
from .features import sensor1_mask
from .metrics import accuracy, classification_report, macro_f1
from .model import DEFAULT_EPOCHS, LinearRegression

LAMBDA_GRID = [0.01, 0.1, 1.0, 10.0, 100.0]
ACCEPTANCE = {"test_accuracy": 0.80, "test_macro_f1": 0.78, "max_gap": 0.08, "test_r2": 0.45}


def fit_and_eval(X_tr, y_tr, X_va, y_va, lam, epochs, alpha, names, verbose=False):
    model = LinearRegression(lam=lam, alpha=alpha, epochs=epochs, feature_names=names)
    t0 = time.time()
    model.fit(X_tr, y_tr, X_va, y_va, verbose=verbose)
    seconds = time.time() - t0
    f1 = macro_f1(y_va, model.predict(X_va))
    acc = accuracy(y_va, model.predict(X_va))
    return model, f1, acc, seconds


def plot_learning_curve(model: LinearRegression) -> None:
    fig, ax = common.new_figure(figsize=(7, 4))
    h = model.history
    ax.plot(h["epoch"], h["train"], color=SERIES_1, linewidth=1.8, label="train")
    if h["val"]:
        ax.plot(h["epoch"], h["val"], color=SERIES_2, linewidth=1.8, label="val")
    common.style_axes(ax, f"Curva de aprendizaje (λ = {model.lam:g}, α = {model.alpha:.4f})",
                      "época", "J(W)")
    ax.set_yscale("log")
    ax.legend(frameon=False, fontsize=9, labelcolor=common.TEXT_SECONDARY)
    common.save_figure(fig, "curva_aprendizaje.png")


def plot_confusion(cm: np.ndarray) -> None:
    fig, ax = common.new_figure(figsize=(8, 7))
    row_norm = cm / np.where(cm.sum(axis=1, keepdims=True) > 0, cm.sum(axis=1, keepdims=True), 1)
    ax.imshow(row_norm, cmap="Blues", vmin=0, vmax=1)
    ax.set_xticks(range(N_CLASSES), MOVEMENTS, fontsize=8, color=common.TEXT_SECONDARY)
    ax.set_yticks(range(N_CLASSES), MOVEMENTS, fontsize=8, color=common.TEXT_SECONDARY)
    for i in range(N_CLASSES):
        for j in range(N_CLASSES):
            if cm[i, j] > 0:
                ax.text(j, i, str(cm[i, j]), ha="center", va="center", fontsize=7,
                        color="white" if row_norm[i, j] > 0.5 else common.TEXT_PRIMARY)
    ax.set_title("Matriz de confusión en test (filas = real, columnas = predicha)",
                 color=common.TEXT_PRIMARY, fontsize=12, loc="left", pad=12)
    ax.set_xlabel("actividad predicha", color=common.TEXT_SECONDARY, fontsize=10)
    ax.set_ylabel("actividad real", color=common.TEXT_SECONDARY, fontsize=10)
    ax.grid(False)
    common.save_figure(fig, "matriz_confusion.png")


def write_metrics(sweep, best_lam, model, reports, baseline_acc, ablation, epochs, n_rows) -> None:
    tr, va, te = reports["train"], reports["val"], reports["test"]
    gap = tr["accuracy"] - te["accuracy"]
    checks = [
        ("exactitud en test ≥ 80 %", te["accuracy"] >= ACCEPTANCE["test_accuracy"], f"{te['accuracy']:.3f}"),
        ("macro-F1 en test ≥ 0.78", te["macro_f1"] >= ACCEPTANCE["test_macro_f1"], f"{te['macro_f1']:.3f}"),
        ("brecha train − test ≤ 8 puntos", gap <= ACCEPTANCE["max_gap"], f"{100 * gap:.1f} pts"),
        ("R² one-hot en test ≥ 0.45", te["r2"] >= ACCEPTANCE["test_r2"], f"{te['r2']:.3f}"),
        ("J(train) decreciente en toda la curva",
         all(b <= a * (1 + 1e-9) for a, b in zip(model.history["train"], model.history["train"][1:])), "—"),
    ]
    lines = [
        "# Resultados · regresión lineal multisalida por descenso de gradiente",
        "",
        f"Generado por `python -m linear_regression.train`. Dataset: {n_rows} filas × "
        f"{len(model.feature_names)} características, particiones {dict(zip(['train', 'val', 'test'], n_rows_per_split(reports)))}.",
        "",
        "## Hiperparámetros",
        "",
        "| Parámetro | Valor |",
        "|---|---|",
        f"| λ (L2) | {best_lam:g} (elegido en val, ver barrido) |",
        f"| α (tasa de aprendizaje) | {model.alpha:.5f} = 1 / λ_max por iteración de potencia |",
        f"| épocas | {epochs} (gradiente completo) |",
        "| inicialización | W = 0 |",
        "",
        "## Barrido de λ (macro-F1 en val; test no se toca)",
        "",
        "| λ | exact. val | macro-F1 val | J_train final | tiempo |",
        "|---:|---:|---:|---:|---:|",
    ]
    for lam, f1, acc, j_final, seconds in sweep:
        mark = " **←**" if lam == best_lam else ""
        lines.append(f"| {lam:g} | {acc:.3f} | {f1:.3f} | {j_final:.4f} | {seconds:.1f} s{mark} |")
    lines += [
        "",
        "## Métricas del modelo final (λ elegido)",
        "",
        "| Conjunto | exactitud | macro-F1 | MSE one-hot | R² one-hot |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, rep in reports.items():
        lines.append(f"| {name} | {rep['accuracy']:.3f} | {rep['macro_f1']:.3f} | {rep['mse']:.4f} | {rep['r2']:.3f} |")
    lines += [
        "",
        f"Brecha exactitud train − test: **{100 * gap:.1f} puntos**.",
        "",
        "## Comparaciones en test",
        "",
        "| Modelo | exactitud | macro-F1 |",
        "|---|---:|---:|",
        f"| Clase mayoritaria (`007`) | {baseline_acc:.3f} | — |",
        f"| Sensor 1 solo ({ablation['n_features']} caract., mismo λ) | {ablation['accuracy']:.3f} | {ablation['macro_f1']:.3f} |",
        f"| **Ambos sensores ({len(model.feature_names)} caract.)** | **{te['accuracy']:.3f}** | **{te['macro_f1']:.3f}** |",
        "",
        "## Recall, precisión y F1 por clase (test)",
        "",
        "| Actividad | Ejercicio | n | recall | precisión | F1 |",
        "|---|---|---:|---:|---:|---:|",
    ]
    pc, cm = te["per_class"], te["confusion"]
    for c in range(N_CLASSES):
        lines.append(f"| `{c:03d}` | {MOVEMENT_NAMES[c]} | {int(cm[c].sum())} | "
                     f"{pc['recall'][c]:.2f} | {pc['precision'][c]:.2f} | {pc['f1'][c]:.2f} |")
    worst = np.argsort(pc["recall"])[:3]
    best = np.argsort(pc["recall"])[::-1][:3]
    lines += [
        "",
        f"Más difíciles (recall): {', '.join(f'`{c:03d}` ({pc['recall'][c]:.2f})' for c in worst)}. "
        f"Más fáciles: {', '.join(f'`{c:03d}` ({pc['recall'][c]:.2f})' for c in best)}.",
        "",
        "## Matriz de confusión (test; filas = real, columnas = predicha)",
        "",
        "| real \\ pred | " + " | ".join(f"`{m}`" for m in MOVEMENTS) + " |",
        "|---|" + "---:|" * N_CLASSES,
    ]
    for i in range(N_CLASSES):
        lines.append(f"| `{MOVEMENTS[i]}` | " + " | ".join(
            f"**{cm[i, j]}**" if i == j else (str(cm[i, j]) if cm[i, j] else "·") for j in range(N_CLASSES)) + " |")
    off = [(cm[i, j] + cm[j, i], i, j) for i in range(N_CLASSES) for j in range(i + 1, N_CLASSES)]
    off.sort(reverse=True)
    lines += [
        "",
        "Pares más confundidos (suma de ambos sentidos): " + ", ".join(
            f"`{i:03d}`↔`{j:03d}` ({n})" for n, i, j in off[:5]) + ".",
        "",
        "## Criterios de aceptación (sección 6 de la especificación)",
        "",
        "| Criterio | Valor | ¿Cumple? |",
        "|---|---:|:---:|",
    ]
    for label, ok, value in checks:
        lines.append(f"| {label} | {value} | {'✅' if ok else '❌'} |")
    lines += [
        "",
        "Figuras: `curva_aprendizaje.png`, `matriz_confusion.png`.",
        "",
        "> Nota: `Rehab_exercise` no trae ID de paciente, así que repeticiones de un mismo "
        "paciente pueden caer en train y en test. Las métricas son optimistas respecto a un "
        "paciente nunca visto.",
        "",
    ]
    RESULTS_DIR.mkdir(exist_ok=True)
    out = RESULTS_DIR / "metrics.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Métricas guardadas en: {out.relative_to(common.ROOT)}")


def n_rows_per_split(reports) -> list[int]:
    return [int(rep["confusion"].sum()) for rep in reports.values()]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--epochs", type=int, default=DEFAULT_EPOCHS)
    parser.add_argument("--lambdas", type=float, nargs="+", default=LAMBDA_GRID)
    parser.add_argument("--alpha", type=float, default=None, help="tasa de aprendizaje (por defecto 1/λ_max)")
    args = parser.parse_args()

    t_start = time.time()
    data = load_dataset()
    names = data["names"]
    X_tr, y_tr = subset(data, "train")
    X_va, y_va = subset(data, "val")
    X_te, y_te = subset(data, "test")
    print(f"Dataset: {len(data['y'])} filas × {len(names)} características "
          f"(train {len(y_tr)}, val {len(y_va)}, test {len(y_te)})\n")

    # 1. Barrido de λ en val.
    print("Barrido de λ (macro-F1 en val):")
    sweep, models = [], {}
    for lam in args.lambdas:
        model, f1, acc, seconds = fit_and_eval(X_tr, y_tr, X_va, y_va, lam, args.epochs, args.alpha, names)
        sweep.append((lam, f1, acc, model.history["train"][-1], seconds))
        models[lam] = model
        print(f"  λ = {lam:>6g}  exact. val = {acc:.3f}  macro-F1 val = {f1:.3f}  "
              f"J_train = {model.history['train'][-1]:.4f}  α = {model.alpha:.4f}  ({seconds:.1f} s)")
    best_lam = max(sweep, key=lambda t: t[1])[0]
    model = models[best_lam]
    print(f"\nλ elegido: {best_lam:g}")

    # 2. Evaluación única en test.
    reports = {
        "train": classification_report(y_tr, model.decision_function(X_tr)),
        "val": classification_report(y_va, model.decision_function(X_va)),
        "test": classification_report(y_te, model.decision_function(X_te)),
    }
    for name, rep in reports.items():
        print(f"  {name:5s}  exactitud = {rep['accuracy']:.3f}  macro-F1 = {rep['macro_f1']:.3f}  "
              f"MSE = {rep['mse']:.4f}  R² = {rep['r2']:.3f}")

    # 3. Línea base y ablación.
    majority = int(np.argmax(np.sum(np.arange(N_CLASSES)[None, :] == y_tr[:, None], axis=0)))
    baseline_acc = accuracy(y_te, np.full_like(y_te, majority))
    mask = sensor1_mask(names)
    abl_model, _, _, _ = fit_and_eval(X_tr[:, mask], y_tr, X_va[:, mask], y_va, best_lam, args.epochs,
                                      args.alpha, [n for n, m in zip(names, mask) if m])
    abl_pred = abl_model.predict(X_te[:, mask])
    ablation = {"accuracy": accuracy(y_te, abl_pred), "macro_f1": macro_f1(y_te, abl_pred),
                "n_features": int(mask.sum())}
    print(f"\n  línea base clase mayoritaria ({majority:03d}) en test: {baseline_acc:.3f}")
    print(f"  ablación sensor 1 solo en test: exactitud = {ablation['accuracy']:.3f}  "
          f"macro-F1 = {ablation['macro_f1']:.3f}")

    # 4. Persistencia.
    model.save(MODEL_FILE)
    print(f"\nModelo guardado en: {MODEL_FILE.relative_to(common.ROOT)}")
    plot_learning_curve(model)
    plot_confusion(reports["test"]["confusion"])
    write_metrics(sweep, best_lam, model, reports, baseline_acc, ablation, args.epochs, len(data["y"]))
    print(f"\nListo en {time.time() - t_start:.0f} s")


if __name__ == "__main__":
    main()
