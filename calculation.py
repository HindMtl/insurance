# region ── USER INPUTS ── modify only this section ────────
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

# ── Available mortality tables ──────────────────────────
TABLES = {
    "1": "TH00_02",    # French male  2000-2002
    "2": "TF00_02",    # French female 2000-2002
    "3": "TV88-90",    # French female 1988-1990
    "4": "TD88-90",    # French male  1988-1990
    "5": "TGF05",      # French female generational 2005
    "6": "TGH05",      # French male generational 2005
    "7": "TF00_02decalee" # French female 2000-2002 adjusted
}


GENERATIONAL_TABLES = {"5", "6"}    # keys requiring generation extraction
SETBACK_ELIGIBLE     = {"1", "2"}    # only TH00-02 and TF00-02 can have setback
ANNUITY_TABLES       = {"5", "6"}

# Setback table files (in tables/ folder)
SETBACK_FILES = {
    "1": "setback/decalageTH00_02.csv",   # ← setback folder
    "2": "setback/decalageTF00_02.csv",   # ← setback folder
}
# ── Available insurance products ────────────────────────
PRODUCTS = {
    "1":  "Term life",
    "2":  "Whole life",
    "3":  "Decreasing term",
    "4":  "Pure endowment",
    "5":  "Whole life annuity",
    "6":  "Deferred annuity",
    "7":  "Temporary annuity",
    "8":  "Endowment",
    "9":  "Endowment + contre-assurance",
    "10": "Pension + reversion",
    "10b": "Pension + reversion (2 beneficiaries)",
    "11": "Pension + contre-assurance",
    "12": "Deferred temporary annuity",
    "13":  "Mortgage insurance (constant capital)",
    "13b": "Mortgage insurance (CRD — decreasing capital)",
}

# ── Regulatory table groups ──────────────────────────────
ANNUITY_PRODUCTS = {"5", "6", "12", "7", "10", "10b", "11"}
ANNUITY_TABLES   = {"5", "6"}       # only generational for annuities
DEATH_TABLES     = {"1", "2", "4", "5", "6"}

# ── Main selections ──────────────────────────────────────
TABLE_CHOICE    = "7"        # ← main table for (x)
TABLE_CHOICE_Y  = "7"        # ← table for (y) — multi-life only    
TABLE_CHOICE_Z  = "7"        # ← table for (z) - reversion plural

PRODUCT_CHOICE  = "9"       # ← insurance product
IMMEDIATE       = False      # ← True = annuity-immediate, False = annuity-due
SINGLE_PREMIUM  = True       # ← True = single premium, False = periodic

# ── Age setback (décalage réglementaire) ────────────────
# Only applies when TABLE_CHOICE is "1" (TH00-02) or "2" (TF00-02)
# For annuity reserves, generational tables are mandatory anyway
USE_SETBACK   = False     # ← True = apply age setback to eligible tables
                         #   False = use raw table without setback
# ── Generational table settings ──────────────────────────
OBSERVATION_YEAR = 2026      # ← current year, used for generational tables

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

x     = 40              # age at issue
C     = 100000           # benefit or annual annuity (€)
i     = 2 / 100       # interest rate

# Set to None if not needed for your chosen product
n     = 20          # term (years)          — products 1,3,4,7,8,9
m     = 0           # deferral period       — products 6,11
y     = 60               # beneficiary age       — products 10,11
z     = 65               # beneficiary 2 age - product 10b
alpha = 1              # reversion rate        — product 10 only

# ── Three reserve calculation times ─────────────────────
T1    = 1
T2    = 2
T3    = 10

# ── Mortgage insurance inputs ─────────────────────────────
LOAN_AMOUNT = 50000     # ← capital prêté (€)
LOAN_RATE   = 0.032635      # ← taux nominal du crédit
LOAN_FEES   = 500         # ← frais de dossier (€), for TEG calculation
LOAN_FREQUENCY = "annual"   # ← "annual" (annuités) ou "monthly" (mensualités)
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# endregion


# region ── IMPORTS ─────────────────────────────────────────
import pandas as pd
from core.interest  import get_v
from core.mortality import load_table, load_generational_table, load_setback, apply_setback

# endregion


