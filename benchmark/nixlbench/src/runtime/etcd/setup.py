#!/usr/bin/env python3

from pybind11.setup_helpers import Pybind11Extension, build_ext
from pybind11 import get_cmake_dir
import pybind11
from setuptools import setup, Extension
import os

# Define the extension module
ext_modules = [
    Pybind11Extension(
        "etcd_runtime",
        [
            "python_bindings.cpp",
            "etcd_rt.cpp",
        ],
        include_dirs=[
            # Path to pybind11 headers
            pybind11.get_include(),
            # Path to the parent directory (for runtime.h)
            "..",
            # Path to current directory
            ".",
        ],
        libraries=["etcd-cpp-api"],
        language='c++'
    ),
]

setup(
    name="etcd_runtime",
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
    zip_safe=False,
    python_requires=">=3.6",
)