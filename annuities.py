from core.mortality import tpx


def a_due(lx, v, x, n=None, immediate=False):
    """
    Annuity-due
    """

    from core.mortality import tpx
    omega = len(lx) - 1
    if n is None:
        n = omega - x
    start = 1 if immediate else 0
    end   = n + 1 if immediate else n
    return sum(v**k * tpx(lx, x, k) for k in range(start, end))



def a_joint(lx, lx_y, v, x, y, immediate=False):
    """
    Joint life annuity-due: paid while both (x) and (y) alive.
    ä_{xy} = sum(k=0 to omega) v^k * kpx * kpy

    Assumes independence of lifetimes.

    Parameters
    ----------
    lx : np.ndarray   mortality table for (x)
    lx_y : np.ndarray   mortality table for (y)
    v    : float        discount factor
    x    : int          age of (x)
    y    : int          age of (y)
    """
    omega = min(len(lx) - x, len(lx_y) - y)
    from core.mortality import tpx
    start = 1 if immediate else 0
    end   = omega + 1 if immediate else omega
    return sum(
        v**k * tpx(lx, x, k) * tpx(lx_y, y, k)
        for k in range(start, end)
    )


def a_reversionary(lx, lx_y, v, x, y,  n=None, immediate=False):
    """
    Reversionary annuity-due: paid to (y) after death of (x).
    ä_{x|y} = ä_y - ä_{xy}

    Parameters
    ----------
    lx : np.ndarray   mortality table for (x)
    lx_y : np.ndarray   mortality table for (y)
    v    : float        discount factor
    x    : int          age of (x)
    y    : int          age of (y)
    """
    return a_due(lx_y, v, y, immediate=immediate) - a_joint(lx, lx_y, v, x, y, immediate=immediate)


def a_immediate(lx, v, x, n=None):
    """
    Annuity-immediate: payments at end of year.
    a_x = sum(k=1 to n) v^k * kpx
    Note: a_x = ä_x - 1  (one less payment at k=0)
    """
    omega = len(lx) - 1
    if n is None:
        n = omega - x
    return sum(v**k * tpx(lx, x, k) for k in range(1, n + 1))


def nEx(lx, v, x, n):
    """Pure endowment: nEx = v^n * nPx"""
    return v**n * tpx(lx, x, n)

