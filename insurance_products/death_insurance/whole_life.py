# contracts/whole_life.py
from core.annuities import a_due, nEx
from insurance_products.death_insurance.term_life import A_term
from core.mortality import kqx



# ═══════════════════════════════════════════════════════════
# APV — Actuarial Present Value
# ═══════════════════════════════════════════════════════════

def IA_whole(lx, v, x):
    """
    APV of increasing whole life insurance on (x).
    Benefit in year k+1 = k+1, paid mid-year (UDD).
    """
    omega = len(lx) - 1
    return sum((k + 1) * v**(k + 0.5) * kqx(lx, x, k) for k in range(omega - x))


def A_whole(lx, v, x):
    """APV of whole life insurance of 1 on (x). Mid-year (UDD)."""
    omega = len(lx) - 1
    return sum(v**(k + 0.5) * kqx(lx, x, k) for k in range(omega - x))



def A_deferred_whole(lx, v, x, m):
    """
    APV of deferred whole life insurance.
    Pays 1 if death occurs after age x+m, for the rest of life.
    m|A_x = mEx * A_{x+m}

    Parameters
    ----------
    m : int     deferral period (years)
    """
    return nEx(lx, v, x, m) * A_whole(lx, v, x + m)


def price_single(lx, v, x, C=1, m=0):
    """
    Single premium — whole life, with optional deferral.

    m=0 (default): standard whole life.
        Π = C * A_x

    m>0: deferred, with premium refund on early death.
        Π = C * m|A_x / (1 - A¹_{x:m})
    """
    if m == 0:
        return C * A_whole(lx, v, x)

    apv_main = C * A_deferred_whole(lx, v, x, m)
    #a1_def   = A_term(lx, v, x, m) - in case of a refund during deferral period
    return apv_main #/ (1 - a1_def) in case of a refund


def price_periodic(lx, v, x, C=1, m=0):
    """
    Annual premium — whole life, with optional deferral.

    m=0 (default): standard whole life pay.
        P = C * A_x / ä_x

    m>0: deferred, with premium refund on early death.
        P = C * m|A_x / (ä_x - A¹_{x:m})
    """
    if m == 0:
        return C * A_whole(lx, v, x) / a_due(lx, v, x)

    apv_main    = C * A_deferred_whole(lx, v, x, m)
    a_full      = a_due(lx, v, x)
    #a1_deferral = A_term(lx, v, x, m)-refund
    return apv_main / (a_full) #refund - a1_deferral)


def reserve_single(lx, v, x, t, C=1, m=0):
    """Prospective reserve at t — single premium, with optional deferral."""
    if m == 0:
        return C * A_whole(lx, v, x + t)

    PI = price_single(lx, v, x, C, m)
    if t < m:
        remaining_deferral = m - t
        apv_main   = C * A_deferred_whole(lx, v, x + t, remaining_deferral)
        #apv_refund = PI * A_term(lx, v, x + t, remaining_deferral)
        return apv_main #+ apv_refund in case of a refund
    else:
        return C * A_whole(lx, v, x + t)


def reserve_periodic(lx, v, x, t, C=1, m=0):
    """Prospective reserve at t — periodic premium, with optional deferral."""
    if m == 0:
        P = price_periodic(lx, v, x, C)
        return C * A_whole(lx, v, x + t) - P * a_due(lx, v, x + t)

    P = price_periodic(lx, v, x, C, m)
    if t < m:
        remaining_deferral = m - t
        apv_main   = C * A_deferred_whole(lx, v, x + t, remaining_deferral)
        #apv_refund = P * A_term(lx, v, x + t, remaining_deferral)
        apv_prem   = P * a_due(lx, v, x + t)
        return apv_main - apv_prem #+ apv_refund 
    else:
        apv_main = C * A_whole(lx, v, x + t)
        apv_prem = P * a_due(lx, v, x + t)
        return apv_main - apv_prem