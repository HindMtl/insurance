# pricing-reserving-tool

A modular Python toolkit for pricing and reserving life insurance contracts, built for French actuarial practice.

---

## Features

- **8 contract types** — term life, whole life, decreasing term, pure endowment, endowment, life annuity (whole, deferred, temporary), pension with reversion, pension with contre-assurance, mortgage insurance
- **Multi-life products** — reversionary annuity with one or two beneficiaries, joint life annuities
- **French regulatory mortality tables** — TH00-02, TF00-02 (with age setback), TV88-90, TD88-90, TGH05, TGF05 (generational, extracted by birth year)
- **Fractioned annuities** — UDD approximation for monthly/quarterly/semi-annual payments
- **Deferral with premium refund** — optional deferral period (garantie obsèques) for term and whole life
- **Mid-year (UDD) death benefit convention** — $v^{k+1/2}$ throughout
- **Comparative tables** — results across all mortality tables; 2D matrices for multi-life products
- **TEG/TAEG calculation** — for mortgage insurance products
- **Offline** — no internet connection required after setup

---

## Project Structure

```
pricing-reserving-tool/
│
├── tables/                          # Mortality table CSV files
│   ├── TH00_02.csv
│   ├── TF00_02.csv
│   ├── TV88-90.csv
│   ├── TD88-90.csv
│   ├── TGH05.csv                    # Generational (rows=ages, cols=birth years)
│   └── TGF05.csv
│
├── setback/                         # Age setback tables (décalage réglementaire)
│   ├── decalageTH00_02.csv
│   └── decalageTF00_02.csv
│
├── core/                            # Building blocks
│   ├── __init__.py
│   ├── mortality.py                 # lx, tpx, qx, kqx, load_table, load_generational_table
│   ├── annuities.py                 # a_due, nEx, a_deferred, IA_term, a_due_fractioned
│   ├── interest.py                  # get_v
│   └── commutation.py               # Dx, Cx, Mx, Nx, Rx and derived functions
│
├── insurance_products/
│   ├── __init__.py
│   ├── death_insurance/
│   │   ├── __init__.py
│   │   ├── term_life.py             # A_term, IA_term, price/reserve (with optional deferral)
│   │   ├── whole_life.py            # A_whole, IA_whole, price/reserve (with optional deferral)
│   │   ├── decreasing_term.py       # A_decreasing, price/reserve
│   │   └── mortgage_insurance.py    # CRD schedule, APV, TEG/TAEG
│   │
│   ├── survival_insurance/
│   │   ├── __init__.py
│   │   ├── pure_endowment.py        # nEx, price/reserve
│   │   └── life_annuity.py          # whole life, deferred, temporary, deferred temporary
│   │
│   ├── mixed_insurance/
│   │   ├── __init__.py
│   │   ├── endowment_insurance.py   # A_endow, price/reserve
│   │   └── endowment_contreassurance.py  # IA_term-based, with rider decomposition
│   │
│   └── multi_life_insurance/
│       ├── __init__.py
│       ├── pension_reversion.py     # a_joint, a_reversionary, price/reserve (1 beneficiary)
│       ├── pension_reversion_2.py   # price/reserve (2 independent beneficiaries)
│       └── pension_contreassurance.py  # immediate and deferred, with lump-sum contre-assurance
│
└── calculation.py                   # Main entry point — inputs, compute(), comparative tables
```

---

## Getting Started

### Requirements

```bash
pip install numpy pandas
```

No other dependencies. Fully offline after installation.

### Running the tool

Always run from the project root:

```bash
cd pricing-reserving-tool
python calculation.py
```

---

## Usage

All user inputs are in the clearly marked section at the top of `calculation.py`:

```python
# region ── USER INPUTS ── modify only this section ────────
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

TABLE_CHOICE    = "1"        # mortality table for (x)
TABLE_CHOICE_Y  = "2"        # mortality table for (y) — multi-life only
PRODUCT_CHOICE  = "10"       # insurance product (see list below)
IMMEDIATE       = True       # annuity-immediate (terme échu) vs annuity-due
SINGLE_PREMIUM  = False      # single vs periodic premium

x     = 60                   # age at issue
n     = 20                   # term (years)
C     = 50_000               # benefit or annual annuity (€)
i     = 0.025                # interest rate
T1, T2, T3 = 1, 5, 10       # reserve calculation times

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
```

