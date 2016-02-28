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
    packages=find_packages(exclude='unittests'),
    version=VERSION,
    test_suite='unittests.unittests',
    license='MIT License',
)
