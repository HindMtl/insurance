# contracts/reversion.py
#
# Product description:
# - Annuity C paid to (x) while alive
# - After (x)'s death: annuity alpha*C paid to (y) for life
#
# Total APV:
# Π = C * ä_x  +  alpha * C * (ä_y - ä_xy)
#   = C * ä_x  +  alpha * C * ä_{x|y}
#
# Assumes independence between lifetimes of (x) and (y)

from core.annuities       import a_due, a_joint, a_reversionary, nEx
from insurance_products.death_insurance.whole_life import A_whole


# ═══════════════════════════════════════════════════════════
# BUILDING BLOCKS — JOINT LIFE
# ═══════════════════════════════════════════════════════════



# ═══════════════════════════════════════════════════════════
# PRICING
# ═══════════════════════════════════════════════════════════


def price_single(lx, lx_y, v, x, y, Cx=1, alpha=0.5, immediate=False):
    """
    Single premium — pension with reversionary annuity.
    Π = C * ä_x  +  alpha * C * ä_{x|y}
      = C * ä_x  +  alpha * C * (ä_y - ä_{xy})

    Parameters
    ----------
    x     : int     age of insured (x)
    y     : int     age of beneficiary (y)
    C    : float   annual pension to (x) €/yr
    alpha : float   reversion rate (0.5 = 50% to y after x dies)
    """
    ax    = a_due(lx, v, x, immediate=immediate)
    a_rev = a_reversionary(lx, lx_y, v, x, y, immediate=immediate)
    return Cx * ax + alpha * Cx * a_rev

def price_periodic(lx, lx_y, v, x, y, Cx=1, alpha=0.5, immediate=False):
    """
    Annual premium — pension with reversionary annuity.
    Premiums paid on joint life ä_{xy}.

    P = [C * ä_x + alpha * C * ä_{x|y}] / ä_{xy}

    Premiums stop at first death:
    - if (x) dies first → reversion triggers, premiums stop
    - if (y) dies first → reversion lapses, premiums stop

    Parameters
    ----------
    x     : int     age of insured (x)
    y     : int     age of beneficiary (y)
    C    : float   annual pension to (x) €/yr
    alpha : float   reversion rate
    """
    apv  = price_single(lx, lx_y, v, x, y, Cx, alpha, immediate=immediate)
    a_xy = a_joint(lx, lx_y, v, x, y, immediate=immediate)
    return apv / a_xy


# ═══════════════════════════════════════════════════════════
# RESERVING
# ═══════════════════════════════════════════════════════════

def reserve_joint(lx, lx_y, v, x, y, t, Cx, alpha, single=False, immediate=False):
    """
    Prospective reserve at t — both (x) and (y) still alive.

    Single premium:
        tV = Cx * ä_{x+t} + alpha * Cx * (ä_{y+t} - ä_{(x+t)(y+t)})

    Periodic premium:
        tV = Cx * ä_{x+t} + alpha * Cx * (ä_{y+t} - ä_{(x+t)(y+t)})
             - P * ä_{(x+t)(y+t)}

    Parameters
    ----------
    t         : int    time elapsed since issue
    single    : bool   True = single premium, False = periodic (default)
    immediate : bool   True = annuity-immediate, False = annuity-due (default)
    """
    xt, yt = x + t, y + t
    ax_t   = a_due(lx, v, xt, immediate=immediate)
    a_rev  = a_reversionary(lx, lx_y, v, xt, yt, immediate=immediate)
    a_xy   = a_joint(lx, lx_y, v, xt, yt, immediate=immediate)

    apv_benefits = Cx * ax_t + alpha * Cx * a_rev

    if single:
        return apv_benefits
    else:
        P = price_periodic(lx, lx_y, v, x, y, Cx, alpha, immediate=immediate)
        return apv_benefits - P * a_xy


def reserve_reversion_triggered(lx_y, v, y, t, Cx, alpha, single=False, immediate=False):
    """
    Prospective reserve at t — (x) is dead, (y) still alive.
    Reversion has triggered. No more premiums.

    tV = alpha * Cx * ä_{y+t}

    Parameters
    ----------
    t         : int    time elapsed since issue
    single    : bool   included for consistency, no effect here
    immediate : bool   True = annuity-immediate, False = annuity-due (default)
    """
    return alpha * Cx * a_due(lx_y, v, y + t, immediate=immediate)


