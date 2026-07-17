#!/usr/bin/env python3

# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Validate that CUDA 13 wheels use, but do not bundle, cuObject Client."""

import argparse
import os
import re
import subprocess
import tempfile
import zipfile


CUOBJ_SONAME = "libcuobjclient.so.1"


def validate_wheel(wheel_path: str) -> None:
    with zipfile.ZipFile(wheel_path) as wheel:
        names = wheel.namelist()
        bundled_cuobj = [
            name
            for name in names
            if os.path.basename(name).startswith("libcuobjclient")
        ]
        if bundled_cuobj:
            raise RuntimeError(
                f"{wheel_path} unexpectedly bundles cuObject Client: {bundled_cuobj}"
            )

        obj_plugins = [
            name for name in names if os.path.basename(name) == "libplugin_OBJ.so"
        ]
        if len(obj_plugins) != 1:
            raise RuntimeError(
                f"{wheel_path} must contain exactly one libplugin_OBJ.so; "
                f"found {obj_plugins}"
            )

        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_path = wheel.extract(obj_plugins[0], tmpdir)
            dynamic = subprocess.run(
                ["readelf", "-d", plugin_path],
                check=True,
                capture_output=True,
                text=True,
            ).stdout

    needed = re.findall(r"\(NEEDED\).*?\[(.*?)\]", dynamic)
    if CUOBJ_SONAME not in needed:
        raise RuntimeError(
            f"{wheel_path} OBJ plugin does not require {CUOBJ_SONAME}; "
            f"DT_NEEDED={needed}"
        )

    print(f"Validated external cuObject linkage: {wheel_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wheels", nargs="+", help="CUDA 13 wheel files to validate")
    args = parser.parse_args()
    for wheel_path in args.wheels:
        validate_wheel(wheel_path)


if __name__ == "__main__":
    main()
