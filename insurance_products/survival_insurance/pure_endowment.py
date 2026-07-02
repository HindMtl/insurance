# contracts/endowment_pure.py

from core.mortality import tpx
from core.annuities import a_due, nEx

# ═══════════════════════════════════════════════════════════
# PRICING
# ═══════════════════════════════════════════════════════════
def price_single(lx, v, x, n, C=1):
    """
    Single premium — pure endowment.
    Π = C * nEx

    Parameters
    ----------
    C : float   benefit paid at maturity if alive
    """
    return C * nEx(lx, v, x, n)



def price_periodic(lx, v, x, n, C=1):
    """
    Annual premium — pure endowment.
    P = C * nEx / ä_{x:n}

    Premiums paid over n years.
    If insured dies before n, premiums stop and nothing is paid
    (basic form — no death benefit).
    """
    return C * nEx(lx, v, x, n) / a_due(lx, v, x, n)


# ═══════════════════════════════════════════════════════════
# RESERVING
# ═══════════════════════════════════════════════════════════

def reserve_single(lx, v, x, n, t, C=1):
    """
    Prospective reserve at t — single premium.
    tV = C * (n-t)E_{x+t}
       = C * v^(n-t) * (n-t)P_{x+t}

    Reserve grows steadily toward C as t → n.
    On prior death: reserve released to insurer (no death benefit).

    Parameters
    ----------
    t : int     time elapsed since issue (t <= n)
    """
    return C * nEx(lx, v, x + t, n - t)


def reserve_periodic(lx, v, x, n, t, C=1):
    """
    Prospective reserve at t — periodic premium.
    tV = C * (n-t)E_{x+t} - P * ä_{x+t : n-t}

    Parameters
    ----------
    t : int     time elapsed since issue (t <= n)
    """
    P = price_periodic(lx, v, x, n, C)
    return C * nEx(lx, v, x + t, n - t) - P * a_due(lx, v, x + t, n - t)