# region ── VALIDATION ──────────────────────────────────────
if TABLE_CHOICE not in TABLES:
    raise ValueError(f"Invalid TABLE_CHOICE '{TABLE_CHOICE}'. "
                     f"Choose from: {list(TABLES.keys())}")
if TABLE_CHOICE_Y not in TABLES:
    raise ValueError(f"Invalid TABLE_CHOICE_Y '{TABLE_CHOICE_Y}'. "
                     f"Choose from: {list(TABLES.keys())}")
if TABLE_CHOICE_Z not in TABLES:
    raise ValueError(f"Invalid TABLE_CHOICE_Z '{TABLE_CHOICE_Z}'. "
                     f"Choose from: {list(TABLES.keys())}")
if PRODUCT_CHOICE not in PRODUCTS:
    raise ValueError(f"Invalid PRODUCT_CHOICE '{PRODUCT_CHOICE}'. "
                     f"Choose from: {list(PRODUCTS.keys())}")


table_name   = TABLES[TABLE_CHOICE]
table_name_y = TABLES[TABLE_CHOICE_Y]
table_name_z = TABLES.get(TABLE_CHOICE_Z, None)
product_name = PRODUCTS[PRODUCT_CHOICE]
v            = get_v(i)
is_multilife = PRODUCT_CHOICE in ("10", "10b", "11")
times        = [T1, T2, T3]
# endregion


# region ── PARAMETER VALIDATION PER PRODUCT ────────────────
NEEDS_N     = {"1", "3", "4", "12", "7", "8", "9", "13", "13b"}
NEEDS_M     = {"6", "12", "11"}
NEEDS_Y     = {"10", "10b", "11"}
NEEDS_Z     = {"10b"}
NEEDS_ALPHA = {"10", "10b"}
NEEDS_LOAN  = {"13", "13b"} 

errors = []

if PRODUCT_CHOICE in NEEDS_N and n is None:
    errors.append(f"Product '{product_name}' requires n (term). Please set n.")
if PRODUCT_CHOICE in NEEDS_M and m is None:
    errors.append(f"Product '{product_name}' requires m (deferral). Please set m.")
if PRODUCT_CHOICE in NEEDS_Y and y is None:
    errors.append(f"Product '{product_name}' requires y (beneficiary age). Please set y.")
if PRODUCT_CHOICE in NEEDS_ALPHA and alpha is None:
    errors.append(f"Product '{product_name}' requires alpha. Please set alpha.")
if PRODUCT_CHOICE in NEEDS_Z and z is None:
    errors.append(f"Product '{product_name}' requires z (second beneficiary age). Please set z.")
if PRODUCT_CHOICE in NEEDS_LOAN and (LOAN_AMOUNT is None or LOAN_RATE is None):
    errors.append(f"Product '{product_name}' requires LOAN_AMOUNT and LOAN_RATE.")

if errors:
    print("\n⚠️  INPUT ERRORS — please fix before running:")
    for e in errors:
        print(f"   ✗ {e}")
    raise ValueError("Missing required inputs — see messages above.")
# endregion

# ── Setback validation ───────────────────────────────────
if USE_SETBACK:
    if TABLE_CHOICE not in SETBACK_ELIGIBLE:
        print(f"  ⚠️  USE_SETBACK=True but table '{TABLES[TABLE_CHOICE]}' "
              f"has no setback defined — setback ignored for (x).")
    if is_multilife and TABLE_CHOICE_Y not in SETBACK_ELIGIBLE:
        print(f"  ⚠️  USE_SETBACK=True but table '{TABLES[TABLE_CHOICE_Y]}' "
              f"has no setback defined — setback ignored for (y).")

# region ── RESERVE TIME VALIDATION ─────────────────────────
for t in times:
    if PRODUCT_CHOICE in NEEDS_N and n is not None and t >= n:
        raise ValueError(
            f"Reserve time t={t} must be strictly less than n={n} "
            f"for product '{product_name}'.")
    if PRODUCT_CHOICE in NEEDS_M and n is not None and t > n:
        raise ValueError(
            f"Reserve time t={t} exceeds insurance_products term n={n}.")
    # deferred temporary annuity — total duration is m + n
    if PRODUCT_CHOICE == "12" and m is not None and n is not None:
        if t >= m + n:
            raise ValueError(
                f"Reserve time t={t} exceeds total duration "
                f"m+n={m+n} ({m} deferral + {n} payment period) "
                f"for product '{product_name}'. Please reduce T1, T2 or T3.")
