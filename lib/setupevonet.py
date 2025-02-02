#!/usr/bin/env python

"""
This file belong to https://github.com/snolfi/evorobotpy
Author: Stefano Nolfi, stefano.nolfi@istc.cnr.it

setupevobet.py, python wrapper for evonet.cpp

This file is part of the python module net.so that include the following files:
evonet.cpp, evonet.h, utilities.cpp, utilities.h, net.pxd, net.pyx and setupevonet.py
And can be compile with cython with the commands: cd ./evorobotpy/lib; python3 setupevonet.py build_ext –inplace; cp net*.so ../bin
"""

from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize
from Cython.Distutils import build_ext
import numpy

# linux
#include_gsl_dir = "/usr/include/gsl"
#lib_gsl_dir = "/usr/lib/x86_64-linux-gnu"
# mac os


include_gsl_dir = "/usr/local/lib"


lib_gsl_dir = "/usr/local/include"

setup(
    cmdclass = {'build_ext': build_ext},
    ext_modules = [Extension("net",
                             sources=["net.pyx"],
                             language="c++",
                             include_dirs=[numpy.get_include(), include_gsl_dir],
			     libraries=["gsl", "gslcblas"],
			     library_dirs=[lib_gsl_dir])],
)


