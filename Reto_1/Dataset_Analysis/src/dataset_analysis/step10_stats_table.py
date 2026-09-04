"""Paso 10: media y mediana por actividad para un canal del sensor 1.

Para cada uno de los 16 movimientos se concatenan todas sus repeticiones
(descartando el relleno de ceros, ver `common.concat_channel`) y se calculan la
media y la mediana del canal elegido. Salida: tabla de 16 filas × 2 columnas,
impresa como Markdown para pegarla en el README y guardada en `tables/`.

Canal por defecto: 0 -> Pitch1 (IMU S1, antebrazo), el mismo del paso 8.

Uso: uv run python -m dataset_analysis.step10_stats_table [canal]
"""

import sys

import numpy as np

from dataset_analysis.common import MOVEMENTS, ROOT, channel_names, concat_channel

SENSOR = "1"
CHANNEL = 0


def stats_por_actividad(channel: int, sensor: str = SENSOR) -> list[tuple[str, float, float, int]]:
    """(movimiento, media, mediana, n_muestras) para cada actividad."""
    filas = []
    for mov in MOVEMENTS:
        valores = concat_channel(mov, channel, sensor)
        filas.append((mov, float(valores.mean()), float(np.median(valores)), valores.size))
    return filas


def main() -> None:
    channel = int(sys.argv[1]) if len(sys.argv) > 1 else CHANNEL
    name = channel_names(SENSOR)[channel]
    filas = stats_por_actividad(channel)

    encabezado = (f"Sensor {SENSOR}, canal {channel} ({name}) — "
                  f"todas las repeticiones concatenadas, sin relleno de ceros")
    lineas = [
        f"| Actividad | Media ({name}, °) | Mediana ({name}, °) |",
        "|---|---:|---:|",
    ]
    lineas += [f"| {mov} | {media:.2f} | {mediana:.2f} |" for mov, media, mediana, _ in filas]

    print(encabezado)
    print()
    print("\n".join(lineas))

    medias = np.array([f[1] for f in filas])
    medianas = np.array([f[2] for f in filas])
    n = np.array([f[3] for f in filas])
    print(f"\nRango de las medias  : {medias.min():.2f}° (mov. {MOVEMENTS[medias.argmin()]})"
          f" a {medias.max():.2f}° (mov. {MOVEMENTS[medias.argmax()]})")
    print(f"Dispersión entre actividades (desv. de las 16 medias): {medias.std(ddof=0):.2f}°")
    print(f"Mayor |media − mediana|: {np.abs(medias - medianas).max():.2f}°"
          f" (mov. {MOVEMENTS[np.abs(medias - medianas).argmax()]}) → asimetría de la distribución")
    print(f"Muestras por actividad : {n.min():,} a {n.max():,} (total {n.sum():,})")

    out_dir = ROOT / "tables"
    out_dir.mkdir(exist_ok=True)
    out = out_dir / f"step10_media_mediana_s{SENSOR}_{name}.md"
    out.write_text(f"# {encabezado}\n\n" + "\n".join(lineas) + "\n")
    print(f"\nTabla guardada en: {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
