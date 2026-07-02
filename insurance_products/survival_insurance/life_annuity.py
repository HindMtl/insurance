# contracts/annuity.py

from core.mortality import tpx
from core.annuities import a_due, nEx


# ═══════════════════════════════════════════════════════════
# APV — BUILDING BLOCKS
# ═══════════════════════════════════════════════════════════
def a_deferred(lx, v, x, m, immediate=False):
    """
    Deferred whole-life annuity-due.
    m|ä_x = v^m * mPx * ä_{x+m}
           = nEx * ä_{x+m}

    Payments start at age x+m, paid while (x) alive.

    Parameters
    ----------
    m : int     deferral period (years)
    """
    return nEx(lx, v, x, m) * a_due(lx, v, x + m, immediate=immediate)


def a_immediate(lx, v, x, n=None):
    """
    Annuity-immediate: payments at end of year.
    a_x = sum(k=1 to n) v^k * kpx
    = ä_x - 1  (one less payment at k=0)

    Parameters
    ----------
    lx : np.ndarray
    v  : float      discount factor
    x  : int        age at issue
    n  : int        term (None = whole life)
    """
    omega = len(lx) - 1
    if n is None:
        n = omega - x
    return sum(v**k * tpx(lx, x, k) for k in range(1, n + 1))




def a_deferred_temporary(lx, v, x, m, n, immediate=False):
    """
    Deferred temporary annuity-due.
    m|ä_{x:n} = nEx(m) * ä_{x+m:n}

    Payments start at age x+m and last at most n years.
    Stops at death or after n payments, whichever comes first.

    Parameters
    ----------
    x         : int     age at issue
    m         : int     deferral period (years)
    n         : int     payment period (years) after deferral
    immediate : bool    annuity-immediate if True
    """
    return nEx(lx, v, x, m) * a_due(lx, v, x + m, n=n, immediate=immediate)


# ═══════════════════════════════════════════════════════════
# PRICING — IMMEDIATE WHOLE-LIFE ANNUITY
# ═══════════════════════════════════════════════════════════

def price_whole_life_single(lx, v, x, C=1, immediate=False):
    """
    Single premium — immediate whole-life annuity-due.
    Π = C * ä_x

    No periodic premium exists for an immediate annuity —
    the contract converts a lump sum into an income stream.

    Parameters
    ----------
    C : float   annual annuity amount (€/yr)
    """
    return C * a_due(lx, v, x, immediate=immediate)


# ═══════════════════════════════════════════════════════════
# PRICING — DEFERRED ANNUITY
# ═══════════════════════════════════════════════════════════

def price_deferred_single(lx, v, x, m, C=1, immediate=False):
    """
    Single premium — deferred whole-life annuity.
    Π = C * m|ä_x

    Parameters
    ----------
    m : int     deferral period (years)
    C : float   annual annuity amount (€/yr)
    """
    return C * a_deferred(lx, v, x, m, immediate=immediate)


def price_deferred_periodic(lx, v, x, m, C=1, immediate=False):
    """
    Annual premium during deferral — deferred whole-life annuity.
    P = C * m|ä_x / ä_{x:m}
    Premiums paid only during the deferral period.

    Parameters
    ----------
    m : int     deferral period (years)
    """
    return C * a_deferred(lx, v, x, m, immediate=False) / a_due(lx, v, x, n=m, immediate=False)


# ═══════════════════════════════════════════════════════════
# PRICING — TEMPORARY ANNUITY
# ═══════════════════════════════════════════════════════════

def price_temporary_single(lx, v, x, n, C=1, immediate=False):
    """
    Single premium — temporary annuity-due (at most n years).
    Π = C * ä_{x:n}

    Parameters
    ----------
    n : int     maximum payment period (years)
    C : float   annual annuity amount (€/yr)
    """
    return C * a_due(lx, v, x, n, immediate=immediate)


# ═══════════════════════════════════════════════════════════
# RESERVING — IMMEDIATE WHOLE-LIFE ANNUITY
# ═══════════════════════════════════════════════════════════

def reserve_whole_life(lx, v, x, t, C=1, immediate=False):
    """
    Prospective reserve at t — immediate whole-life annuity (single premium).
    tV = C * ä_{x+t}

    Reserve decreases as insured ages (fewer expected payments).
    No premium term — single premium paid at t=0.

    Parameters
    ----------
    t : int     time elapsed since issue
    """
    return C * a_due(lx, v, x + t, immediate=immediate)


# ═══════════════════════════════════════════════════════════
# RESERVING — DEFERRED ANNUITY
# ═══════════════════════════════════════════════════════════

def reserve_deferred_single(lx, v, x, m, t, C=1, immediate=False):
    """
    Prospective reserve at t — deferred annuity (single premium).

    t <= m  (still in deferral):
        tV = C * (m-t)|ä_{x+t}

    t > m   (in payout phase):
        tV = C * ä_{x+t}

    Parameters
    ----------
    m : int     deferral period
    t : int     time elapsed since issue
    """
    if t <= m:
        return C * a_deferred(lx, v, x + t, m - t, immediate=immediate)
    else:
        return C * a_due(lx, v, x + t, immediate=immediate)


def reserve_deferred_periodic(lx, v, x, m, t, C=1, immediate=False):
    """
    Prospective reserve at t — deferred annuity (periodic premium).

    t <= m  (still in deferral, premiums still due):
        tV = C * (m-t)|ä_{x+t} - P * ä_{x+t : m-t}

    t > m   (in payout phase, no more premiums):
        tV = C * ä_{x+t}

    Parameters
    ----------
    m : int     deferral period
    t : int     time elapsed since issue
    """
    P = price_deferred_periodic(lx, v, x, m, C, immediate=immediate)
    if t <= m:
        apv_ben = C * a_deferred(lx, v, x + t, m - t, immediate=immediate)
        apv_prem = P * a_due(lx, v, x + t, n=m - t, immediate=immediate)
        return apv_ben - apv_prem
    else:
        return C * a_due(lx, v, x + t, immediate=immediate)


# ═══════════════════════════════════════════════════════════
# RESERVING — TEMPORARY ANNUITY
# ═══════════════════════════════════════════════════════════

def reserve_temporary(lx, v, x, n, t, C=1, immediate=False):
    """
    Prospective reserve at t — temporary annuity (single premium).
    tV = C * ä_{x+t : n-t}

    Parameters
    ----------
    n : int     maximum payment period
    t : int     time elapsed since issue (t < n)
    """
    return C * a_due(lx, v, x + t, n - t, immediate=immediate)

def reserve_deferred_temporary(lx, v, x, m, n, t, C=1, immediate=False):
    """
    Prospective reserve at t — deferred temporary annuity (single premium).

    t <= m  (still in deferral):
        tV = C * (m-t)|ä_{x+t:n}

    t > m   (in payout phase):
        tV = C * ä_{x+t : n-(t-m)}
    """
    if t <= m:
        return C * a_deferred_temporary(lx, v, x + t, m - t, n,
                                        immediate=immediate)
    else:
        remaining = n - (t - m)
        if remaining <= 0:
            return 0.0
        return C * a_due(lx, v, x + t, n=remaining, immediate=immediate)