# endregion


# region ── LOAD HELPER ─────────────────────────────────────
def load(table_key, age):
    path = f"tables/{TABLES[table_key]}.csv"

    if table_key in GENERATIONAL_TABLES:
        return load_generational_table(path, age, OBSERVATION_YEAR)

    lx = load_table(path)

    if USE_SETBACK and table_key in SETBACK_ELIGIBLE:
        setback_path = SETBACK_FILES[table_key]   # ← already includes setback/ prefix
        setback      = load_setback(setback_path)
        lx           = apply_setback(lx, setback)
        print(f"  [Setback applied] {TABLES[table_key]} — age offset active")

    return lx
# endregion


# region ── CALCULATION HELPER ──────────────────────────────
def compute(lx,lx_y =None, lx_z =None):
    """
    Returns dict with pricing and reserve results
    for the selected product and all reserve times.
    """
    pc  = PRODUCT_CHOICE
    res = {}

    if pc in ("10","10b", "11") and lx_y is None:
        raise ValueError(
            "Multi-life product selected but no table for (y). "
            "Please set TABLE_CHOICE_Y.")
    if pc == "10b" and lx_z is None:
        raise ValueError("Product 10b requires a table for (z).")

    def rkey(label, t):
        return f"{label} t={t}"

    # ── 1. Term life ──────────────────────────────────────
    if pc == "1":
        from insurance_products.death_insurance.term_life import (
            price_single, price_periodic, reserve_single, reserve_periodic)
        m_val = m if m is not None else 0
        res["Single premium"]   = price_single(lx, v, x, n, C, m=m_val)
        res["Periodic premium"] = price_periodic(lx, v, x, n, C, m=m_val)
        for t in times:
            res[rkey("Reserve (single)", t)]   = reserve_single(lx, v, x, n, t, C, m=m_val)
            res[rkey("Reserve (periodic)", t)] = reserve_periodic(lx, v, x, n, t, C, m=m_val)

    # ── 2. Whole life ─────────────────────────────────────
    elif pc == "2":
        from insurance_products.death_insurance.whole_life import (
        price_single, price_periodic, reserve_single, reserve_periodic)
        m_val = m if m is not None else 0
        res["Single premium"]   = price_single(lx, v, x, C, m=m_val)
        res["Periodic premium"] = price_periodic(lx, v, x, C, m=m_val)
        for t in times:
            res[rkey("Reserve (single)", t)]   = reserve_single(lx, v, x, t, C, m=m_val)
            res[rkey("Reserve (periodic)", t)] = reserve_periodic(lx, v, x, t, C, m=m_val)
    
        # ── 3. Decreasing term ────────────────────────────────
    elif pc == "3":
        from insurance_products.death_insurance.decreasing_term import (
            price_single, price_periodic,
            reserve_single, reserve_periodic)
        res["Single premium"]   = price_single(lx, v, x, n, C)
        res["Periodic premium"] = price_periodic(lx, v, x, n, C)
        for t in times:
            res[rkey("Reserve (single)", t)]   = reserve_single(lx, v, x, n, t, C)
            res[rkey("Reserve (periodic)", t)] = reserve_periodic(lx, v, x, n, t, C)

    # ── 4. Pure endowment ─────────────────────────────────
    elif pc == "4":
        from insurance_products.survival_insurance.pure_endowment import (
            price_single, price_periodic,
            reserve_single, reserve_periodic)
        res["Single premium"]   = price_single(lx, v, x, n, C)
        res["Periodic premium"] = price_periodic(lx, v, x, n, C)
        for t in times:
            res[rkey("Reserve (single)", t)]   = reserve_single(lx, v, x, n, t, C)
            res[rkey("Reserve (periodic)", t)] = reserve_periodic(lx, v, x, n, t, C)

    # ── 5. Whole life annuity ─────────────────────────────
    elif pc == "5":
        from insurance_products.survival_insurance.life_annuity import (
            price_whole_life_single, reserve_whole_life)
        res["Single premium"]   = price_whole_life_single(lx, v, x, C,
                                                           immediate=IMMEDIATE)
        res["Periodic premium"] = None
        for t in times:
            res[rkey("Reserve (single)", t)]   = reserve_whole_life(lx, v, x, t, C,
                                                                      immediate=IMMEDIATE)
            res[rkey("Reserve (periodic)", t)] = None

    # ── 6. Deferred annuity ───────────────────────────────
    elif pc == "6":
        from insurance_products.survival_insurance.life_annuity import (price_deferred_single, price_deferred_periodic,
            reserve_deferred_single, reserve_deferred_periodic)
        
        res["Single premium"]   = price_deferred_single(lx, v, x, m, C, immediate=IMMEDIATE)
        res["Periodic premium"] = price_deferred_periodic(lx, v, x, m, C, immediate=IMMEDIATE)
        for t in times:
            res[rkey("Reserve (single)", t)]   = reserve_deferred_single(lx, v, x, m, t, C, immediate=IMMEDIATE)
            res[rkey("Reserve (periodic)", t)] = reserve_deferred_periodic(lx, v, x, m, t, C, immediate=IMMEDIATE)
    # ── 12. Deferred temporary annuity ───────────────────────
    elif pc == "12":
        from insurance_products.survival_insurance.life_annuity import (
            a_deferred_temporary,
            reserve_deferred_temporary)

        res["Single premium"]   = C * a_deferred_temporary(lx, v, x, m, n,
                                                            immediate=IMMEDIATE)
        res["Periodic premium"] = None
        for t in times:
            res[rkey("Reserve (single)", t)]   = reserve_deferred_temporary(
                lx, v, x, m, n, t, C, immediate=IMMEDIATE)
            res[rkey("Reserve (periodic)", t)] = None
    # ── 7. Temporary annuity ──────────────────────────────
    elif pc == "7":
        from insurance_products.survival_insurance.life_annuity import (
            price_temporary_single, reserve_temporary)
        res["Single premium"]   = price_temporary_single(lx, v, x, n, C,
                                                          immediate=IMMEDIATE)
        res["Periodic premium"] = None
        for t in times:
            res[rkey("Reserve (single)", t)]   = reserve_temporary(lx, v, x, n, t, C,
                                                                     immediate=IMMEDIATE)
            res[rkey("Reserve (periodic)", t)] = None

    # ── 8. Endowment ──────────────────────────────────────
    elif pc == "8":
        from insurance_products.mixed_insurance.endowment_insurance import (
            price_single, price_periodic,
            reserve_single, reserve_periodic)
        res["Single premium"]   = price_single(lx, v, x, n, C)
        res["Periodic premium"] = price_periodic(lx, v, x, n, C)
        for t in times:
            res[rkey("Reserve (single)", t)]   = reserve_single(lx, v, x, n, t, C)
            res[rkey("Reserve (periodic)", t)] = reserve_periodic(lx, v, x, n, t, C)

    # ── 9. Endowment + contre-assurance ───────────────────
    elif pc == "9":
        from insurance_products.mixed_insurance.endowment_contreassurance import (
            price_single, price_periodic,
            reserve_single, reserve_periodic)
        res["Single premium"]   = price_single(lx, v, x, n, C)
        res["Periodic premium"] = price_periodic(lx, v, x, n, C)
        for t in times:
            res[rkey("Reserve (single)", t)]   = reserve_single(lx, v, x, n, t, C)
            res[rkey("Reserve (periodic)", t)] = reserve_periodic(lx, v, x, n, t, C)

    # ── 10. Pension + reversion ───────────────────────────
    elif pc == "10":
        from insurance_products.multi_life_insurance.pension_reversion import (
            price_single, price_periodic,
            reserve_joint, reserve_reversion_triggered, reserve_reversion_lapsed,
            a_reversionary)
        from core.annuities import a_due

        apv_pension   = C * a_due(lx, v, x, n=None, immediate=IMMEDIATE)
        apv_reversion = alpha * C * a_reversionary(lx, lx_y, v, x, y,
                                                    immediate=IMMEDIATE)
        res["Premium — pension part (APV)"]   = apv_pension
        res["Premium — reversion part (APV)"] = apv_reversion
        res["Single premium (total)"]         = apv_pension + apv_reversion
        res["Periodic premium (total)"]       = price_periodic(lx, lx_y, v, x, y,
                                                                C, alpha,
                                                                immediate=IMMEDIATE)
        for t in times:
            res[rkey("Reserve — both alive", t)] = reserve_joint(
                lx, lx_y, v, x, y, t, C, alpha,
                single=SINGLE_PREMIUM, immediate=IMMEDIATE)
            res[rkey("Reserve — (x) dead (y) alive", t)] = reserve_reversion_triggered(
                lx_y, v, y, t, C, alpha, immediate=IMMEDIATE)
            res[rkey("Reserve — (y) dead (x) alive", t)] = reserve_reversion_lapsed(
                lx, v, x, t, C, immediate=IMMEDIATE)
     # ── 1Ob. Pension + reversion 2 beneficiaries ────────────────────
    elif pc == "10b":
        from insurance_products.multi_life_insurance.pension_reversion import (
            price_single_two_beneficiaries, price_periodic_two_beneficiaries,
            reserve_two_beneficiaries, reserve_x_dead, a_reversionary)
        from core.annuities import a_due

        if lx_z is None:
            raise ValueError("Product 10b requires a table for (z).")

        apv_pension     = C * a_due(lx, v, x, n=None, immediate=IMMEDIATE)
        apv_reversion_y = alpha * C * a_reversionary(lx, lx_y, v, x, y, immediate=IMMEDIATE)
        apv_reversion_z = alpha * C * a_reversionary(lx, lx_z, v, x, z, immediate=IMMEDIATE)

        res["Premium — pension part (APV)"]      = apv_pension
        res["Premium — reversion (y) part (APV)"] = apv_reversion_y
        res["Premium — reversion (z) part (APV)"] = apv_reversion_z
        res["Single premium (total)"]            = apv_pension + apv_reversion_y + apv_reversion_z
        res["Periodic premium (total)"]          = price_periodic_two_beneficiaries(
            lx, lx_y, lx_z, v, x, y, z, C, alpha)

        for t in times:
            res[rkey("Reserve — x alive", t)] = reserve_two_beneficiaries(
                lx, lx_y, lx_z, v, x, y, z, t, C, alpha, single=SINGLE_PREMIUM)
            res[rkey("Reserve — x dead", t)] = reserve_x_dead(
                lx_y, lx_z, v, y, z, t, C, alpha)

    # ── 11. Pension + contre-assurance ────────────────────
    elif pc == "11":
        from insurance_products.multi_life_insurance.pension_contreassurance import (
            price_immediate_single, price_deferred_periodic,
            reserve_immediate_single, reserve_deferred_periodic)
        from insurance_products.survival_insurance.life_annuity import price_deferred_single
        from core.annuities import a_due, nEx

        PI_total        = price_immediate_single(lx, v, x, C)
        P_total         = price_deferred_periodic(lx, v, x, m, C)
        apv_pension     = price_deferred_single(lx, v, x, m, C, immediate=IMMEDIATE)
        apv_contre      = PI_total - apv_pension
        nex             = nEx(lx, v, x, m)
        ax_m            = a_due(lx, v, x + m, immediate=IMMEDIATE)
        ax_defer        = a_due(lx, v, x, n=m, immediate=IMMEDIATE)
        apv_pension_per = C * nex * ax_m
        apv_contre_per  = P_total * ax_defer - apv_pension_per

        res["Single premium — pension part"]            = apv_pension
        res["Single premium — contre-assurance part"]   = apv_contre
        res["Single premium (total)"]                   = PI_total
        res["Periodic premium — pension part"]          = apv_pension_per / ax_defer
        res["Periodic premium — contre-assurance part"] = apv_contre_per / ax_defer
        res["Periodic premium (total)"]                 = P_total

        for t in times:
            res[rkey("Reserve (single)", t)]   = reserve_immediate_single(lx, v, x, t, C)
            res[rkey("Reserve (periodic)", t)] = reserve_deferred_periodic(lx, v, x, m, t, C)

    
    # ── 13. Mortgage insurance — constant capital ─────────────
    elif pc == "13":
        from insurance_products.death_insurance.mortgage_insurance import (
            price_single_constant, price_periodic_constant)

        PI = price_single_constant(lx, v, x, n, LOAN_AMOUNT)
        P  = price_periodic_constant(lx, v, x, n, LOAN_AMOUNT)

        res["Single premium"]   = PI
        res["Periodic premium (monthly)"] = P
        res["Periodic premium (annual equiv.)"] = P * 12

        # reserves use existing term life functions since constant capital
        # = LOAN_AMOUNT * A_term, same structure as term_life
        from insurance_products.death_insurance.term_life import (
            reserve_single as reserve_single_term,
            reserve_periodic as reserve_periodic_term)
        for t in times:
            res[rkey("Reserve (single)", t)]   = reserve_single_term(lx, v, x, n, t, LOAN_AMOUNT)
            res[rkey("Reserve (periodic)", t)] = reserve_periodic_term(lx, v, x, n, t, LOAN_AMOUNT)


    # ── 13b. Mortgage insurance — CRD (decreasing capital) ────
    elif pc == "13b":
        from insurance_products.death_insurance.mortgage_insurance import (
            price_single_crd, price_periodic_crd, amortization_schedule,
            A_mortgage_crd)

        PI = price_single_crd(lx, v, x, n, LOAN_AMOUNT, LOAN_RATE, frequency=LOAN_FREQUENCY)
        P  = price_periodic_crd(lx, v, x, n, LOAN_AMOUNT, LOAN_RATE)

        res["Single premium"]   = PI
        res["Periodic premium (monthly)"] = P
        res["Periodic premium (annual equiv.)"] = P * 12

        # reserve at time t: remaining CRD-weighted death benefit
        # minus future premiums (re-priced with t years already elapsed)
        crd_full, _ = amortization_schedule(LOAN_AMOUNT, LOAN_RATE, n, frequency=LOAN_FREQUENCY)

        for t in times:
            remaining_n   = n - t
            remaining_crd = crd_full[t:]   # CRD schedule from year t onward
            apv_benefit_t = A_mortgage_crd(lx, v, x + t, remaining_n, remaining_crd, LOAN_RATE)

            # future premiums still to be paid (annual equivalent annuity)
            from core.annuities import a_due
            a_remaining = a_due(lx, v, x + t, remaining_n, immediate=True)
            apv_premium_t = (P * 12) * a_remaining

            res[rkey("Reserve (single)", t)]   = apv_benefit_t
            res[rkey("Reserve (periodic)", t)] = apv_benefit_t - apv_premium_t

    return res
