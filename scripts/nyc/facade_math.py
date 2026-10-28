"""Image projective geometry; no GIS/runtime dependency for system Pillow CLI."""
import numpy as np


def homography(source, target):
    a, b = [], []
    for (x, y), (u, v) in zip(source, target):
        a.extend([[x, y, 1, 0, 0, 0, -u*x, -u*y],
                  [0, 0, 0, x, y, 1, -v*x, -v*y]])
        b.extend([u, v])
    if len(a) != 8 or not np.isfinite(a).all():
        raise ValueError("four finite corresponding points required")
    if np.linalg.matrix_rank(a) < 8:
        raise ValueError("degenerate image control polygon")
    return np.append(np.linalg.solve(a, b), 1).reshape((3, 3))
