import os
import glob
from MesaTools import MesaAccess


class cd:
    """
    Directory changer. Can change the directory using the
    'with' keyword, and returns to the previous path
    after leaving intendation. Example:

    with cd("some/path/to/go"): # changing dir
        foo()
        ...
        bar()
    #back to old dir
    """

    def __init__(self, newPath):
        self.newPath = os.path.expanduser(newPath)

    def __enter__(self):
        self.savedPath = os.getcwd()
        os.chdir(self.newPath)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)


def get_latest_log():
    """Gets the most recent profile filename from the
    LOGS directory.

        Returns:
            latest_log (str): filename of most recent profile
    """
    ma = MesaAccess()
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


def get_X(Z):
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


def get_Y(Z):
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
