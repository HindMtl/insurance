# insurance_products/mixed_insurance/endowment_insurance.py

from core.annuities import a_due, nEx
from insurance_products.death_insurance.term_life import A_term


# ═══════════════════════════════════════════════════════════
# APV — BUILDING BLOCK
# ═══════════════════════════════════════════════════════════

def A_endow(lx, v, x, n):
    """
    APV of endowment insurance of 1 on (x) over n years.
    A_{x:n} = A¹_{x:n} + nEx

    Decomposition:
    - A¹_{x:n} : term life  — pays 1 if death before n
    - nEx      : pure endow — pays 1 if alive at n

    The insurer pays in all cases.

    Parameters
    ----------
    lx : np.ndarray
    v  : float      discount factor
    x  : int        age at issue
    n  : int        term (years)
    """
    return A_term(lx, v, x, n) + nEx(lx, v, x, n)


# ═══════════════════════════════════════════════════════════
# PRICING
# ═══════════════════════════════════════════════════════════

def price_single(lx, v, x, n, C=1):
    """
    Single premium — endowment insurance.
    Π = C * A_{x:n}
      = C * (A¹_{x:n} + nEx)
    """
    return C * A_endow(lx, v, x, n)


def price_periodic(lx, v, x, n, C=1):
    """
    Annual premium — endowment insurance.
    P = C * A_{x:n} / ä_{x:n}
    """
    return C * A_endow(lx, v, x, n) / a_due(lx, v, x, n)


# ═══════════════════════════════════════════════════════════
# RESERVING
# ═══════════════════════════════════════════════════════════

def reserve_single(lx, v, x, n, t, C=1):
    """
    Prospective reserve at t — single premium.
    tV = C * A_{x+t : n-t}
    """
    return C * A_endow(lx, v, x + t, n - t)


def reserve_periodic(lx, v, x, n, t, C=1):
    """
    Prospective reserve at t — periodic premium.
    tV = C * A_{x+t : n-t} - P * ä_{x+t : n-t}

    Boundary conditions:
    - 0V = 0  (equivalence principle)
    - nV = C  (benefit certain at maturity)
    """
    P = price_periodic(lx, v, x, n, C)
    return C * A_endow(lx, v, x + t, n - t) - P * a_due(lx, v, x + t, n - t)