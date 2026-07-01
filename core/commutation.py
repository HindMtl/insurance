# core/commutation.py

import numpy as np

def compute_commutation(lx: np.ndarray, v: float, omega: int = 110) -> dict:
    """
    Computes commutation functions from lx and v.

    Returns dict with arrays:
    Dx, Cx, Mx, Nx, Rx — each indexed by age
    """
    ages = np.arange(len(lx))

    # dx = lx - lx+1 (deaths)
    dx = np.zeros(len(lx))
    dx[:-1] = lx[:-1] - lx[1:]
    dx[-1]  = lx[-1]

    # Dx = v^x * lx
    Dx = v**ages * lx

    # update Cx
    Cx = v**(ages + 0.5) * dx    #now v**(ages + 0.5)

    # Mx = sum from x to omega of Cx (reverse cumulative sum)
    Mx = np.cumsum(Cx[::-1])[::-1]

    # Nx = sum from x to omega of Dx (reverse cumulative sum)
    Nx = np.cumsum(Dx[::-1])[::-1]

    # Rx = sum from x to omega of Mx (reverse cumulative sum)
    Rx = np.cumsum(Mx[::-1])[::-1]

    return {"Dx": Dx, "Cx": Cx, "Mx": Mx, "Nx": Nx, "Rx": Rx}


def a_due_comm(comm: dict, x: int, n: int) -> float:
    """ä_{x:n} using commutation functions."""
    return (comm["Nx"][x] - comm["Nx"][x + n]) / comm["Dx"][x]


def A_term_comm(comm: dict, x: int, n: int) -> float:
    """A¹_{x:n} using commutation functions."""
    return (comm["Mx"][x] - comm["Mx"][x + n]) / comm["Dx"][x]


def nEx_comm(comm: dict, x: int, n: int) -> float:
    """nEx using commutation functions."""
    return comm["Dx"][x + n] / comm["Dx"][x]


def IA_term_comm(comm: dict, x: int, n: int) -> float:
    """IA¹_{x:n} using commutation functions."""
    return (comm["Rx"][x] - comm["Rx"][x + n] - n * comm["Mx"][x + n]) / comm["Dx"][x]