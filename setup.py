from setuptools import setup

setup(
    name="mesatools",
    version="0.1",
    description="various tools to handle MESA with python",
    url="https://github.com/tiny-hippo/pyMesaToolbox",
    author="Simon Müller",
    author_email="simon.mueller7@uzh.ch",
    license="GNU GPLv3",
    packages=["mesatools"],
    install_requires=["numpy", "matplotlib", "f90nml", "mesa_reader"]
)
