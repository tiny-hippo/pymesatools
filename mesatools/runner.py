import datetime
import glob
import os
import subprocess
import sys
from distutils.dir_util import copy_tree
from shutil import copy2, move

import mesa_reader as mr
import numpy as np

from mesatools.inlist import MesaInlist


class MesaRunner:
    """Runs MESA using the desired inlist.

    It is also capable of various other useful manipulations.

    Attributes:
        inlist (str): Name of the inlist used in the run.
        last_inlist (str): Name of the last inlist to run.
        pgstar (bool): Enable/disable pgstar.
        pause (bool): Enable/disable waiting for user input at the end.
        check (bool): Checks whether the model successfully finished.
        model_name (str): Output model name.
        profile_name (str): Output profile name.
        history_name (str): Output history name.
    """

    def __init__(
        self,
        infile: str,
        pgstar: bool = True,
        pause: bool = True,
        expandVectors: bool = True,
        reloadDefaults: bool = False,
        useMesaenv: bool = True,
        legacyInlist: bool = True,
    ):
        """__init__ method

        Args:
            infile (str): Name of the inlist used in the run.
            pgstar (bool): Enable/disable pgstar.
            pause (bool): Enable/disable waiting for user input at the end.
            expandVectors (bool): Expand fortran vectors in the inlist.
            reloadDefaults (bool): Reload default inlist files.
            useMesaenv (bool): Use MESA_ENV environment variable.
            legacyInlist (bool): Legacy inlist (before mesa-r15140).
        """
        self.inlist = infile
        self.last_inlist = infile
        self.expandVectors = expandVectors
        self.reloadDefaults = reloadDefaults
        self.useMesaenv = useMesaenv
        self.legacyInlist = legacyInlist
        self.pause = pause
        self.pgstar = pgstar
        self.model_name = ""
        self.profile_name = ""
        self.history_name = ""
        self.run_time = 0

        self.convergence = False
        if isinstance(self.inlist, list):
            self.summary = np.zeros_like(self.inlist, dtype=bool)
        else:
            self.summary = False

    def run(self, check_age: bool = True) -> None:
        """Runs either a single inlist or a list of inlists.

        args:
            check_age (bool): Check whether the output
                              model has the desired max_age.
        """
        if isinstance(self.inlist, list):
            for ind, item in enumerate(self.inlist):
                self.last_inlist = item
                self.run_support(item, check_age)
                self.summary[ind] = self.convergence
                if not (self.convergence):
                    raise SystemExit("Aborting since", item, "failed to converge")

            print("Finished running inlists", self.inlist)
        else:
            self.run_support(self.inlist, check_age)

    def run_support(self, inlist: str, check_age: bool) -> None:
        """Helper function for running MESA.

        Args:
            inlist (str): Inlist to run.
            check_age (bool): Check whether the output
                              model has the desired max_age.
        """

        # to-do: implement option to store terminal
        # output in a log file
        if self.inlist != "inlist":
            self.remove_file("inlist")
        self.remove_file("restart_photo")
        copy2(self.inlist, "inlist")
        inList = MesaInlist(
            infile="inlist",
            outfile="inlist",
            expandVectors=self.expandVectors,
            reloadDefaults=self.reloadDefaults,
            useMesaenv=self.useMesaenv,
            legacyInlist=self.legacyInlist,
            suppressWarnings=False,
        )
        self.model_name = inList["save_model_filename"]
        try:
            self.profile_name = inList["filename_for_profile_when_terminate"]
        except KeyError:
            self.profile_name = "profile.data"

        try:
            self.history_name = inList["star_history_name"]
        except KeyError:
            self.history_name = "history.data"

        if self.pause:
            inList["pause_before_terminate"] = True
        else:
            inList["pause_before_terminate"] = False

        if self.pgstar:
            inList["pgstar_flag"] = True
        else:
            inList["pgstar_flag"] = False

        inList.writeInlist()

        self.remove_file(self.model_name)
        self.remove_file(self.profile_name)

        start_time = datetime.datetime.now()
        if os.path.isfile("star"):
            print("Running", inlist)
            subprocess.call("./star")
        else:
            print("You need to build star first!")
            sys.exit()
        end_time = datetime.datetime.now()
        run_time = str(end_time - start_time)
        self.run_time = run_time
        micro_index = run_time.find(".")

        if check_age:
            if os.path.isfile(self.profile_name):
                md = mr.MesaData(self.profile_name)
                star_age = md.star_age
                max_age = inList["max_age"]

                if star_age < max_age:
                    print(42 * "%")
                    print(f"Star age is {star_age:.2E}, while max age is {max_age:.2E}")
                    print(
                        "Failed to complete",
                        inlist,
                        f"after {run_time[:micro_index]} h:mm:ss",
                    )
                    print(42 * "%")
                    self.convergence = False
                else:
                    print(42 * "%")
                    print(
                        "Evolving the star took:",
                        f"{run_time[:micro_index]} h:mm:ss",
                    )
                    print(42 * "%")
                    self.convergence = True
            else:
                print(42 * "%")
                print(f"Could not find profile {self.profile_name}")
                print(
                    "Failed to complete",
                    inlist,
                    f"after {run_time[:micro_index]} h:mm:ss",
                )
                print(42 * "%")
                self.convergence = False

        else:
            if os.path.isfile(self.model_name):
                print(42 * "%")
                print(
                    "Evolving the star took:",
                    f"{run_time[:micro_index]} h:mm:ss",
                )
                print(42 * "%")
                self.convergence = True
            else:
                print(42 * "%")
                print(f"Could not find model {self.model_name}")
                print(
                    "Failed to complete",
                    inlist,
                    f"after {run_time[:micro_index]} h:mm:ss",
                )
                print(42 * "%")
                self.convergence = False

    def restart(self, photo: str) -> None:
        """Restarts the run from the given photo.

        Args:
            photo (str): Photo to run from in the photos directory.
        """
        if not (os.path.isfile("inlist")):
            copy2(self.last_inlist, "inlist")

        photo_path = os.path.join("photos", photo)
        if os.path.isfile(photo_path):
            subprocess.call(["./re", photo])
        else:
            print(photo_path, "not found")

    def restart_latest(self) -> None:
        """Restarts the run from the latest photo."""
        old_path = os.getcwd()
        new_path = os.path.expanduser("photos")
        os.chdir(new_path)
        latest_file = max(glob.iglob("*"), key=os.path.getctime)
        os.chdir(old_path)

        if not (os.path.isfile("inlist")):
            copy2(self.last_inlist, "inlist")

        if latest_file:
            print("Restarting with photo", latest_file)
            subprocess.call(["./re", latest_file])
        else:
            print("No photo found.")

    def copy_logs(self, dir_name: str) -> None:
        """Save the current logs and profile.

        Args:
            dir_name (str): Destination to copy the logs to.
        """
        if not (self.profile_name):
            inList = MesaInlist(
                infile="inlist",
                outfile="foo",
                expandVectors=self.expandVectors,
                reloadDefaults=self.reloadDefaults,
                useMesaenv=self.useMesaenv,
                legacyInlist=self.legacyInlist,
                suppressWarnings=False,
            ).inlist
            self.profile_name = inList["filename_for_profile_when_terminate"]

        dst = os.path.join(dir_name, self.profile_name)
        copy_tree("LOGS", dir_name)
        if os.path.isfile(self.profile_name):
            move(self.profile_name, dst)

    @staticmethod
    def make() -> None:
        """Builds the star executable."""
        print("Building star")
        subprocess.call("./mk")

    @staticmethod
    def cleanup(
        keep_png: bool = False, keep_logs: bool = False, keep_photos: bool = True
    ) -> None:
        """Cleans the photos, png and logs directories.

        Args:
            keep_png (bool): Store/delete the png directory.
            keep_logs (bool): Store/delete the logs directory.
            keep_photos (bool): Store/delete the photo directory.
        """
        if not (keep_png):
            dir_name = "png"
            if os.path.isdir(dir_name):
                items = os.listdir(dir_name)
                for item in items:
                    if item.endswith(".png"):
                        os.remove(os.path.join(dir_name, item))

        if not (keep_logs):
            dir_name = "LOGS"
            if os.path.isdir(dir_name):
                items = os.listdir(dir_name)
                for item in items:
                    if item.endswith(".data") or item.endswith(".index"):
                        os.remove(os.path.join(dir_name, item))

        if not (keep_photos):
            dir_name = "photos"
            if os.path.isdir(dir_name):
                items = os.listdir(dir_name)
                for item in items:
                    os.remove(os.path.join(dir_name, item))

    @staticmethod
    def remove_file(file_name: str) -> None:
        """Safely removes a file.

        Args:
            file_name (str): File to delete.
        """
        if os.path.isfile(file_name):
            os.remove(file_name)
