# contracts/pension_contre_assurance.py
#
# Product description:
# - Annuity C paid to (x) while alive (immediate or deferred)
# - On death of (x): lump sum returned to (y) = total premiums paid
#
# Contre-assurance = return of premiums to (y) on (x)'s death
# This is a lump sum to (y), NOT a recurring annuity to (y)

from core.mortality import tpx, kqx
from core.annuities import a_due, nEx
from insurance_products.death_insurance.term_life import A_term, IA_term
from insurance_products.death_insurance.whole_life import A_whole, IA_whole

# ═══════════════════════════════════════════════════════════
# BUILDING BLOCKS
# ═══════════════════════════════════════════════════════════





# ═══════════════════════════════════════════════════════════
# CASE 1 — IMMEDIATE PENSION WITH CONTRE-ASSURANCE
# ═══════════════════════════════════════════════════════════
#
# (x) pays a single premium at t=0 and immediately receives
# the pension C per year for life.
# On (x)'s death: lump sum = single premium Π returned to (y).
#
# Equivalence:
# Π = C * ä_x  +  Π * A_x
#
# Solving for Π:
# Π * (1 - A_x) = C * ä_x
# Π = C * ä_x / (1 - A_x)
#
# Note: only single premium makes sense for immediate pension
# since (x) is already receiving income — no periodic premium.

def price_immediate_single(lx, v, x, C=1):
    """
    Single premium — immediate pension with contre-assurance.
    Π = C * ä_x / (1 - A_x)

    Parameters
    ----------
    x  : int    age at issue (pension starts immediately)
    C : float  annual pension amount (€/yr)
    """
    ax  = a_due(lx, v, x)
    Ax  = A_whole(lx, v, x)
    return C * ax / (1 - Ax)


def reserve_immediate_single(lx, v, x, t, C=1):
    """
    Prospective reserve at t — immediate pension, single premium.

    Two future obligations:
    1. Remaining pension to (x):       C * ä_{x+t}
    2. Return of Π to (y) on death:    Π  * A_{x+t}

    tV = C * ä_{x+t} + Π * A_{x+t}

    Parameters
    ----------
    t : int     time elapsed since issue
    """
    PI   = price_immediate_single(lx, v, x, C)
    ax_t = a_due(lx, v, x + t)
    Ax_t = A_whole(lx, v, x + t)
    return C * ax_t + PI * Ax_t


# ═══════════════════════════════════════════════════════════
# CASE 2 — DEFERRED PENSION WITH CONTRE-ASSURANCE
# ═══════════════════════════════════════════════════════════
#
# (x) pays premium P for m years (deferral period).
# After m years: pension C per year for life starts.
# On (x)'s death at any time: premiums paid so far returned to (y).
#
# Death during deferral (year k+1, k < m):
#   benefit to (y) = (k+1) * P   → increasing term → IA¹_{x:m}
#
# Death during pension phase (year k+1 from issue, k >= m):
#   benefit to (y) = m * P       → constant = total premiums paid
#                                 → m * P * deferred whole life
#
# Equivalence:
# P * ä_{x:m}  =  C * m|ä_x                   (pension)
#              +  P  * IA¹_{x:m}                (return during deferral)
#              +  m*P * (A_x - A¹_{x:m})        (return during pension phase)
#
# Solving for P:
# P * [ä_{x:m} - IA¹_{x:m} - m*(A_x - A¹_{x:m})] = C * m|ä_x
# P = C * m|ä_x / [ä_{x:m} - IA¹_{x:m} - m*(A_x - A¹_{x:m})]

def price_deferred_periodic(lx, v, x, m, C=1):
    """
    Annual premium — deferred pension with contre-assurance.

    P = C * m|ä_x / [ä_{x:m} - IA¹_{x:m} - m*(A_x - A¹_{x:m})]

    Parameters
    ----------
    x  : int    age at issue
    m  : int    deferral period (years)
    C : float  annual pension amount (€/yr)
    """
    m_ax    = nEx(lx, v, x, m) * a_due(lx, v, x + m)   # m|ä_x
    a_xm    = a_due(lx, v, x, m)                         # ä_{x:m}
    IA      = IA_term(lx, v, x, m)                       # IA¹_{x:m}
    Ax      = A_whole(lx, v, x)                          # A_x
    A1_xm   = A_term(lx, v, x, m)                        # A¹_{x:m}

    denom = a_xm - IA - m * (Ax - A1_xm)
    return C * m_ax / denom


def reserve_deferred_periodic(lx, v, x, m, t, C=1):
    """
    Prospective reserve at t — deferred pension, periodic premium.

    ── During deferral (t <= m) ──────────────────────────────
    Future obligations:
    1. Pension if survives deferral:   C * (m-t)|ä_{x+t}
    2. Return of future premiums
       if death in deferral:           P * IA¹_{x+t : m-t}
    3. Return of ALL premiums (past+future)
       if death in pension phase:      (t+k+1)*P for k>=m-t
                                     = P*(t*A_{x+t} deferred + m*...) 
       Simplified: m*P*(A_{x+t} - A¹_{x+t:m-t})  for past portion
                 + P*IA¹_{x+t:m-t} already in (2) for future deferral
    Future premiums still due:         P * ä_{x+t : m-t}

    tV = C * (m-t)|ä_{x+t}
         + P * t      * (A_{x+t} - A¹_{x+t:m-t})   ← past premiums, death in pension
         + P * IA¹_{x+t:m-t}                         ← future premiums, death in deferral
         + P * m      * ... (future prem, death in pension — folded in denom)
         - P * ä_{x+t : m-t}                         ← future premiums to collect

    ── After deferral (t > m) ────────────────────────────────
    No more premiums. Only obligations:
    1. Remaining pension:   C * ä_{x+t}
    2. Return of m*P lump sum on death: m*P * A_{x+t}

    tV = C * ä_{x+t} + m*P * A_{x+t}

    Parameters
    ----------
    t : int     time elapsed since issue
    """
    P = price_deferred_periodic(lx, v, x, m, C)

    if t > m:
        # ── Pension phase ─────────────────────────────────
        ax_t  = a_due(lx, v, x + t)
        Ax_t  = A_whole(lx, v, x + t)
        return C * ax_t + m * P * Ax_t

    else:
        # ── Deferral phase ────────────────────────────────
        rem       = m - t                                    # remaining deferral
        m_ax_t    = nEx(lx, v, x+t, rem) * a_due(lx, v, x+m)  # (m-t)|ä_{x+t}
        IA_t      = IA_term(lx, v, x+t, rem)                # IA¹_{x+t:m-t}
        A1_t      = A_term(lx, v, x+t, rem)                 # A¹_{x+t:m-t}
        Ax_t      = A_whole(lx, v, x+t)                     # A_{x+t}
        a_t       = a_due(lx, v, x+t, rem)                  # ä_{x+t:m-t}

        apv_pension   = C * m_ax_t
        apv_past_prem = P * t * (Ax_t - A1_t)   # past premiums returned if death in pension
        apv_fut_def   = P * IA_t                 # future premiums returned if death in deferral
        apv_fut_pen   = P * m * (Ax_t - A1_t)   # full m premiums if death in pension phase
        apv_incoming  = P * a_t                  # future premiums still to collect

        return apv_pension + apv_past_prem + apv_fut_def - apv_incoming