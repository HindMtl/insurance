# contracts/endowment_contre_assurance.py

from core.mortality import tpx, kqx
from core.annuities import a_due, nEx
from insurance_products.death_insurance.term_life import IA_term


# ═══════════════════════════════════════════════════════════
# APV — BUILDING BLOCKS
# ═══════════════════════════════════════════════════════════


# ═══════════════════════════════════════════════════════════
# PRICING
# ═══════════════════════════════════════════════════════════

def price_single(lx, v, x, n, C=1):
    """
    Single premium — pure endowment with contre-assurance.
    On prior death: single premium Π returned to beneficiary.

    The death benefit is constant = Π (the single premium paid).
    This is simply an endowment insurance:
    Π = C * nEx + Π * A¹_{x:n}

    Solving for Π:
    Π * (1 - A¹_{x:n}) = C * nEx
    Π = C * nEx / (1 - A¹_{x:n})

    Parameters
    ----------
    C : float   benefit paid at maturity if alive
    """
    from insurance_products.death_insurance.term_life import A_term
    A1 = A_term(lx, v, x, n)
    return C * nEx(lx, v, x, n) / (1 - A1)


def price_periodic(lx, v, x, n, C=1):
    """
    Annual premium P — pure endowment with contre-assurance.
    On prior death in year k+1: (k+1) * P returned to beneficiary.

    Equivalence principle:
    P * ä_{x:n} = C * nEx + P * IA¹_{x:n}

    Solving for P:
    P * (ä_{x:n} - IA¹_{x:n}) = C * nEx
    P = C * nEx / (ä_{x:n} - IA¹_{x:n})

    Parameters
    ----------
    C : float   benefit paid at maturity if alive
    """
    num   = C * nEx(lx, v, x, n)
    denom = a_due(lx, v, x, n) - IA_term(lx, v, x, n)
    return num / denom


# ═══════════════════════════════════════════════════════════
# RESERVING
# ═══════════════════════════════════════════════════════════

def reserve_single(lx, v, x, n, t, C=1):
    """
    Prospective reserve at t — single premium.
    tV = C * (n-t)E_{x+t} + Π * A¹_{x+t : n-t}

    Two components:
    - pure endowment still owed at maturity
    - return of single premium if death occurs before n

    Parameters
    ----------
    t : int     time elapsed since issue (t <= n)
    """
    from insurance_products.death_insurance.term_life import A_term
    PI    = price_single(lx, v, x, n, C)
    apv_surv  = C  * nEx(lx, v, x + t, n - t)
    apv_death = PI * A_term(lx, v, x + t, n - t)
    return apv_surv + apv_death


def reserve_periodic(lx, v, x, n, t, C=1):
    """
    Prospective reserve at t — periodic premium.
    tV = C * (n-t)E_{x+t}
         + P * IA¹_{x+t : n-t}    (contre-assurance: future premiums returned)
         + P * t * A¹_{x+t : n-t} (past premiums already paid, also returned)
         - P * ä_{x+t : n-t}      (future premiums still to be received)

    Simplified:
    tV = C * (n-t)E_{x+t}
         + P * (t * A¹_{x+t:n-t} + IA¹_{x+t:n-t})
         - P * ä_{x+t : n-t}

    Explanation of the death benefit at time t:
    If death occurs in year k+1 from now, beneficiary receives
    ALL premiums paid = past (t premiums) + future (k+1 premiums)
    = (t + k + 1) * P
    So the APV of the death benefit splits into:
    - t * P * A¹_{x+t:n-t}   for the t premiums already paid
    - P * IA¹_{x+t:n-t}      for the future premiums yet to be paid

    Parameters
    ----------
    t : int     time elapsed since issue (t <= n)
    """
    from insurance_products.death_insurance.term_life import A_term
    P         = price_periodic(lx, v, x, n, C)
    apv_surv  = C * nEx(lx, v, x + t, n - t)
    apv_past  = P * t * A_term(lx, v, x + t, n - t)
    apv_fut   = P * IA_term(lx, v, x + t, n - t)
    apv_prem  = P * a_due(lx, v, x + t, n - t)
    return apv_surv + apv_past + apv_fut - apv_prem