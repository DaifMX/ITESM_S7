"""Paso 4: corrobora que la estructura de Rehab_exercise corresponde con el artículo.

Artículo: "A wearable sensor-based kinematic dataset collected under standardized
rehabilitation tasks from 120 post-stroke patients", Scientific Data (2026),
doi:10.1038/s41597-026-07802-2 (dataset REHAB).

Lo que el artículo declara para Rehab_exercise/d02_processed_data:
  - archivos <movementID>_<sensorID>.npy con movementID 000-015 (16 ejercicios)
    y sensorID 1 o 2  ->  32 archivos
  - dimensiones d x 880 x 6 (d = repeticiones, 880 pasos de tiempo, 6 canales)
  - 4,616 muestras en total, entre 212 y 385 por movimiento
  - muestreo a 50 Hz; señales truncadas o rellenadas con ceros hasta 880 puntos
  - sensorID 1 = S1+S2 / S3+S4 -> (Pitch1, Yaw1, Roll1, Pitch2, Yaw2, Roll2)
  - sensorID 2 = S5 (guante)   -> (f1, f2, f3, f4, f5, pitch3)
  - preprocesamiento: media móvil (ventana 10) y normalización de media cero
"""

from pathlib import Path

import numpy as np

DATA_DIR = Path(__file__).resolve().parents[3] / "Data"
FS_HZ = 50
N_STEPS = 880
N_CHANNELS = 6
MOVEMENTS = [f"{i:03d}" for i in range(16)]
SENSORS = ["1", "2"]


def _check(label: str, expected, observed) -> bool:
    ok = expected == observed
    print(f"  [{'OK ' if ok else 'DIF'}] {label}: artículo={expected} datos={observed}")
    return ok


def _trailing_zero_steps(sample: np.ndarray) -> int:
    """Pasos de tiempo rellenados con ceros al final de una repetición."""
    silent = np.all(sample == 0, axis=1)
    n = 0
    while n < len(silent) and silent[-1 - n]:
        n += 1
    return n


def main() -> None:
    files = sorted(DATA_DIR.glob("*.npy"))
    print(f"Carpeta: {DATA_DIR}\n")

    print("1) Nomenclatura y número de archivos")
    _check("archivos .npy", 32, len(files))
    _check("movementIDs", MOVEMENTS, sorted({f.stem.split("_")[0] for f in files}))
    _check("sensorIDs", SENSORS, sorted({f.stem.split("_")[1] for f in files}))

    print("\n2) Dimensiones d x 880 x 6")
    shapes = {m: {s: np.load(DATA_DIR / f"{m}_{s}.npy").shape for s in SENSORS} for m in MOVEMENTS}
    for m in MOVEMENTS:
        print(f"  {m}: sensor1={shapes[m]['1']}  sensor2={shapes[m]['2']}")
    _check(
        "todas (d, 880, 6)",
        True,
        all(sh[1:] == (N_STEPS, N_CHANNELS) for v in shapes.values() for sh in v.values()),
    )
    _check("d igual en sensor 1 y 2", True, all(v["1"][0] == v["2"][0] for v in shapes.values()))

    reps = [shapes[m]["1"][0] for m in MOVEMENTS]
    print("\n3) Conteo de repeticiones")
    _check("total de muestras", 4616, sum(reps))
    _check("rango de d por movimiento", (212, 385), (min(reps), max(reps)))
    print(f"  media de d = {np.mean(reps):.1f}")
    print(f"  880 pasos a {FS_HZ} Hz = {N_STEPS / FS_HZ:.1f} s por repetición")

    print("\n4) Semántica de los canales (movimiento 000)")
    for s in SENSORS:
        a = np.load(DATA_DIR / f"000_{s}.npy")
        lo, hi = a.min(axis=(0, 1)), a.max(axis=(0, 1))
        print(f"  sensor {s}: min={np.round(lo, 1)}")
        print(f"             max={np.round(hi, 1)}")
    a1 = np.load(DATA_DIR / "000_1.npy")
    a2 = np.load(DATA_DIR / "000_2.npy")
    _check("sensor 1: 6 canales con signo (ángulos de Euler)", 6, int((a1.min(axis=(0, 1)) < 0).sum()))
    _check("sensor 2: 5 canales no negativos (flexión f1-f5)", 5, int((a2.min(axis=(0, 1)) >= 0).sum()))

    print("\n5) Relleno con ceros hasta 880")
    for s in SENSORS:
        a = np.load(DATA_DIR / f"000_{s}.npy")
        pad = np.array([_trailing_zero_steps(rep) for rep in a])
        print(f"  sensor {s}: {(pad > 0).sum()}/{len(pad)} repeticiones rellenadas, "
              f"máximo {pad.max()} pasos ({pad.max() / FS_HZ:.1f} s)")

    print("\n6) Normalización de media cero")
    valid_means = []
    for rep in a1:
        n = N_STEPS - _trailing_zero_steps(rep)
        valid_means.append(rep[:n].mean(axis=0))
    valid_means = np.abs(np.array(valid_means))
    print(f"  |media| por repetición y canal: mediana={np.median(valid_means):.2f} "
          f"máximo={valid_means.max():.2f}")
    _check("media cero por repetición", True, bool(np.median(valid_means) < 1))


if __name__ == "__main__":
    main()
