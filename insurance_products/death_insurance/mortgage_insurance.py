from core.mortality import kqx
from core.annuities import a_due
from insurance_products.death_insurance.term_life import A_term


def amortization_schedule(loan_amount, loan_rate, n_years, frequency="annual"):
    """
    Construit le tableau d'amortissement du prêt.

    Parameters
    ----------
    frequency : str   "annual" (annuités annuelles) ou "monthly" (mensualités)

    Returns
    -------
    crd     : list    CRD en début de chaque PÉRIODE PRINCIPALE (année)
    payment : float   montant du paiement périodique (annuel ou mensuel)
    """
    if frequency == "annual":
        periods_per_year = 1
        n_periods = n_years
        rate_per_period = loan_rate

    elif frequency == "monthly":
        periods_per_year = 12
        n_periods = n_years * 12
        rate_per_period = loan_rate / 12

    else:
        raise ValueError("frequency must be 'annual' or 'monthly'")

    if rate_per_period == 0:
        payment = loan_amount / n_periods
    else:
        payment = loan_amount * rate_per_period / (1 - (1 + rate_per_period) ** (-n_periods))

    balance = loan_amount
    crd_yearly = []
    for period in range(n_periods):
        if period % periods_per_year == 0:
            crd_yearly.append(balance)
        interest  = balance * rate_per_period
        principal = payment - interest
        balance  -= principal

    return crd_yearly, payment

def crd_mid_year_approx(crd_start, loan_rate):
    """
    Approximation du CRD à mi-année (convention UDD).
    C_mid = CRD_début + 0.5 * i * CRD_début
          = CRD_début * (1 + i/2)

    Parameters
    ----------
    crd_start : float   CRD en début d'année
    loan_rate : float   taux nominal annuel du crédit
    """
    return crd_start * (1 + loan_rate / 2)

def A_mortgage_crd(lx, v, x, n, crd_schedule, loan_rate):
    """
    APV avec capital ajusté à mi-année (CRD début + 1/2 intérêt).
    """
    crd_adjusted = [crd_mid_year_approx(c, loan_rate) for c in crd_schedule]
    return sum(
        crd_adjusted[k] * v**(k + 0.5) * kqx(lx, x, k)
        for k in range(n)
    )

def price_single_crd(lx, v, x, n, loan_amount, loan_rate, frequency="annual"):
    crd, _ = amortization_schedule(loan_amount, loan_rate, n, frequency=frequency)  # ← dépaqueter ici aussi
    return A_mortgage_crd(lx, v, x, n, crd, loan_rate)



def price_periodic_crd(lx, v, x, n, loan_amount, loan_rate, k_fraction=12):
    """
    Monthly premium — mortgage insurance on remaining capital (CRD).
    Premiums paid monthly (k_fraction=12), constant amount.
    """
    PI = price_single_crd(lx, v, x, n, loan_amount, loan_rate)
    a_annual = a_due(lx, v, x, n, immediate=True)
    return PI / a_annual / k_fraction   # monthly amount


def price_single_constant(lx, v, x, n, loan_amount):
    """Single premium — mortgage insurance, constant capital = initial loan."""
    return loan_amount * A_term(lx, v, x, n)


def price_periodic_constant(lx, v, x, n, loan_amount, k_fraction=12):
    """Monthly premium — mortgage insurance, constant capital."""
    PI = price_single_constant(lx, v, x, n, loan_amount)
    a_annual = a_due(lx, v, x, n, immediate=True)
    return PI / a_annual / k_fraction


def compute_teg(loan_amount, loan_rate, n_years, insurance_premium,
                 frequency="annual", fees=0):
    """
    Calcule le TEG/TAEG en intégrant l'assurance dans les flux.

    Parameters
    ----------
    frequency          : str   "annual" ou "monthly" — doit correspondre
                                à la fréquence des annuités du prêt
    insurance_premium  : float   prime périodique (même fréquence que le prêt)
    """
    crd, payment = amortization_schedule(loan_amount, loan_rate, n_years, frequency)

    periods_per_year = 1 if frequency == "annual" else 12
    n_periods = n_years * periods_per_year
    total_flow = payment + insurance_premium

    def npv(rate_per_period):
        flows = sum(
            total_flow / (1 + rate_per_period) ** p
            for p in range(1, n_periods + 1)
        )
        return flows + fees - loan_amount

    rate = loan_rate / periods_per_year
    for _ in range(100):
        f  = npv(rate)
        df = (npv(rate + 1e-7) - f) / 1e-7
        if abs(df) < 1e-12:
            break
        new_rate = rate - f / df
        if abs(new_rate - rate) < 1e-10:
            rate = new_rate
            break
        rate = new_rate

    annual_teg = (1 + rate) ** periods_per_year - 1
    return annual_teg