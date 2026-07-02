# contracts/decreasing_term.py

from core.mortality import tpx, kqx
from core.annuities import a_due
from insurance_products.death_insurance.term_life import A_term


# ═══════════════════════════════════════════════════════════
# APV
# ═══════════════════════════════════════════════════════════

def A_decreasing(lx, v, x, n):
    """
    APV of n-year decreasing term life insurance of 1 on (x).
    Benefit in year k+1 = (n-k)/n, paid mid-year (UDD).
    """
    return sum(
        v**(k + 0.5) * ((n - k) / n) * kqx(lx, x, k)
        for k in range(n)
    )

# ═══════════════════════════════════════════════════════════
# PRICING
# ═══════════════════════════════════════════════════════════

def price_single(lx, v, x, n, C=1):
    """
    Single premium — decreasing term life.
    Π = C * DA¹_{x:n}
    """
    return C * A_decreasing(lx, v, x, n)


def price_periodic(lx, v, x, n, C=1):
    """
    Annual premium — decreasing term life.
    P = C * DA¹_{x:n} / ä_{x:n}

    Note: premiums are constant even though the benefit decreases.
    """
    return C * A_decreasing(lx, v, x, n) / a_due(lx, v, x, n)


# ═══════════════════════════════════════════════════════════
# RESERVING
# ═══════════════════════════════════════════════════════════

def reserve_single(lx, v, x, n, t, C=1):
    """
    Prospective reserve at t — single premium.
    tV = C * DA¹_{x+t : n-t}

    The remaining benefit at t is still (n-k)/n of the ORIGINAL C,
    so we recompute A_decreasing from x+t with remaining term n-t,
    but rescale to reflect that the benefit has already decreased.

    At time t, death in year k+1 from now pays C*(n-t-k)/(n) not C*(n-t-k)/(n-t).
    """
    return sum(
        C * v**(k+1) * ((n - t - k) / n) * kqx(lx, x + t, k)
        for k in range(n - t)
    )


def reserve_periodic(lx, v, x, n, t, C=1):
    """
    Prospective reserve at t — periodic premium.
    tV = APV(future decreasing benefits) - P * ä_{x+t : n-t}
    """
    P      = price_periodic(lx, v, x, n, C)
    apv_b  = reserve_single(lx, v, x, n, t, C)   # reuses APV of future benefits
    return apv_b - P * a_due(lx, v, x + t, n - t)


# ═══════════════════════════════════════════════════════════
# USEFUL IDENTITY
# ═══════════════════════════════════════════════════════════

def check_identity(lx, v, x, n):
    """
    Verify the classical identity:
    DA¹_{x:n} + IA¹_{x:n} = (n+1) * A¹_{x:n}

    where IA¹_{x:n} is the increasing term insurance
    with benefit k+1 in year k+1.
    """
    DA = A_decreasing(lx, v, x, n) * n     # scale back to integer benefits
    IA = sum(
        (k+1) * v**(k+1) * kqx(lx, x, k)
        for k in range(n)
    )
    standard = (n + 1) * A_term(lx, v, x, n)
    print(f"DA¹ + IA¹ = {DA + IA:.6f}")
    print(f"(n+1)*A¹  = {standard:.6f}")
    print(f"Identity holds: {abs(DA + IA - standard) < 1e-10}")