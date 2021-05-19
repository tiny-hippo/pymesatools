import numpy as np
import matplotlib.pyplot as plt
from os.path import join


class MesaDebugger:
    """Helps with trying to find the locations in the planet/star
    where convergence issues arise. Based on Bill Wolf's version.
    """

    def __init__(
        self,
        name="corr_lnd",
        dir=join(".", "plot_data", "solve_logs"),
        min_zone=1,
        max_zone=None,
    ):

        self.name = name
        self.dir = dir
        self.min_zone = min_zone
        self.max_zone = max_zone
        self.fig = self.make_iter_plot(
            name, dir=dir, min_zone=min_zone, max_zone=max_zone
        )

    @staticmethod
    def num_columns_rows(size_file):
        """Reads the size file and returns the number of
        columns and rows in a tuple.
        """
        with open(size_file) as file:
            data = file.read().split()
        return (int(data[0]), int(data[1]))

    @staticmethod
    def format_data(data_file, num_cols, num_rows):
        """ Reads data from file and reshapes it to be an n x m array. """
        data = np.genfromtxt(data_file)
        return data.reshape((num_rows, num_cols))

    def plot_data(
        self, data_file, num_cols, num_rows, min_zone=1, max_zone=None, title=None
    ):
        """Makes and returns a plot of the data from a hydro dump.

        Args:
            data_file (str): path to file from which to plot
            num_cols (int): number of columns the data should have
            num_rows (int): number of rows the data should have
            min_zone (int): outermost zone to be plotted
                            (default is 1 for surface)
            max_zone (int): innermost zone to be plotted
                            (default is None for center)

        Returns:
            matplotlib.pyplot.figure instance
        """
        if max_zone is None:
            max_zone = num_cols
        self.data = self.format_data(data_file, num_cols, num_rows)
        minmax = max([-min(self.data.flatten()), max(self.data.flatten())])

        fig, ax = plt.subplots(1, 1, figsize=(12, 8))
        if title is not None:
            ax.set_title(title)
        im = ax.imshow(
            self.data,
            aspect="auto",
            cmap="RdBu",
            origin="lower",
            extent=(1, num_cols, 1, num_rows),
            vmin=-minmax,
            vmax=minmax,
        )
        ax.set_xlabel("Zone")
        ax.set_ylabel("Iteration")
        ax.set_xlim(max_zone, min_zone)
        fig.colorbar(im)
        fig.tight_layout()

        return fig

    def make_iter_plot(
        self, name, dir=join(".", "plot_data", "solve_logs"), min_zone=1, max_zone=None
    ):
        """Wrapper for plot_data.

        Args:
            name (str): name of parameter to plot (found in names.data)
            dir (str): path to data files from hydro dump.
            min_zone (int): outermost zone to be plotted
                            (default is 1 for surface)
            max_zone (int): innermost zone to be plotted
                            (default is None for center)

        Returns:
            matplotlib.pyplot.figure instance
        """
        self.data_file = join(dir, "{}.log".format(name))
        self.size_file = join(dir, "size.data")
        self.num_cols, self.num_rows = self.num_columns_rows(self.size_file)

        return self.plot_data(
            self.data_file,
            self.num_cols,
            self.num_rows,
            min_zone=min_zone,
            max_zone=max_zone,
            title=name.replace("_", " "),
        )

    def save_fig(self):
        self.fig.savefig(self.name + ".pdf")
