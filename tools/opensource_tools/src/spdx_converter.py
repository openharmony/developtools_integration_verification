#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2024 Huawei Device Co., Ltd.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
SPDX License Standardization Converter.

Converts various license name formats to SPDX standard identifiers.
"""

import json
import logging
import re
from pathlib import Path
from typing import Dict, Optional, Set

logger = logging.getLogger(__name__)


class SPDXLicenseConverter:
    """Convert license names to SPDX standard identifiers."""

    # Common license name variants that map to SPDX identifiers
    # These handle the most common non-standard formats found in README.OpenSource files
    COMMON_VARIANTS: Dict[str, str] = {
        # MIT variants
        "mit license": "MIT",
        "the mit license": "MIT",
        "mit": "MIT",

        # Apache variants
        "apache license v2.0": "Apache-2.0",
        "apache license 2.0": "Apache-2.0",
        "apache 2.0 license": "Apache-2.0",
        "apache v2": "Apache-2.0",
        "apache v2.0": "Apache-2.0",
        "apache license v2": "Apache-2.0",
        "apache 2 license": "Apache-2.0",
        "apache 2.0 with llvm exception": "Apache-2.0 WITH LLVM-exception",
        "apache license v2.0 with llvm exception": "Apache-2.0 WITH LLVM-exception",
        "apache license 2.0 with llvm exception": "Apache-2.0 WITH LLVM-exception",
        "apache license 2.0 with runtime library exception": "Apache-2.0 WITH LLVM-exception",
        "apache-2.0 with runtime library exceptions": "Apache-2.0 WITH LLVM-exception",
        "apache 2.0 with runtime library exceptions": "Apache-2.0 WITH LLVM-exception",

        # BSD variants
        "bsd 3-clause license": "BSD-3-Clause",
        "bsd 2-clause license": "BSD-2-Clause",
        "bsd 3 license": "BSD-3-Clause",
        "bsd 2 license": "BSD-2-Clause",
        "bsd 3-clause": "BSD-3-Clause",
        "bsd 2-clause": "BSD-2-Clause",

        # GPL variants - map to -only by default
        "gpl v2.0": "GPL-2.0-only",
        "gpl v2": "GPL-2.0-only",
        "gpl v3.0": "GPL-3.0-only",
        "gpl v3": "GPL-3.0-only",
        "gpl-2.0": "GPL-2.0-only",
        "gpl-2": "GPL-2.0-only",
        "gpl-3": "GPL-3.0-only",
        "gpl v2.0+": "GPL-2.0-or-later",
        "gpl v2+": "GPL-2.0-or-later",
        "gpl-2.0+": "GPL-2.0-or-later",

        # LGPL variants - map to -only by default
        "lgpl v2.1": "LGPL-2.1-only",
        "lgpl v2.0": "LGPL-2.0-only",
        "lgpl v3.0": "LGPL-3.0-only",
        "lgpl-2.1": "LGPL-2.1-only",
        "lgpl-2.0": "LGPL-2.0-only",
        "lgpl-3.0": "LGPL-3.0-only",
        "lgpl-2": "LGPL-2.0-only",
        "lgpl-3": "LGPL-3.0-only",
        "lgpl-2.1+": "LGPL-2.1-or-later",
        "lgpl v2.1+": "LGPL-2.1-or-later",

        # Other common licenses
        "isc license": "ISC",
        "zlib license": "Zlib",
        "zlib/libpng license": "Zlib",
        "libpng license": "Libpng",
        "python software foundation license v2": "Python-2.0",
        "public domain": "0BSD",
        "the freetype project license": "FTL",
        "freetype project license": "FTL",
        "jpeg license": "IJG",
        "unicode 3.0": "Unicode-3.0",
        "unicode license": "Unicode-3.0",
        "sun microsystems license": "SunPro",
        "mulan permissive software license，version 2": "MulanPSL-2.0",
        "bzip2 license": "bzip2-1.0.6",
        "miros license": "MirOS",
        "free software foundation - mit license": "MIT",

        # LPPL variants
        "lppl-1": "LPPL-1.0",
        "lppl 1": "LPPL-1.0",
        "lppl-1.3": "LPPL-1.3c",
        "latex project public license 1.0": "LPPL-1.0",
        "latex project public license 1.3": "LPPL-1.3c",

        # CNRI licenses
        "cnri-python-gpl-compatible": "CNRI-Python-GPL-Compatible",

        # Unicode licenses
        "unicode-dfs-2022": "Unicode-DFS-2022",  # Not in SPDX, keep as-is
    }

    # Licenses that need -only suffix when missing
    LICENSES_REQUIRING_ONLY: Set[str] = {
        "GPL-2.0", "GPL-3.0",
        "LGPL-2.0", "LGPL-2.1", "LGPL-3.0",
    }

    # Valid SPDX exceptions
    VALID_EXCEPTIONS: Set[str] = {
        "389-exception", "Asterisk-exception", "Asterisk-linking-protocols-exception",
        "Autoconf-exception-2.0", "Autoconf-exception-3.0", "Autoconf-exception-generic",
        "Autoconf-exception-generic-3.0", "Autoconf-exception-macro", "Bison-exception-1.24",
        "Bison-exception-2.2", "Bootloader-exception", "CGAL-linking-exception",
        "Classpath-exception-2.0", "Classpath-exception-2.0-short", "CLISP-exception-2.0",
        "cryptsetup-OpenSSL-exception", "Digia-Qt-LGPL-exception-1.1", "DigiRule-FOSS-exception",
        "eCos-exception-2.0", "erlang-otp-linking-exception", "Fawkes-Runtime-exception",
        "FLTK-exception", "fmt-exception", "Font-exception-2.0", "freertos-exception-2.0",
        "GCC-exception-2.0", "GCC-exception-2.0-note", "GCC-exception-3.1", "Gmsh-exception",
        "GNAT-exception", "GNOME-examples-exception", "GNU-compiler-exception",
        "gnu-javamail-exception", "GPL-3.0-389-ds-base-exception", "GPL-3.0-interface-exception",
        "GPL-3.0-linking-exception", "GPL-3.0-linking-source-exception", "GPL-CC-1.0",
        "GStreamer-exception-2005", "GStreamer-exception-2008", "harbour-exception",
        "i2p-gpl-java-exception", "Independent-modules-exception", "KiCad-libraries-exception",
        "kvirc-openssl-exception", "LGPL-3.0-linking-exception", "libpri-OpenH323-exception",
        "Libtool-exception", "Linux-syscall-note", "LLGPL", "LLVM-exception", "LZMA-exception",
        "mif-exception", "mxml-exception", "Nokia-Qt-exception-1.1", "OCaml-LGPL-linking-exception",
        "OCCT-exception-1.0", "OpenJDK-assembly-exception-1.0", "openvpn-openssl-exception",
        "PCRE2-exception", "polyparse-exception", "PS-or-PDF-font-exception-20170817",
        "QPL-1.0-INRIA-2004-exception", "Qt-GPL-exception-1.0", "Qt-LGPL-exception-1.1",
        "Qwt-exception-1.0", "romic-exception", "RRDtool-FLOSS-exception-2.0",
        "rsync-linking-exception", "SANE-exception", "SHL-2.0", "SHL-2.1",
        "Simple-Library-Usage-exception", "stunnel-exception", "SWI-exception", "Swift-exception",
        "Texinfo-exception", "u-boot-exception-2.0", "UBDL-exception", "Universal-FOSS-exception-1.0",
        "vsftpd-openssl-exception", "WxWindows-exception-3.1", "x11vnc-openssl-exception",
    }

    # Additional valid licenses not in standard SPDX (but commonly used)
    ADDITIONAL_VALID_LICENSES: Set[str] = {
        "Unicode-DFS-2022",  # Newer version of Unicode DFS license
    }

    def __init__(self, spdx_json_path: Optional[str] = None):
        """
        Initialize the SPDX license converter.

        Args:
            spdx_json_path: Path to spdx.json file. If None, uses default path.
        """
        if spdx_json_path is None:
            spdx_json_path = Path(__file__).parent.parent / "data" / "spdx.json"

        self.spdx_mapping: Dict[str, str] = self._load_spdx_data(spdx_json_path)
        self._build_normalized_lookup()
        self._build_spdx_id_set()

    def _load_spdx_data(self, json_path: str) -> Dict[str, str]:
        """Load SPDX license mappings from JSON file."""
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"SPDX JSON file not found: {json_path}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in SPDX file: {e}")
            return {}

    def _build_normalized_lookup(self) -> None:
        """Build a normalized lookup dictionary for fuzzy matching."""
        self._normalized_lookup: Dict[str, str] = {}
        for full_name, spdx_id in self.spdx_mapping.items():
            normalized = self._normalize_key(full_name)
            self._normalized_lookup[normalized] = spdx_id

    def _build_spdx_id_set(self) -> None:
        """Build a set of all valid SPDX identifiers for quick lookup."""
        self._valid_spdx_ids: Set[str] = set(self.spdx_mapping.values())

    @staticmethod
    def _normalize_key(name: str) -> str:
        """Normalize license name for lookup (remove punctuation, lowercase)."""
        # Remove all non-alphanumeric characters (except spaces)
        normalized = re.sub(r"[^a-zA-Z0-9 ]", "", name)
        return normalized.lower().strip()

    def convert(self, license_str: str) -> str:
        """
        Convert a license string to SPDX standard identifiers.

        Args:
            license_str: License string (may contain multiple licenses).

        Returns:
            SPDX-standardized license string.
        """
        if not license_str or license_str.lower() in ("null", "none"):
            return license_str

        # Handle separators: ; / , or OR // (case-insensitive for OR)
        # Note: Match "or" as whole word to avoid splitting "for" etc.
        separators = r"[;/,]|//|\sor\s"
        licenses = re.split(separators, license_str, flags=re.IGNORECASE)

        converted = []
        for lic in licenses:
            lic = lic.strip()
            if not lic:
                continue
            spdx_id = self._convert_single(lic)
            converted.append(spdx_id)

        return "; ".join(converted)

    def _convert_single(self, license_name: str) -> str:
        """Convert a single license name to SPDX identifier."""
        # First, normalize underscore WITH to space WITH
        normalized_input = license_name.replace("_WITH_", " WITH ")
        normalized_input = normalized_input.replace("_", "-")

        # Check if it's a valid WITH exception format
        if " WITH " in normalized_input:
            return self._normalize_with_exception(normalized_input)

        # Check if already a valid SPDX identifier
        if normalized_input in self._valid_spdx_ids:
            return normalized_input

        # Check if it's a license that needs -only suffix
        if normalized_input in self.LICENSES_REQUIRING_ONLY:
            return f"{normalized_input}-only"

        # Check common variants (case-insensitive)
        key = license_name.lower()
        if key in self.COMMON_VARIANTS:
            result = self.COMMON_VARIANTS[key]
            # Post-process result for WITH exception
            if " WITH " in result:
                return self._normalize_with_exception(result)
            return result

        # Try exact normalized match against SPDX database
        normalized = self._normalize_key(license_name)
        if normalized in self._normalized_lookup:
            result = self._normalized_lookup[normalized]
            # Check if result needs -only suffix
            if result in self.LICENSES_REQUIRING_ONLY:
                return f"{result}-only"
            return result

        # Try fuzzy match (contains all words)
        match = self._fuzzy_match(normalized)
        if match:
            if match in self.LICENSES_REQUIRING_ONLY:
                return f"{match}-only"
            return match

        # No match found - return original
        return license_name

    def _normalize_with_exception(self, license_str: str) -> str:
        """
        Normalize a WITH exception license string.

        Args:
            license_str: License string like "Apache-2.0 WITH LLVM-exception"

        Returns:
            Normalized SPDX identifier string.
        """
        # Split by " WITH "
        parts = license_str.split(" WITH ")
        if len(parts) != 2:
            return license_str

        base_license = parts[0].strip()
        exception = parts[1].strip()

        # Normalize the base license
        if base_license in self._valid_spdx_ids:
            normalized_base = base_license
        elif base_license in self.LICENSES_REQUIRING_ONLY:
            normalized_base = f"{base_license}-only"
        else:
            # Try to convert the base license
            normalized_base = self._convert_single(base_license)

        # Normalize the exception
        # Check if exception is valid
        if exception in self.VALID_EXCEPTIONS:
            normalized_exception = exception
        else:
            # Try to find the exception (case-insensitive)
            for valid_exc in self.VALID_EXCEPTIONS:
                if exception.lower() == valid_exc.lower():
                    normalized_exception = valid_exc
                    break
            else:
                # Unknown exception, keep as is
                normalized_exception = exception

        return f"{normalized_base} WITH {normalized_exception}"

    def _is_spdx_identifier(self, license_name: str) -> bool:
        """Check if the string appears to already be an SPDX identifier."""
        # SPDX identifiers typically contain dashes and follow a pattern
        # Check against known SPDX identifiers from our mapping
        return license_name in self._valid_spdx_ids

    def _fuzzy_match(self, normalized: str) -> Optional[str]:
        """
        Try fuzzy matching for license names.

        Matches if all words in the input appear in a normalized SPDX name.
        """
        words = set(normalized.split())
        if not words:
            return None

        # Sort by number of matching words (most matches first)
        matches = []
        for norm_key, spdx_id in self._normalized_lookup.items():
            key_words = set(norm_key.split())
            if words.issubset(key_words):
                # Calculate match score
                match_score = len(words) / len(key_words)
                matches.append((match_score, spdx_id))

        if matches:
            # Return the best match (highest score, then shortest)
            matches.sort(key=lambda x: (-x[0], len(x[1])))
            return matches[0][1]

        return None

    def validate_spdx_id(self, spdx_id: str) -> bool:
        """
        Validate if a string is a valid SPDX identifier.

        Args:
            spdx_id: The SPDX identifier to validate.

        Returns:
            True if valid, False otherwise.
        """
        # Check additional valid licenses
        if spdx_id in self.ADDITIONAL_VALID_LICENSES:
            return True

        # Check if it's a WITH exception format
        if " WITH " in spdx_id:
            parts = spdx_id.split(" WITH ")
            if len(parts) != 2:
                return False
            base_license, exception = parts[0].strip(), parts[1].strip()
            return (base_license in self._valid_spdx_ids or base_license in self.ADDITIONAL_VALID_LICENSES) and exception in self.VALID_EXCEPTIONS

        # Regular SPDX identifier
        return spdx_id in self._valid_spdx_ids
