# contracts/term.py

from core.mortality import tpx, kqx
from core.annuities import a_due, nEx


# ═══════════════════════════════════════════════════════════
# APV
# ═══════════════════════════════════════════════════════════

def IA_term(lx, v, x, n):
    """
    APV of increasing term insurance on (x) over n years.
    Benefit in year k+1 = k+1, paid mid-year (UDD).

    IA¹_{x:n} = sum(k=0 to n-1) (k+1) * v^(k+1/2) * kpx * qx+k
    """
    return sum((k + 1) * v**(k + 0.5) * kqx(lx, x, k) for k in range(n))




def A_term(lx, v, x, n):
    """APV of n-year term life insurance of 1 on (x). Mid-year (UDD)."""
    return sum(v**(k +1/2)  *kqx(lx, x, k) for k in range(n))


def A_deferred_term(lx, v, x, m, n):
    """
    APV of deferred term insurance.
    Pays 1 if death occurs between age x+m and x+n.
    m|A¹_{x:n-m} = mEx * A¹_{x+m:n-m}

    Parameters
    ----------
    m : int     deferral period (years)
    n : int     total contract term (years)
    """
    return nEx(lx, v, x, m) * A_term(lx, v, x + m, n - m)


def price_single(lx, v, x, n, C=1, m=0):
    """
    Single premium — term life, with optional deferral.

    m=0 (default): standard term life, no deferral.
        Π = C * A¹_{x:n}

    m>0: deferred, with premium refund on early death.
        Π = C * m|A¹_{x:n-m} / (1 - A¹_{x:m})
    """
    if m == 0:
        return C * A_term(lx, v, x, n)

    apv_main = C * A_deferred_term(lx, v, x, m, n)
    #a1_def   = A_term(lx, v, x, m) - refund if t<m
    return apv_main # / (1 - a1_def)


def price_periodic(lx, v, x, n, C=1, m=0):
    """
    Annual premium — term life, with optional deferral.

    m=0 (default): standard term life.
        P = C * A¹_{x:n} / ä_{x:n}

    m>0: deferred, with premium refund on early death.
        P = C * m|A¹_{x:n-m} / (ä_{x:n} - A¹_{x:m})
    """
    if m == 0:
        return C * A_term(lx, v, x, n) / a_due(lx, v, x, n)

    apv_main    = C * A_deferred_term(lx, v, x, m, n)
    a_full      = a_due(lx, v, x, n)
    #a1_deferral = A_term(lx, v, x, m)
    return apv_main / (a_full) # - a1_deferral)


def reserve_single(lx, v, x, n, t, C=1, m=0):
    """Prospective reserve at t — single premium, with optional deferral."""
    if m == 0:
        return C * A_term(lx, v, x + t, n - t)

    PI = price_single(lx, v, x, n, C, m)
    if t < m:
        remaining_deferral = m - t
        apv_main   = C * A_deferred_term(lx, v, x + t, remaining_deferral, n - t)
        #apv_refund = PI * A_term(lx, v, x + t, remaining_deferral)
        return apv_main #+ apv_refund
    else:
        return C * A_term(lx, v, x + t, n - t)


def reserve_periodic(lx, v, x, n, t, C=1, m=0):
    """Prospective reserve at t — periodic premium, with optional deferral."""
    if m == 0:
        P = price_periodic(lx, v, x, n, C)
        return C * A_term(lx, v, x + t, n - t) - P * a_due(lx, v, x + t, n - t)

    P = price_periodic(lx, v, x, n, C, m)
    if t < m:
        remaining_deferral = m - t
        apv_main   = C * A_deferred_term(lx, v, x + t, remaining_deferral, n - t)
        #apv_refund = P * A_term(lx, v, x + t, remaining_deferral)
        apv_prem   = P * a_due(lx, v, x + t, n - t)
        return apv_main - apv_prem #+ apv_refund 
    else:
        apv_main = C * A_term(lx, v, x + t, n - t)
        apv_prem = P * a_due(lx, v, x + t, n - t)
        return apv_main - apv_prem

