import os
import glob
from mesatools.inlist import MesaInlist


def get_X(Z: float):
    """Calculates the hydrogen fraction given
        a heavy-element fraction Z and assuming protosolar
        composition.

    Args:
        Z (float): Heavy-element mass fraction

    Returns:
        X (float): Hydrogen mass fraction

    """
    yproto = 0.275  # protosolar helium abundance
    xproto = 0.705  # protosolar hydrogen abundance
    eta = yproto / xproto

    X = (1 - Z) / (1 + eta)
    return X


def get_Y(Z: float):
    """Calculates the helium fraction given
        a heavy-element fraction Z and assuming protosolar
        composition.

    Args:
        Z (float): Heavy-element mass fraction

    Returns:
        Y (float): Helium mass fraction
    """
    X = get_X(Z)
    return round(1 - Z - X, 3)


def get_latest_log(infile: str, legacyInlist: bool = False):
    """Gets the most recent profile filename from the
    LOGS directory.

        Returns:
            latest_log (str): filename of most recent profile
    """
    ma = MesaInlist(
        infile=infile,
        outfile="foo",
        legacyInlist=legacyInlist,
    ).inlist
    try:
        log_prefix = ma["profile_data_prefix"]
    except KeyError:
        log_prefix = "profile"
    try:
        log_dir = ma["log_directory"]
    except KeyError:
        log_dir = "LOGS"

    log_fnames = log_prefix + "*.data"
    src = os.path.join(log_dir, log_fnames)
    list_of_logs = glob.glob(src)

    if list_of_logs:
        latest_log = max(list_of_logs, key=os.path.getctime)
    else:
        print("failed in get_latest_log")
        latest_log = ""

    return latest_log