# endregion


# region ── MAIN CALCULATION ────────────────────────────────
lx   = load(TABLE_CHOICE,   x)
lx_y = load(TABLE_CHOICE_Y, y) if is_multilife else None
lx_z = load(TABLE_CHOICE_Z, z) if PRODUCT_CHOICE == "10b" else None

main_results = compute(lx, lx_y, lx_z)

print()
print("=" * 65)
print(f"  {product_name}")
print(f"  Table (x): {table_name}  |  i={i*100:.3f}%  |  x={x}  n={n}  C={C:,}")
if is_multilife:
    print(f"  Table (y): {table_name_y}  |  y={y}  alpha={alpha}")
    if PRODUCT_CHOICE == "10b":
        print(f"  Table (z): {table_name_z}  |  z={z}")
print("=" * 65)
for label, val in main_results.items():
    if val is not None:
        print(f"  {label:<45} : {val:>12.2f} €")
    else:
        print(f"  {label:<45} : {'N/A':>12}")
print("=" * 65)

#  TEG  block  :
if PRODUCT_CHOICE in ("13", "13b"):
    from insurance_products.death_insurance.mortgage_insurance import compute_teg

    P_periodic = main_results["Periodic premium (monthly)"] if LOAN_FREQUENCY == "monthly" \
                 else main_results["Periodic premium (annual equiv.)"]

    teg = compute_teg(LOAN_AMOUNT, LOAN_RATE, n, P_periodic,
                      frequency=LOAN_FREQUENCY, fees=LOAN_FEES)

    print()
    print(f"  Taux nominal du crédit               : {LOAN_RATE*100:>10.3f} %")
    print(f"  TEG / TAEG                           : {teg*100:>10.3f} %")
    print("=" * 65)

