from typing import Any

from mesatools.access import MesaAccess


class MesaInlist:
    """Wrapper to read & write MESA inlists.

    Args:
        infile (str): Name of the inlist to use as a source.
        outfile (str): Name of the output file.
        expandVectors (bool): Expand fortran vectors in the inlist.
        reloadDefaults (bool): Reload default inlist files.
        useMesaenv (bool): Use MESA_ENV environment variable.
        legacyInlist (bool): Legacy inlist (before mesa-r15140).

    Attributes:

    To-do: Change this to work with setting 'extra_star_job_inlist1_name
    """

    def __init__(
        self,
        infile: str,
        outfile: str,
        expandVectors: bool = True,
        reloadDefaults: bool = False,
        useMesaenv: bool = True,
        legacyInlist: bool = False,
        suppressWarnings: bool = False,
    ) -> None:
        self.inlist = MesaAccess(
            infile=infile,
            outfile=outfile,
            expandVectors=expandVectors,
            reloadDefaults=reloadDefaults,
            useMesaenv=useMesaenv,
            legacyInlist=legacyInlist,
            suppressWarnings=suppressWarnings,
        )

    def __getitem__(self, key: str) -> Any:
        return self.inlist.__getitem__(key=key)

    def __setitem__(self, key: str, value: float) -> None:
        self.inlist.__setitem__(key=key, value=value)

    def __delitem__(self, key: str) -> None:
        self.inlist.__delitem__(key=key)

    def items(self):
        return self.inlist.items()

    def keys(self):
        return self.inlist.keys()

    def values(self):
        return self.inlist.values()

    def writeInlist(self) -> None:
        self.inlist.writeFile()
