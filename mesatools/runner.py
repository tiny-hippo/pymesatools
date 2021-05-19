import os
import sys
import glob
import subprocess
import datetime
import numpy as np
import mesa_reader as mr
from shutil import copy2, move
from distutils.dir_util import copy_tree
from mesatools.access import MesaAccess


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
        infile,
        mesaVersion=15140,
        expandVectors=True,
        reloadDefaults=False,
        useMesaenv=True,
        pgstar=True,
        pause=True,
    ):
        """__init__ method

        Args:
            infile (str): Name of the inlist used in the run.
            mesaVersion (int): MESA release version.
            expandVectors (bool): Expand fortran vectors in the inlist.
            reloadDefaults (bool): Reload default inlist files.
            useMesaenv (bool): Use MESA_ENV environment variable.
            pgstar (bool): Enable/disable pgstar.
            pause (bool): Enable/disable waiting for user input at the end.
        """
        self.inlist = infile
        self.last_inlist = infile
        self.mesaVersion = mesaVersion
        self.expandVectors = expandVectors
        self.reloadDefaults = reloadDefaults
        self.useMesaenv = useMesaenv
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

    def run(self, check_age=True):
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

    def run_support(self, inlist, check_age):
        """Helper function for running MESA.

        Args:
            inlist (str): Inlist to run.
            check_age (bool): Check whether the output
                              model has the desired max_age.
        """

        # to-do: implement option to store terminal
        # output in a log file
        if not self.inlist == "inlist":
            self.remove_file("inlist")
        self.remove_file("restart_photo")
        copy2(self.inlist, "inlist")
        ma = MesaAccess(
            "inlist",
            "inlist",
            self.mesaVersion,
            self.expandVectors,
            self.reloadDefaults,
            self.useMesaenv,
        )
        self.model_name = ma["save_model_filename"]
        try:
            self.profile_name = ma["filename_for_profile_when_terminate"]
        except KeyError:
            self.profile_name = "profile.data"

        try:
            self.history_name = ma["star_history_name"]
        except KeyError:
            self.history_name = "history.data"

        if self.pause:
            ma["pause_before_terminate"] = True
        else:
            ma["pause_before_terminate"] = False

        if self.pgstar:
            ma["pgstar_flag"] = True
        else:
            ma["pgstar_flag"] = False

        if self.pause or self.pgstar:
            ma.writeFile()

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
                max_age = ma["max_age"]

                if star_age < max_age:
                    print(42 * "%")
                    print(
                        "Star age is {:.2E}, while max age is {:.2E}".format(
                            star_age, max_age
                        )
                    )
                    print(
                        "Failed to complete",
                        inlist,
                        "after {} h:mm:ss".format(run_time[:micro_index]),
                    )
                    print(42 * "%")
                    self.convergence = False
                else:
                    print(42 * "%")
                    print(
                        "Evolving the star took:",
                        "{} h:mm:ss".format(run_time[:micro_index]),
                    )
                    print(42 * "%")
                    self.convergence = True
            else:
                print(42 * "%")
                print(f"Could not find profile {self.profile_name}")
                print(
                    "Failed to complete",
                    inlist,
                    "after {} h:mm:ss".format(run_time[:micro_index]),
                )
                print(42 * "%")
                self.convergence = False

        else:
            if os.path.isfile(self.model_name):
                print(42 * "%")
                print(
                    "Evolving the star took:",
                    "{} h:mm:ss".format(run_time[:micro_index]),
                )
                print(42 * "%")
                self.convergence = True
            else:
                print(42 * "%")
                print(f"Could not find model {self.model_name}")
                print(
                    "Failed to complete",
                    inlist,
                    "after {} h:mm:ss".format(run_time[:micro_index]),
                )
                print(42 * "%")
                self.convergence = False

    def restart(self, photo):
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

    def restart_latest(self):
        """ Restarts the run from the latest photo. """
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

    def copy_logs(self, dir_name):
        """Save the current logs and profile.

        Args:
            dir_name (str): Destination to copy the logs to.
        """
        if not (self.profile_name):
            ma = MesaAccess(
                self.inlist,
                "_",
                self.mesaVersion,
                self.expandVectors,
                self.reloadDefaults,
                self.useMesaenv,
            )
            self.profile_name = ma["filename_for_profile_when_terminate"]

        dst = os.path.join(dir_name, self.profile_name)
        copy_tree("LOGS", dir_name)
        if os.path.isfile(self.profile_name):
            move(self.profile_name, dst)

    @staticmethod
    def make():
        """ Builds the star executable. """
        print("Building star")
        subprocess.call("./mk")

    @staticmethod
    def cleanup(keep_png=False, keep_logs=False, keep_photos=True):
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
    def remove_file(file_name):
        """Safely removes a file.

        Args:
            file_name (str): File to delete.
        """
        if os.path.isfile(file_name):
            os.remove(file_name)