# region ── COMPARATIVE TABLE ───────────────────────────────

# ── Pricing: always all tables ───────────────────────────
COMPARE_TABLES_PRICING_X = {k: tname for k, tname in TABLES.items()}
COMPARE_TABLES_PRICING_Y = {k: tname for k, tname in TABLES.items()}


# region ── COMPARATIVE TABLE ───────────────────────────────

if PRODUCT_CHOICE == "10b":
    print()
    print("  ℹ️  3-life product — showing 3 separate 2D comparisons")
    print("     (each varies one table, fixes the other two at main selection)")

    # ── Determine valid tables for comparison ────────────────
    if PRODUCT_CHOICE in ANNUITY_PRODUCTS:
        COMPARE_TABLES_10B = {k: v for k, v in TABLES.items()
                               if k in ANNUITY_TABLES}
        print("     (regulatory: generational tables only)")
    else:
        COMPARE_TABLES_10B = {k: v for k, v in TABLES.items()}

    # ── Pre-load tables once ──────────────────────────────────
    loaded_10b = {k: load(k, x) for k in COMPARE_TABLES_10B}
    # note: same physical lx values reused with different ages below

    all_metrics     = list(main_results.keys())
    pricing_metrics = [k for k in all_metrics if "Reserve" not in k]
    reserve_metrics = [k for k in all_metrics if "Reserve" in k]

    metric_groups = [(pricing_metrics, "PRICING")]
    if PRODUCT_CHOICE in ANNUITY_PRODUCTS or True:
        metric_groups.append((reserve_metrics, "RESERVES"))

    for metrics, label in metric_groups:
        for metric in metrics:
            if main_results[metric] is None:
                continue

            print()
            print(f"── [{label}] {metric} ──")

            # ── Vary table of (x), fix (y) and (z) ─────────────
            print(f"   Varying table of (x)  [(y)={table_name_y}, (z)={table_name_z} fixed]")
            row = {}
            for kx, tx in COMPARE_TABLES_10B.items():
                lx_i = load(kx, x)
                r    = compute(lx_i, lx_y, lx_z)
                val  = r[metric]
                row[tx] = round(val, 2) if val is not None else "N/A"
            print(pd.Series(row).to_string())

            # ── Vary table of (y), fix (x) and (z) ─────────────
            print(f"\n   Varying table of (y)  [(x)={table_name}, (z)={table_name_z} fixed]")
            row = {}
            for ky, ty in COMPARE_TABLES_10B.items():
                lx_j = load(ky, y)
                r    = compute(lx, lx_j, lx_z)
                val  = r[metric]
                row[ty] = round(val, 2) if val is not None else "N/A"
            print(pd.Series(row).to_string())

            # ── Vary table of (z), fix (x) and (y) ─────────────
            print(f"\n   Varying table of (z)  [(x)={table_name}, (y)={table_name_y} fixed]")
            row = {}
            for kz, tz in COMPARE_TABLES_10B.items():
                lx_k = load(kz, z)
                r    = compute(lx, lx_y, lx_k)
                val  = r[metric]
                row[tz] = round(val, 2) if val is not None else "N/A"
            print(pd.Series(row).to_string())

    print()
    print(f"  ★ Main selection : (x) = {table_name}  |  (y) = {table_name_y}  |  (z) = {table_name_z}")

