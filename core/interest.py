# core/interest.py

def get_v(i: float) -> float:
    """
    Returns the annual discount factor v = 1 / (1 + i).

    Parameters
    ----------
    i : float
        Annual interest rate (e.g. 0.03 for 3%)
    """
    return 1 / (1 + i)