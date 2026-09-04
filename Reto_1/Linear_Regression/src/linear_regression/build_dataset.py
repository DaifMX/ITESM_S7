"""CLI: `Data/*.npy` → `dataset/rehab_windows.csv` + `DICCIONARIO.md` + `meta.json`.

Una fila por repetición (sección 3 de la especificación). Reglas de descarte (2.4):

1. repetición totalmente en cero en cualquiera de los dos sensores;
2. longitud útil menor que `MIN_VALID_LEN` pasos en cualquiera de los dos sensores.

Uso (desde `Linear_Regression/`):

    uv run python -m linear_regression.build_dataset [--windows 4] [--seed 7]
"""

import argparse
import json
import time

import numpy as np

from . import common
from .common import (
    DATASET_CSV, DATASET_DICT, DATASET_DIR, DATASET_META, MIN_VALID_LEN, MODE_BINS,
    MOVEMENT_NAMES, MOVEMENTS, N_WINDOWS, SEED, SPLIT_FRACTIONS, channel_names, load_pair,
    valid_length,
)
from .features import feature_names, repetition_features
from .split import SPLIT_NAMES, stratified_split
from .stats import STAT_DESCRIPTIONS, STAT_NAMES

ID_COLUMNS = ["movement", "movement_name", "rep_index", "split"]


def _fmt(value: float) -> str:
    """Cuatro decimales, sin ceros de cola (sigue siendo el valor redondeado a 4)."""
    text = f"{value:.4f}".rstrip("0").rstrip(".")
    return "0" if text in ("-0", "") else text


def build(n_windows: int = N_WINDOWS, seed: int = SEED) -> dict:
    """Construye las filas de todas las repeticiones válidas y devuelve el resumen."""
    names = feature_names(n_windows)
    rows: list[np.ndarray] = []
    labels: list[int] = []
    rep_indices: list[int] = []
    discarded: dict[str, list[dict]] = {}
    per_movement_total: dict[str, int] = {}

    t0 = time.time()
    for movement in MOVEMENTS:
        reps_s1, reps_s2 = load_pair(movement)
        per_movement_total[movement] = len(reps_s1)
        for k in range(len(reps_s1)):
            len1, len2 = valid_length(reps_s1[k]), valid_length(reps_s2[k])
            reason = None
            if len1 == 0 or len2 == 0:
                reason = "repetición totalmente en cero"
            elif len1 < MIN_VALID_LEN or len2 < MIN_VALID_LEN:
                reason = f"longitud útil < {MIN_VALID_LEN} pasos"
            if reason is not None:
                discarded.setdefault(movement, []).append(
                    {"rep_index": k, "valid_len_s1": len1, "valid_len_s2": len2, "reason": reason})
                continue
            rows.append(repetition_features(reps_s1[k], reps_s2[k], n_windows))
            labels.append(int(movement))
            rep_indices.append(k)
        kept = len(reps_s1) - len(discarded.get(movement, []))
        print(f"  {movement} {MOVEMENT_NAMES[int(movement)]:<50} {kept:4d} filas "
              f"({len(discarded.get(movement, [])):2d} descartadas)")

    X = np.stack(rows)
    y = np.array(labels)
    reps = np.array(rep_indices)
    if not np.all(np.isfinite(X)):
        raise RuntimeError("hay valores no finitos en las características")
    split = stratified_split(y, seed=seed)
    print(f"\n{len(rows)} filas × {len(names)} características en {time.time() - t0:.1f} s")
    return {"X": X, "y": y, "rep": reps, "split": split, "names": names,
            "discarded": discarded, "totals": per_movement_total}