else:
    # ── Determine which tables are valid for comparison ──────
    if PRODUCT_CHOICE in ANNUITY_PRODUCTS:
        COMPARE_TABLES_PRICING_X = {k: v for k, v in TABLES.items()}
        COMPARE_TABLES_PRICING_Y = {k: v for k, v in TABLES.items()}
        COMPARE_TABLES_RESERVE_X = {k: v for k, v in TABLES.items()
                                     if k in ANNUITY_TABLES}
        COMPARE_TABLES_RESERVE_Y = {k: v for k, v in TABLES.items()
                                     if k in ANNUITY_TABLES}
        print()
        print("  ℹ️  Annuity product — reserves restricted to generational tables")
        print("     (regulatory requirement: TGF05/TGH05 for rentes viagères)")
        print("     Pricing comparative shows all tables for reference.")
    else:
        COMPARE_TABLES_PRICING_X = {k: v for k, v in TABLES.items()
                                     if k not in GENERATIONAL_TABLES}
        COMPARE_TABLES_PRICING_Y = {k: v for k, v in TABLES.items()
                                     if k not in GENERATIONAL_TABLES}
        COMPARE_TABLES_RESERVE_X = COMPARE_TABLES_PRICING_X
        COMPARE_TABLES_RESERVE_Y = COMPARE_TABLES_PRICING_Y

    # ── Pre-load all tables once ─────────────────────────────
    all_keys   = set(COMPARE_TABLES_PRICING_X) | set(COMPARE_TABLES_RESERVE_X)
    all_keys_y = set(COMPARE_TABLES_PRICING_Y) | set(COMPARE_TABLES_RESERVE_Y)

    loaded_x = {kx: load(kx, x) for kx in all_keys}
    loaded_y = {ky: load(ky, y) for ky in all_keys_y}

    if not is_multilife:
        # ── Single life: rows = tables, columns = metrics ────
        rows_pricing = {}
        for kx, tx in COMPARE_TABLES_PRICING_X.items():
            lx_i = loaded_x[kx]
            r    = compute(lx_i)
            rows_pricing[tx] = {
                k: (round(val, 2) if val is not None else "N/A")
                for k, val in r.items()
                if "Reserve" not in k
            }

        rows_reserve = {}
        for kx, tx in COMPARE_TABLES_RESERVE_X.items():
            lx_i = loaded_x[kx]
            r    = compute(lx_i)
            rows_reserve[tx] = {
                k: (round(val, 2) if val is not None else "N/A")
                for k, val in r.items()
                if "Reserve" in k
            }

        print()
        print("── Comparative — PRICING (all tables) ────────────────────")
        df_p = pd.DataFrame(rows_pricing).T
        df_p.index.name = "Mortality table"
        print(df_p.to_string())

        print()
        print("── Comparative — RESERVES (regulatory tables only) ───────")
        df_r = pd.DataFrame(rows_reserve).T
        df_r.index.name = "Mortality table"
        print(df_r.to_string())

        print(f"\n  ★ Main table : {table_name}")

    else:
        # ── Multi-life: one matrix per metric ────────────────
        all_metrics     = list(main_results.keys())
        pricing_metrics = [k for k in all_metrics if "Reserve" not in k]
        reserve_metrics = [k for k in all_metrics if "Reserve" in k]

        for metric in pricing_metrics:
            if main_results[metric] is None:
                continue

            print()
            print(f"── [PRICING] {metric} ──")
            print(f"   rows = table of (x)   |   cols = table of (y)   "
                  f"[all tables]")

            matrix = {}
            for kx, tx in COMPARE_TABLES_PRICING_X.items():
                lx_i = loaded_x[kx]
                row  = {}
                for ky, ty in COMPARE_TABLES_PRICING_Y.items():
                    lx_j = loaded_y[ky]
                    r    = compute(lx_i, lx_j)
                    val  = r[metric]
                    row[ty] = round(val, 2) if val is not None else "N/A"
                matrix[tx] = row

            df = pd.DataFrame(matrix).T
            df.index.name   = "lx(x) \\ lx(y)"
            df.columns.name = None
            print(df.to_string())

        if PRODUCT_CHOICE in ANNUITY_PRODUCTS:
            print()
            print("── [RESERVES] Regulatory tables only "
                  "(TGF05/TGH05) ────────────────")

        for metric in reserve_metrics:
            if main_results[metric] is None:
                continue

            print()
            print(f"── [RESERVES] {metric} ──")
            print(f"   rows = table of (x)   |   cols = table of (y)   "
                  f"[regulatory tables only]")

            matrix = {}
            for kx, tx in COMPARE_TABLES_RESERVE_X.items():
                lx_i = loaded_x[kx]
                row  = {}
                for ky, ty in COMPARE_TABLES_RESERVE_Y.items():
                    lx_j = loaded_y[ky]
                    r    = compute(lx_i, lx_j)
                    val  = r[metric]
                    row[ty] = round(val, 2) if val is not None else "N/A"
                matrix[tx] = row

            df = pd.DataFrame(matrix).T
            df.index.name   = "lx(x) \\ lx(y)"
            df.columns.name = None
            print(df.to_string())

        print()
        print(f"  ★ Main : (x) = {table_name}  |  (y) = {table_name_y}")

# endregion