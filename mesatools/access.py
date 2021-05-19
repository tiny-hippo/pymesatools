import os
import re
import pickle
import f90nml
from pathlib import Path
from collections import OrderedDict
from typing import Tuple
from mesatools.support.definitions import *


class MesaAccess:
    """Reads & writes MESA inlists.
    Args:
        infile (str): Name of the inlist to use as a source.
        outfile (str): Name of the output file.
        mesaVersion (int): MESA release version.
        expandVectors (bool): Expand fortran vectors in the inlist.
        reloadDefaults (bool): Reload default inlist files.
        useMesaenv (bool): Use MESA_ENV environment variable.
    """

    def __init__(
        self,
        infile,
        outfile,
        mesaVersion=15140,
        expandVectors=True,
        reloadDefaults=False,
        useMesaenv=False,
    ) -> None:

        self.infile = infile
        self.outfile = outfile
        self.mesaVersion = mesaVersion
        self.expandVectors = expandVectors
        self.reloadDefaults = reloadDefaults
        self.useMesaenv = useMesaenv
        self.nml = f90nml.read(self.infile)
        self.nml.float_format = ".3e"

        self.controls = self.getDefaults("controls")
        self.pgstar = self.getDefaults("pgstar")
        self.star_job = self.getDefaults("star_job")
        if self.mesaVersion >= 15140:
            self.eos = self.getDefaults("eos")
            self.kap = self.getDefaults("kap")

        self.controls_keys = self.controls[sectionControls].keys()
        self.pgstar_keys = self.pgstar[sectionPgStar].keys()
        self.star_job_keys = self.star_job[sectionStarJob].keys()
        if self.mesaVersion >= 15140:
            self.eos_keys = self.eos[sectionEos].keys()
            self.kap_keys = self.kap[sectionKap].keys()

        self.default_keys = (
            list(self.controls_keys) + list(self.pgstar_keys) + list(self.star_job_keys)
        )

        if self.mesaVersion >= 15140:
            self.default_keys = self.default_keys + (
                list(self.eos_keys) + list(self.kap_keys)
            )

        self.fullDict = OrderedDict()
        self.fullDict[sectionStarJob] = dict(self.star_job[sectionStarJob])
        self.fullDict[sectionControls] = dict(self.controls[sectionControls])
        self.fullDict[sectionPgStar] = dict(self.pgstar[sectionPgStar])
        if self.mesaVersion >= 15140:
            self.fullDict[sectionEos] = dict(self.eos[sectionEos])
            self.fullDict[sectionKap] = dict(self.kap[sectionKap])

        self.expandedVectors = False
        if self.expandVectors:
            self.fixVectors()
            self.expandedVectors = True

    def items(self):
        return self.nml.items()

    def keys(self):
        return self.nml.keys()

    def values(self):
        return self.nml.values()

    def __getitem__(self, key):
        try:
            whichSection = self.getSection(key)
        except KeyError:
            key = self.format_key(key)
            whichSection = self.getSection(key)
        _, key, _ = self.checkVector(key)
        return self.nml[whichSection][key]

    def __setitem__(self, key, value):
        # to-do: fix handling of vectors
        try:
            whichSection = self.getSection(key)
        except KeyError:
            key = self.format_key(key)
            whichSection = self.getSection(key)
        section = self.nml[whichSection]
        section_keys = section.keys()

        isVector, vectorKey, vectorIndex = self.checkVector(key)
        if vectorKey not in self.default_keys:
            raise KeyError(f"{vectorKey}is not a default MESA key.")

        if isVector:
            defaultValue = self.fullDict[whichSection][vectorKey]
            defaultType = type(defaultValue[0])
        else:
            defaultValue = self.fullDict[whichSection][key]
            defaultType = type(defaultValue)

        if not isinstance(value, defaultType):
            if isinstance(defaultValue, float) and isinstance(value, int):
                print(f"Warning: defaultValue for {key} is float, but value is int")
                pass
            elif isinstance(defaultValue, int) and isinstance(value, float):
                print(f"Warning: defaultValue for {key} is int, but value is float")
                pass
            else:
                raise ValueError(value, "is not the same as the default", defaultType)

        if isVector and vectorKey in section_keys:
            with open(self.infile, "r") as file:
                nml_idcs = []
                for line in file.readlines():
                    if vectorKey in line:
                        nml_idcs.append(self.checkVector(line)[-1])

            idcs = range(min(nml_idcs), max(nml_idcs) + 1)
            if vectorIndex not in idcs:
                self.nml[whichSection][key] = value

            else:
                loc = idcs.index(vectorIndex)
                vals = self.nml[whichSection][vectorKey]
                vals[loc] = value
                for i in range(len(vals)):
                    if not vals[i]:
                        vals[i] = defaultValue[0]
                # alternative idea: expand vectors
                # maybe do this in a pre-processing stage?
                # for i in range(len(vals)):
                #     newKey = vectorKey + "(" + str(idcs[i]) + ")"
                #     self.nml[whichSection][newKey] = vals[i]
                # del self.nml[whichSection][vectorKey]
                self.nml[whichSection][vectorKey] = vals

        else:
            self.nml[whichSection][key] = value

    def __delitem__(self, key) -> None:
        _, key, _ = self.checkVector(key)
        if key not in self.default_keys:
            raise KeyError(f"{key} is not a default MESA key.")

        try:
            whichSection = self.getSection(key)
        except KeyError:
            key = self.format_key(key)
            whichSection = self.getSection(key)
        section = self.nml[whichSection]
        section_keys = section.keys()
        if key in section_keys:
            del self.nml[whichSection][key]
        else:
            raise KeyError(key, "is not in the current inlist.")

    def fixVectors(self) -> None:
        if self.expandedVectors:
            print("Vectors are already expanded.")
            return

        vectorKeys = []
        with open(self.infile, "r") as file:
            for line in file.readlines():
                line = line.strip()
                isVector, vectorKey, vectorIndex = self.checkVector(line)
                if isVector:
                    vectorKeys.append(vectorKey)

        vectorKeys = sorted(set(vectorKeys))
        for vectorKey in vectorKeys:
            try:
                whichSection = self.getSection(key)
            except KeyError:
                key = self.format_key(key)
                whichSection = self.getSection(key)
            nml_idcs = []
            with open(self.infile, "r") as file:
                for line in file.readlines():
                    if vectorKey in line:
                        nml_idcs.append(self.checkVector(line)[-1])
                idcs = range(min(nml_idcs), max(nml_idcs) + 1)
                vals = self.nml[whichSection][vectorKey]
                for i in range(len(vals)):
                    if vals[i] is None:
                        continue
                    else:
                        newKey = vectorKey + "(" + str(idcs[i]) + ")"
                        self.nml[whichSection][newKey] = vals[i]
            del self.nml[whichSection][vectorKey]

    def writeFile(self) -> None:
        with open(self.outfile, "w") as file:
            self.nml.write(file)

    def getDefaults(self, whichDefaults) -> dict:
        if self.useMesaenv:
            defaultsDir = self.getDefaultsDir(mesaEnv, whichDefaults)
            pickleDir = Path(__file__).parent / "defaults/"
        else:
            if self.mesaVersion == 15140:
                defaultsDir = Path(__file__).parent / "defaults/mesa-r15140/"
                pickleDir = Path(__file__).parent / "defaults/mesa-r15140/"
            else:
                defaultsDir = Path(__file__).parent / "defaults/mesa-r10108/"
                pickleDir = Path(__file__).parent / "defaults/mesa-r10108/"
        tempDir = Path(__file__).parent / "defaults/"

        if whichDefaults not in defaultsDict.keys():
            raise BaseException(whichDefaults, "is not a valid option")

        src = os.path.join(defaultsDir, defaultsDict[whichDefaults])
        dst = os.path.join(tempDir, defaultsDict[whichDefaults])
        pickleFile = os.path.join(pickleDir, defaultsDict[whichDefaults] + ".pkl")
        defaults = ["&" + sectionDict[whichDefaults]]

        if os.path.exists(pickleFile) and not self.reloadDefaults:
            with open(pickleFile, "rb") as file:
                nml = pickle.load(file)
        else:
            with open(src, "r") as file:
                for line in file.readlines():
                    line = line.strip()
                    if line.startswith("!"):
                        continue
                    elif not line:
                        continue
                    else:
                        if "num_x_ctrls" in line:
                            line = line.replace("num_x_ctrls", "10")
                        defaults.append(line)
            defaults.append("/")

            with open(dst, "w") as file:
                for item in defaults:
                    file.write("%s\n" % item)

            nml = f90nml.read(dst)
            os.remove(dst)

            with open(pickleFile, "wb") as file:
                pickle.dump(nml, file)

        return nml

    def getSection(self, key) -> str:
        _, key, _ = self.checkVector(key)
        if key in self.controls_keys:
            whichSection = sectionControls
        elif key in self.pgstar_keys:
            whichSection = sectionPgStar
        elif key in self.star_job_keys:
            whichSection = sectionStarJob
        elif key in self.eos_keys:
            whichSection = sectionEos
        elif key in self.kap_keys:
            whichSection = sectionKap
        else:
            raise KeyError(f"{key} is not a default MESA key.")
        return whichSection

    @staticmethod
    def format_key(key):
        return key.lower()

    @staticmethod
    def getDefaultsDir(envVar, whichDefaults) -> str:
        try:
            mesaDir = os.environ[envVar]
        except KeyError:
            raise EnvironmentError("MESA_DIR is not set in your enviroment.")

        if not os.path.exists(mesaDir):
            raise FileNotFoundError("MESA directory " + mesaDir + " does not exist.")
        if whichDefaults in ["controls", "pgstar", "star_job"]:
            defaultsDir = os.path.join(mesaDir, defaultsPath)
        elif whichDefaults == "eos":
            defaultsDir = os.path.join(mesaDir, eos_defaultsPath)
        elif whichDefaults == "kap":
            defaultsDir = os.path.join(mesaDir, kap_defaultsPath)
        else:
            raise BaseException(whichDefaults, "is not a valid option")

        if not os.path.exists(defaultsDir):
            raise FileNotFoundError(
                "Defaults directory " + defaultsDir + " does not exist."
            )
        return defaultsDir

    @staticmethod
    def checkVector(key) -> Tuple[bool, str, int]:
        regex = r"(\w*) (\( [0-9]+ \))"
        match = re.search(regex, key, re.VERBOSE)
        isVector = False
        vectorKey = key
        vectorIndex = None
        if match:
            isVector = True
            vectorKey = match.group(1)
            vectorIndex = int(match.group(2)[1:-1])
        return isVector, vectorKey, vectorIndex


if __name__ == "__main__":
    ma = MesaAccess(
        "test/inlist.nml",
        "test/outlist.nml",
        mesaVersion=10108,
        expandVectors=True,
        reloadDefaults=True,
        useMesaenv=False,
    )
    ma["x_ctrl(6)"] = 6.0
    ma["x_ctrl(8)"] = 8.0
    ma["x_ctrl(7)"] = 0.7
    ma["x_ctrl(1)"] = 0.1
    ma["x_logical_ctrl(1)"] = True
    ma["pgstar_flag"] = False
    # ma["use_cms"] = False
    # ma["zbase"] = 0.01
    ma.writeFile()