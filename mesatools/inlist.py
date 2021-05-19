from mesatools.access import MesaAccess


class MesaInlist:
    """Wrapper to read & write MESA inlists.

    Args:
        infile (str): Name of the inlist to use as a source.
        outfile (str): Name of the output file.
        mesaVersion (int): MESA release version.
        expandVectors (bool): Expand fortran vectors in the inlist.
        reloadDefaults (bool): Reload default inlist files.
        useMesaenv (bool): Use MESA_ENV environment variable.

    Attributes:

    To-do: Change this to work with setting 'extra_star_job_inlist1_name
    """

    def __init__(
        self,
        infile,
        outfile,
        mesaVersion=15140,
        expandVectors=True,
        reloadDefaults=False,
        useMesaenv=True,
    ) -> None:

        self.inlist = MesaAccess(
            infile, outfile, mesaVersion, expandVectors, reloadDefaults, useMesaenv
        )

    def writeInlist(self) -> None:
        self.inlist.writeFile()