def reserve_reversion_lapsed(lx, v, x, t, Cx, single=False, immediate=False):
    """
    Prospective reserve at t — (y) is dead, (x) still alive.
    Reversion will never trigger. Premiums stopped at (y)'s death.
    (x) receives pension Cx for remaining life — fully paid-up.

    tV = Cx * ä_{x+t}

    Parameters
    ----------
    t         : int    time elapsed since issue
    single    : bool   included for consistency, no effect here
    immediate : bool   True = annuity-immediate, False = annuity-due (default)
    """
    return Cx * a_due(lx, v, x + t, immediate=immediate)

#reversion plural case. Design 1 simple Independent reversions (each gets their own share) Π=Cx​⋅a¨x​+α⋅Cx​⋅a¨x∣y​+α⋅Cx​⋅a¨x∣z​
#Design 2 — Last-survivor reversion (the share passes between y and z) Π=Cx​⋅a¨x​+α⋅Cx​⋅(a¨yz​​−a¨xyz​​)

def price_single_two_beneficiaries(lx, lx_y, lx_z, v, x, y, z, Cx=1, alpha=0.5):
    """
    Single premium — pension with TWO independent reversionary annuities.
    Each beneficiary (y) and (z) gets alpha*Cx independently after (x) dies.

    Π = Cx * ä_x + alpha*Cx * ä_{x|y} + alpha*Cx * ä_{x|z}

    Parameters
    ----------
    y, z  : int     ages of the two beneficiaries
    alpha : float   reversion rate, applied to EACH beneficiary independently
    """
    ax     = a_due(lx, v, x)
    a_rev_y = a_reversionary(lx, lx_y, v, x, y)
    a_rev_z = a_reversionary(lx, lx_z, v, x, z)
    return Cx * ax + alpha * Cx * a_rev_y + alpha * Cx * a_rev_z


def price_periodic_two_beneficiaries(lx, lx_y, lx_z, v, x, y, z, Cx=1, alpha=0.5):
    """
    Annual premium — pension with TWO independent reversionary annuities.
    Premiums paid while (x) is alive (since each reversion is independent,
    premium-paying life is (x) alone, not a joint life).

    P = Π / ä_x
    """
    PI = price_single_two_beneficiaries(lx, lx_y, lx_z, v, x, y, z, Cx, alpha)
    return PI / a_due(lx, v, x)


def reserve_two_beneficiaries(lx, lx_y, lx_z, v, x, y, z, t, Cx=1, alpha=0.5,
                               single=False):
    """
    Prospective reserve at t — (x) still alive (both beneficiaries' status
    doesn't matter for premium continuation since premiums depend only on x).

    tV = Cx * ä_{x+t} + alpha*Cx*(ä_{x+t|y+t} + ä_{x+t|z+t}) - P * ä_{x+t}
    """
    xt, yt, zt = x + t, y + t, z + t
    ax_t    = a_due(lx, v, xt)
    a_rev_y = a_reversionary(lx, lx_y, v, xt, yt)
    a_rev_z = a_reversionary(lx, lx_z, v, xt, zt)

    apv_benefits = Cx * ax_t + alpha * Cx * (a_rev_y + a_rev_z)

    if single:
        return apv_benefits
    else:
        P = price_periodic_two_beneficiaries(lx, lx_y, lx_z, v, x, y, z, Cx, alpha)
        return apv_benefits - P * ax_t


def reserve_x_dead(lx_y, lx_z, v, y, z, t, Cx=1, alpha=0.5):
    """
    Prospective reserve at t — (x) is dead.
    Both reversions are now independent ongoing annuities — no more
    interaction with (x)'s survival.

    tV = alpha*Cx * ä_{y+t} + alpha*Cx * ä_{z+t}
    """
    return alpha * Cx * (a_due(lx_y, v, y + t) + a_due(lx_z, v, z + t))