---

## Available Products

| Code | Product | French name |
|------|---------|-------------|
| `"1"` | Term life | Temporaire décès |
| `"2"` | Whole life | Vie entière |
| `"3"` | Decreasing term | Temporaire décès capital décroissant |
| `"4"` | Pure endowment | Capital différé |
| `"5"` | Whole life annuity | Rente viagère immédiate |
| `"6"` | Deferred annuity | Rente viagère différée |
| `"7"` | Temporary annuity | Rente temporaire |
| `"8"` | Endowment | Assurance mixte |
| `"9"` | Endowment + contre-assurance | Capital différé avec contre-assurance |
| `"10"` | Pension + reversion (1 beneficiary) | Rente avec réversion |
| `"10b"` | Pension + reversion (2 beneficiaries) | Rente avec réversion plurale |
| `"11"` | Pension + contre-assurance | Rente avec contre-assurance |
| `"12"` | Deferred temporary annuity | Rente temporaire différée |
| `"13"` | Mortgage insurance (constant capital) | Assurance emprunteur capital constant |
| `"13b"` | Mortgage insurance (CRD) | Assurance emprunteur capital décroissant |

---

## Available Mortality Tables

| Code | Table | Description |
|------|-------|-------------|
| `"1"` | TH00-02 | French male, 2000–2002 (moment table) |
| `"2"` | TF00-02 | French female, 2000–2002 (moment table) |
| `"3"` | TV88-90 | French female, 1988–1990 |
| `"4"` | TD88-90 | French male, 1988–1990 |
| `"5"` | TGF05 | French female, generational 2005 *(requires `OBSERVATION_YEAR`)* |
| `"6"` | TGH05 | French male, generational 2005 *(requires `OBSERVATION_YEAR`)* |

**Age setback (décalage réglementaire)** — applicable to TH00-02 and TF00-02 for life annuity pricing. Activate with `USE_SETBACK = True`.

**Generational tables** — birth year is derived automatically as `OBSERVATION_YEAR - x`. Set `OBSERVATION_YEAR` in the inputs.

---

## Actuarial Conventions

| Convention | Choice made |
|---|---|
| Death benefit timing | Mid-year UDD: $v^{k+1/2}$ |
| Survival annuity | Annuity-due $\ddot{a}_x$ (default) or annuity-immediate $a_x$ (`IMMEDIATE = True`) |
| Fractioned annuities | UDD approximation: $\ddot{a}_x^{(m)} \approx \ddot{a}_x - \frac{m-1}{2m}(1 - {}_nE_x)$ |
| Reserve basis | Prospective: ${}_{t}V = \text{APV(future benefits)} - \text{APV(future premiums)}$ |
| Mortality table format | CSV with columns `age;lx`, semicolon separator, comma decimal (French Excel) |

---

## Output

For each run, the tool prints:

1. **Main result** — single premium, periodic premium, reserves at T1/T2/T3
2. **Decomposition** (where applicable) — pension vs reversion APV, contre-assurance rider cost
3. **Comparative table** — results across all mortality tables
   - Single-life products: one row per table
   - Multi-life products: 2D matrix (table of x × table of y), or 3 separate 1D tables for 3-life products
   - Regulatory constraint applied: generational tables only for annuity product reserves

---

## Regulatory Notes

- **Life annuity reserving** (post-2007): TGH05/TGF05 mandatory (arrêté du 1er août 2006, Article A.335-1-1)
- **Age setback**: applicable to TH/TF00-02 for annuity *pricing* (not reserving) under the same arrêté
- **Mid-year convention**: consistent with course notation $A_{x:\overline{n|}} = \frac{M_x - M_{x+n}}{D_x}$ where $C_x = v^{x+1/2} \cdot d_x$

---

## CSV Format

### Standard mortality table
```
age;lx
0;100000
1;99511
...
110;0
```

### Generational table (TGH05/TGF05)
```
Age;1900;1901;1902;...;2005
0;-;-;-;...;100000
1;-;-;-;...;99745
...
```
Values use space as thousands separator and `-` for missing data (handled automatically).

### Age setback table
```
age;décalage
"[16 ; 32]";0
"[33 ; 34]";-11
...
[94 et plus];-1
```

---

## Author

Built as part of the actuarial studies programme.
