"""Utilities for loading the MNIST dataset from IDX files."""

from pathlib import Path
import struct

import numpy as np


IMAGE_MAGIC = 2051
LABEL_MAGIC = 2049


def load_images(path: str | Path) -> np.ndarray:
    """Load an IDX image file as a writable ``(N, rows * columns)`` array."""
    path = Path(path)
    with path.open("rb") as file:
        header = file.read(16)
        assert len(header) == 16, f"Incomplete image header in {path}"
        magic, count, rows, columns = struct.unpack(">IIII", header)
        assert magic == IMAGE_MAGIC, (
            f"Invalid image magic number in {path}: {magic} (expected {IMAGE_MAGIC})"
        )
        data = np.frombuffer(file.read(), dtype=np.uint8)

    expected = count * rows * columns
    assert data.size == expected, (
        f"Invalid image data size in {path}: {data.size} (expected {expected})"
    )
    return data.reshape(count, rows * columns).copy()


def load_labels(path: str | Path) -> np.ndarray:
    """Load an IDX label file as a writable ``(N,)`` array."""
    path = Path(path)
    with path.open("rb") as file:
        header = file.read(8)
        assert len(header) == 8, f"Incomplete label header in {path}"
        magic, count = struct.unpack(">II", header)
        assert magic == LABEL_MAGIC, (
            f"Invalid label magic number in {path}: {magic} (expected {LABEL_MAGIC})"
        )
        data = np.frombuffer(file.read(), dtype=np.uint8)

    assert data.size == count, (
        f"Invalid label data size in {path}: {data.size} (expected {count})"
    )
    return data.copy()


def load_mnist(data_dir: str | Path) -> tuple[np.ndarray, ...]:
    """Return ``X_train, y_train, X_test, y_test`` from an MNIST directory."""
    data_dir = Path(data_dir)
    X_train = load_images(data_dir / "train-images.idx3-ubyte")
    y_train = load_labels(data_dir / "train-labels.idx1-ubyte")
    X_test = load_images(data_dir / "t10k-images.idx3-ubyte")
    y_test = load_labels(data_dir / "t10k-labels.idx1-ubyte")

    assert X_train.shape[0] == y_train.shape[0], "Train images/labels mismatch"
    assert X_test.shape[0] == y_test.shape[0], "Test images/labels mismatch"
    return X_train, y_train, X_test, y_test
