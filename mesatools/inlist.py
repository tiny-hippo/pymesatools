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
        suppressWarnings: bool = False
    ) -> None:

        self.inlist = MesaAccess(
            infile=infile,
            outfile=outfile,
            expandVectors=expandVectors,
            reloadDefaults=reloadDefaults,
            useMesaenv=useMesaenv,
            legacyInlist=legacyInlist,
            suppressWarnings=suppressWarnings
        )

    def writeInlist(self) -> None:
        self.inlist.writeFile()