def write_csv(result: dict) -> None:
    """Escribe el CSV con las columnas de identificación seguidas de las características."""
    DATASET_DIR.mkdir(exist_ok=True)
    names = result["names"]
    int_cols = {i for i, n in enumerate(names) if n.startswith("valid_len_")}
    with open(DATASET_CSV, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(",".join(ID_COLUMNS + names) + "\n")
        for x, label, rep, split in zip(result["X"], result["y"], result["rep"], result["split"]):
            values = [str(int(v)) if i in int_cols else _fmt(v) for i, v in enumerate(x)]
            fh.write(",".join([str(label), MOVEMENT_NAMES[int(label)], str(rep), split] + values) + "\n")
    size_mb = DATASET_CSV.stat().st_size / 1e6
    print(f"CSV guardado en: {DATASET_CSV.relative_to(common.ROOT)} ({size_mb:.1f} MB)")


def write_dictionary(n_windows: int) -> None:
    """Diccionario de datos generado (no se edita a mano)."""
    lines = [
        "# Diccionario de datos · `rehab_windows.csv`",
        "",
        "Generado por `python -m linear_regression.build_dataset`. Una fila por repetición "
        "de un ejercicio del dataset REHAB (`Rehab_exercise`), vista por los dos grupos de "
        "sensores (`_1` IMU del miembro, `_2` guante).",
        "",
        "## Columnas de identificación",
        "",
        "| Columna | Tipo | Descripción |",
        "|---|---|---|",
        "| `movement` | int 0–15 | **Rótulo.** Actividad según la Tabla 3 del artículo |",
        "| `movement_name` | str | Nombre del ejercicio, sólo para lectura humana |",
        "| `rep_index` | int | Índice de la repetición dentro del `.npy` original (permite volver a la señal cruda) |",
        "| `split` | str | `train` / `val` / `test`, partición estratificada fija (semilla en `meta.json`) |",
        "",
        "## Columnas de características (842)",
        "",
        "| Columna | Tipo | Descripción |",
        "|---|---|---|",
        "| `valid_len_s1` | int | Pasos útiles del flujo `_1` (880 − relleno de ceros); 50 pasos = 1 s |",
        "| `valid_len_s2` | int | Pasos útiles del flujo `_2` |",
        f"| `s<sensor>_<canal>_w<k>_<estadístico>` | float | 12 canales × {n_windows + 1} ventanas × "
        f"{len(STAT_NAMES)} estadísticos = {12 * (n_windows + 1) * len(STAT_NAMES)} columnas (ver abajo) |",
        "",
        "### `<sensor>` y `<canal>`",
        "",
        "| Sensor | Canales | Qué es |",
        "|---|---|---|",
        f"| `s1` | {', '.join(f'`{c}`' for c in channel_names('1'))} | Ángulos de Euler (°) de las dos IMU del miembro que se ejercita: antebrazo/brazo en `000`–`012`, pantorrilla/muslo en `013`–`015` |",
        f"| `s2` | {', '.join(f'`{c}`' for c in channel_names('2'))} | Guante: flexión (°) de cada dedo y pitch de la muñeca |",
        "",
        "### `<k>`: ventana",
        "",
        "| Ventana | Tramo |",
        "|---|---|",
        "| `w0` | Toda la señal útil `x[0:L]` (`L` = `valid_len_s*` del sensor correspondiente) |",
    ]
    for k in range(1, n_windows + 1):
        lines.append(f"| `w{k}` | Tramo {k} de {n_windows}: `x[round(({k}-1)·L/{n_windows}) : round({k}·L/{n_windows})]` |")
    lines += [
        "",
        "Las ventanas se cortan sobre la longitud útil de **cada sensor por separado** (no "
        "sobre los 880 pasos), de modo que ninguna ventana contiene relleno de ceros.",
        "",
        "### `<estadístico>` (los 14, escritos a mano en `stats.py`)",
        "",
        "| Nombre | Definición |",
        "|---|---|",
    ]
    for stat in STAT_NAMES:
        lines.append(f"| `{stat}` | {STAT_DESCRIPTIONS[stat]} |")
    lines += [
        "",
        f"Ejemplo: `s1_pitch1_w2_median` es la mediana del pitch de la IMU 1 en el segundo cuarto "
        f"de la repetición; `s2_f3_w0_iqr` es el rango intercuartílico de la flexión del dedo medio "
        f"en toda la repetición. Los valores están redondeados a 4 decimales. La moda usa {MODE_BINS} bins.",
        "",
    ]
    DATASET_DICT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Diccionario guardado en: {DATASET_DICT.relative_to(common.ROOT)}")


def write_meta(result: dict, n_windows: int, seed: int) -> None:
    """Parámetros, filas descartadas, conteos y asignación de particiones (auditable)."""
    y, split, rep = result["y"], result["split"], result["rep"]
    counts = {}
    splits = {}
    for movement in MOVEMENTS:
        m = int(movement)
        mask = y == m
        counts[movement] = {"total": result["totals"][movement],
                            "kept": int(np.sum(mask)),
                            **{s: int(np.sum(mask & (split == s))) for s in SPLIT_NAMES}}
        splits[movement] = {s: [int(r) for r in rep[mask & (split == s)]] for s in SPLIT_NAMES}
    n_discarded = sum(len(v) for v in result["discarded"].values())
    meta = {
        "source": "REHAB · Rehab_exercise/d02_processed_data (doi:10.1038/s41597-026-07802-2)",
        "params": {"N_WINDOWS": n_windows, "MIN_VALID_LEN": MIN_VALID_LEN, "MODE_BINS": MODE_BINS,
                   "SEED": seed, "SPLIT_FRACTIONS": SPLIT_FRACTIONS, "decimals": 4},
        "n_rows": int(len(y)),
        "n_features": len(result["names"]),
        "n_discarded": n_discarded,
        "counts_per_movement": counts,
        "counts_per_split": {s: int(np.sum(split == s)) for s in SPLIT_NAMES},
        "discarded": result["discarded"],
        "splits": splits,
    }
    DATASET_META.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Meta guardada en: {DATASET_META.relative_to(common.ROOT)} "
          f"({n_discarded} repeticiones descartadas)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--windows", type=int, default=N_WINDOWS, help="número de ventanas (por defecto 4)")
    parser.add_argument("--seed", type=int, default=SEED, help="semilla de la partición")
    args = parser.parse_args()

    print(f"Construyendo dataset con {args.windows} ventanas (+ señal completa), semilla {args.seed}\n")
    result = build(args.windows, args.seed)
    write_csv(result)
    write_dictionary(args.windows)
    write_meta(result, args.windows, args.seed)
    print("\nFilas por partición:",
          {s: int(np.sum(result["split"] == s)) for s in SPLIT_NAMES})


if __name__ == "__main__":
    main()
