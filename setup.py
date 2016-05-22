# -*- coding: utf-8 -*-
"""
The setup script for the entire project.
@author: Christoph Lassner
"""
from setuptools import setup, find_packages

VERSION = '0.1'

setup(
    name='pymp',
    author='Christoph Lassner',
    author_email='mail@christophlassner.de',
    packages=find_packages(),
    version=VERSION,
    test_suite='tests.unittests',
    license='MIT License',
)
