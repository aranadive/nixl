#!/bin/bash
# SPDX-FileCopyrightText: Copyright (c) 2025-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Verifies whether the OBJ plugin linked cuObject (libcuobjclient) support,
# with severity that matches what the build environment actually promised:
#
#   1. No cuObject runtime in the base image at all -> nothing was ever
#      possible here. Skip silently.
#   2. Runtime present but the dev package (headers + pkg-config module)
#      wasn't discoverable -> the environment genuinely couldn't have linked
#      it. Warn loudly and let the build continue with S3 acceleration
#      disabled; this is a config/environment gap, not a build defect.
#   3. Runtime AND dev package both present, yet libplugin_OBJ.so still
#      doesn't link libcuobjclient -> everything needed was available and it
#      still didn't happen. That is a real build regression: fail the build.
#
# The "dev package discoverable" check reuses pkg-config --list-all (the
# same mechanism meson.build's cuobjclient probe uses), rather than
# independently re-deriving header/pc file paths, so this check can never
# disagree with what meson actually saw at configure time.
#
# Usage: verify-cuobj-plugin.sh <nixl-install-prefix>

set -euo pipefail

NIXL_PREFIX="${1:?usage: $0 <nixl-install-prefix>}"

CUDA_HOME_RESOLVED="$(readlink -f /usr/local/cuda 2>/dev/null || true)"
if [ -z "$CUDA_HOME_RESOLVED" ] || [ ! -d "$CUDA_HOME_RESOLVED" ]; then
    echo "cuObject: no CUDA toolkit in this image, skipping OBJ plugin check"
    exit 0
fi

TARGET_DIR="$(echo "$CUDA_HOME_RESOLVED"/targets/*-linux)"

if ! ls "$TARGET_DIR"/lib/libcuobjclient.so.1.* >/dev/null 2>&1; then
    echo "cuObject: no runtime in base, skipping OBJ plugin check"
    exit 0
fi

OBJ_PLUGIN="$(find "$NIXL_PREFIX" -name libplugin_OBJ.so -print -quit)"
if [ -z "$OBJ_PLUGIN" ]; then
    echo "ERROR: cuObject runtime is present but libplugin_OBJ.so was not built at all" >&2
    exit 1
fi

DEV_OK="false"
if ! command -v pkg-config >/dev/null 2>&1; then
    echo "cuObject: pkg-config binary not found in this image; cuobjclient dev package" >&2
    echo "cuObject: could not have been discovered by meson. S3 acceleration is NOT" >&2
    echo "cuObject: compiled in. This is an environment gap, not failing the build." >&2
elif ! pkg-config --list-all 2>/dev/null | grep -q '^cuobjclient-'; then
    echo "cuObject: no cuobjclient-<version> pkg-config module discoverable (dev package" >&2
    echo "cuObject: missing or not on PKG_CONFIG_PATH). S3 acceleration is NOT compiled" >&2
    echo "cuObject: in. This is an environment gap, not failing the build." >&2
else
    DEV_OK="true"
fi

if [ "$DEV_OK" != "true" ]; then
    exit 0
fi

# Both the runtime and the dev package were discoverable, so meson should
# have found cuobjclient and linked it. If it didn't, that's a real
# regression (e.g. the pkg-config version-list bug from #2228, or something
# in this image breaking pkg-config discovery outright) - fail loudly.
if readelf -d "$OBJ_PLUGIN" | grep -q libcuobjclient; then
    echo "cuObject: libplugin_OBJ.so links libcuobjclient"
else
    echo "ERROR: cuobjclient runtime + dev package are both present, but" >&2
    echo "ERROR: libplugin_OBJ.so does not link libcuobjclient. S3 acceleration" >&2
    echo "ERROR: should have compiled in and did not - this is a build regression." >&2
    exit 1
fi
