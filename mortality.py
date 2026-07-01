# core/mortality.py

import pandas as pd
import numpy as np

def load_table(path: str, omega=120) -> np.ndarray:
    """
    Loads a standard mortality table (columns: age, lx).
    Handles French decimal separator and padding from age 0.
    """
    df      = pd.read_csv(path, sep=";", decimal=",")
    # ── convert lx to numeric, fill empty cells with 0 ───
    df["lx"] = pd.to_numeric(df["lx"], errors="coerce").fillna(0.0)

    df      = df.sort_values("age").reset_index(drop=True)
    min_age = int(df["age"].iloc[0])
    max_age = int(df["age"].iloc[-1])

    if min_age > 0:
        pad_start = pd.DataFrame({"age": range(0, min_age), "lx": 0.0})
        df = pd.concat([pad_start, df], ignore_index=True)

    if max_age < omega:
        pad_end = pd.DataFrame({"age": range(max_age + 1, omega + 1), "lx": 0.0})
        df = pd.concat([df, pad_end], ignore_index=True)

    return df["lx"].to_numpy(dtype=float)

def load_generational_table(path: str, x: int, observation_year: int,
                             omega=120) -> np.ndarray:
    import os
    filename   = os.path.basename(path)
    birth_year = observation_year - x

    df = pd.read_csv(path, sep=";", decimal=",", index_col=0)
    df.index = df.index.astype(int)

    # ── convert string column names to int, drop non-numeric ──
    new_cols = {}
    for col in df.columns:
        try:
            new_cols[col] = int(str(col).strip())
        except ValueError:
            pass

    # drop columns that could not be converted
    df = df[list(new_cols.keys())].rename(columns=new_cols)


    if birth_year not in df.columns:
        raise ValueError(
            f"Birth year {birth_year} not found in {filename}. "
            f"Available: {min(df.columns)} to {max(df.columns)}"
        )

    series = df[birth_year]
    lx     = np.zeros(omega + 1)

    for age, val in series.items():
        if pd.isna(val):
            continue
        try:
            cleaned = (str(val)
                       .replace(" ", "")
                       .replace("\xa0", "")
                       .replace("-", "")
                       .strip())
            if cleaned != "":
                lx[int(age)] = float(cleaned)
        except (ValueError, IndexError):
            pass

    print(f"  [{filename}] Generation {birth_year} extracted "
          f"(age {x} in {observation_year})  lx[{x}] = {lx[x]:,.0f}")
    return lx

def load_setback(path: str) -> dict:
    """
    Loads an age setback table from CSV.
    Format: age ranges as strings, e.g. "[16 ; 32]";-11
    Returns dict mapping each individual age to its offset.

    Parameters
    ----------
    path : str   path to the setback CSV file
    """
    import re
    df = pd.read_csv(path, sep=";", header=0,
                     names=["age_range", "offset"])

    setback = {}
    for _, row in df.iterrows():
        age_str = str(row["age_range"]).strip().replace('"', '')
        offset  = int(row["offset"])

        # match [a ; b] pattern
        match = re.match(r'\[(\d+)\s*;\s*(\d+)\]', age_str)
        if match:
            a, b = int(match.group(1)), int(match.group(2))
            for age in range(a, b + 1):
                setback[age] = offset
        # match "94 et plus" pattern
        elif "et plus" in age_str:
            start = int(re.search(r'\d+', age_str).group())
            for age in range(start, 121):
                setback[age] = offset
        # match single age
        else:
            try:
                setback[int(age_str)] = offset
            except ValueError:
                pass

    return setback


def apply_setback(lx: np.ndarray, setback: dict, omega: int = 120) -> np.ndarray:
    """
    Returns a new lx array with age setback applied.
    lx_adjusted[x] = lx[x + offset(x)]

    Parameters
    ----------
    lx      : np.ndarray   original survival vector
    setback : dict         age -> offset mapping
    omega   : int          limiting age
    """
    lx_adj = np.zeros(omega + 1)
    for x in range(omega + 1):
        offset        = setback.get(x, 0)
        adjusted_age  = x + offset
        if 0 <= adjusted_age <= omega:
            lx_adj[x] = lx[adjusted_age]
        else:
            lx_adj[x] = 0.0
    return lx_adj


def tpx(lx: np.ndarray, x: int, t: int) -> float:
    """
    Probability that (x) survives t more years.
    tpx = lx[x+t] / lx[x]

    Parameters
    ----------
    lx : np.ndarray
        Survival function from the mortality table
    x  : int
        Current age
    t  : int
        Number of years
    """
    if x + t >= len(lx): # if the age is greater than the length of the table, return 0
        return 0.0
    if lx[x] == 0: # if age is 0, return 0
        return 0.0
    return lx[x + t] / lx[x]


def qx(lx: np.ndarray, x: int) -> float:
    """
    Probability that (x) dies within 1 year.
    qx = 1 - px = 1 - lx[x+1] / lx[x]

    Parameters
    ----------
    lx : np.ndarray
        Survival function from the mortality table
    x  : int
        Current age
    """
    return 1 - tpx(lx, x, 1)


def kqx(lx: np.ndarray, x: int, k: int) -> float:
    """
    Probability that (x) dies in year k+1, i.e. survives k years
    then dies in the following year.
    kqx = kpx * qx+k

    Parameters
    ----------
    lx : np.ndarray
        Survival function from the mortality table
    x  : int
        Current age
    k  : int
        Number of years survived before death year
    """
    return tpx(lx, x, k) * qx(lx, x + k)