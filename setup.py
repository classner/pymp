# -*- coding: utf-8 -*-
"""
The setup script for the entire project.
@author: Christoph Lassner
"""
from setuptools import find_packages, setup

VERSION = "0.4.5"

setup(
    name="pymp-pypi",
    author="Christoph Lassner",
    author_email="mail@christophlassner.de",
    packages=find_packages(),
    version=VERSION,
    test_suite="tests.unittests",
    license="MIT License",
    url="https://github.com/classner/pymp",
    download_url="https://github.com/classner/pymp/tarball/v{0}".format(VERSION),
    keywords=["multiprocessing", "openmp", "parallelism"],
)
