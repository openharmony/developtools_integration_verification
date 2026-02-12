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
SPDX License Matcher for Excel files.

This tool processes Excel files containing license information and
matches them to SPDX standard license identifiers.
"""

import argparse
import logging
import sys
from typing import Optional

import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Try to import SPDX converter, fallback to basic implementation
try:
    from spdx_converter import SPDXLicenseConverter
    SPDX_AVAILABLE = True
except ImportError:
    SPDX_AVAILABLE = False
    logger.warning("SPDX converter not available, using basic matching")


class SPDXLicenseMatcher:
    """
    Match license names in Excel files to SPDX standard identifiers.

    This class processes Excel files containing license information,
    converts license names to SPDX standard identifiers, and outputs
    the results to a new Excel file.
    """

    def __init__(
        self,
        input_excel_path: str,
        input_json_path: Optional[str] = None
    ) -> None:
        """
        Initialize the SPDX License Matcher.

        Args:
            input_excel_path: Path to input Excel file.
            input_json_path: Path to SPDX license mapping JSON file.
                            If None, uses default path from SPDXLicenseConverter.
        """
        self.df = pd.read_excel(input_excel_path)

        # Initialize SPDX converter
        if SPDX_AVAILABLE:
            self.converter = SPDXLicenseConverter(input_json_path)
        else:
            self.converter = None
            logger.warning("SPDX conversion disabled")

    def copy_url_column(self) -> None:
        """Copy cc_url to match_url for reference."""
        if "cc_url" in self.df.columns:
            self.df["match_url"] = self.df["cc_url"]
        else:
            logger.warning("cc_url column not found")

    def match_license_column(self, license_column: str = "spdx_fixed_license_name") -> None:
        """
        Match licenses in specified column to SPDX standard identifiers.

        Args:
            license_column: Name of column containing license names.
                          Default is "spdx_fixed_license_name".
        """
        if license_column not in self.df.columns:
            logger.error(f"Column '{license_column}' not found in Excel file")
            logger.info(f"Available columns: {list(self.df.columns)}")
            return

        if self.converter:
            self.df["match_license"] = self.df[license_column].apply(self._convert_with_spdx)
        else:
            self.df["match_license"] = self.df[license_column].apply(
                lambda x: x if pd.notna(x) else "No Match"
            )

        # Log summary
        matched = (self.df["match_license"] != "No Match").sum()
        total = len(self.df)
        logger.info(f"Matched {matched}/{total} licenses ({matched*100//total}%)")

    def _convert_with_spdx(self, license_names: str) -> str:
        """
        Convert license names to SPDX standard identifiers.

        Args:
            license_names: License names string (may contain multiple licenses).

        Returns:
            SPDX-standardized license string or "No Match".
        """
        if pd.isna(license_names):
            return "No Match"

        try:
            return self.converter.convert(str(license_names))
        except Exception as e:
            logger.debug(f"Conversion error for '{license_names}': {e}")
            return "No Match"

    def save_to_excel(self, output_excel_path: str) -> None:
        """
        Save the processed DataFrame to an Excel file.

        Args:
            output_excel_path: Path to output Excel file.
        """
        self.df.to_excel(output_excel_path, index=False)
        logger.info(f"Results saved to {output_excel_path}")

    def print_summary(self) -> None:
        """Print a summary of the matching results."""
        if "match_license" not in self.df.columns:
            logger.warning("No matching results to display")
            return

        print("\n" + "=" * 60)
        print("匹配结果摘要")
        print("=" * 60)

        # Count unique licenses
        original_licenses = self.df["spdx_fixed_license_name"].dropna().unique()
        matched_licenses = self.df["match_license"][self.df["match_license"] != "No Match"].unique()

        print(f"原始许可证数量: {len(original_licenses)}")
        print(f"匹配到的 SPDX 标识符: {len(matched_licenses)}")
        print(f"未匹配: {(self.df['match_license'] == 'No Match').sum()}")

        # Show unmatched licenses
        unmatched = self.df[self.df["match_license"] == "No Match"]["spdx_fixed_license_name"].unique()
        if len(unmatched) > 0:
            print(f"\n未匹配的许可证 ({len(unmatched)}):")
            for lic in sorted(unmatched):
                print(f"  - {lic}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Match OpenHarmony license names to SPDX standard licenses"
    )
    parser.add_argument(
        "input_excel",
        help="Path to input Excel file containing license data"
    )
    parser.add_argument(
        "input_json",
        nargs="?",
        default=None,
        help="Path to JSON file containing SPDX license mappings (optional)"
    )
    parser.add_argument(
        "output_excel",
        help="Path to output Excel file for matched results"
    )
    parser.add_argument(
        "-c", "--column",
        default="spdx_fixed_license_name",
        help="Name of column containing license names (default: spdx_fixed_license_name)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        matcher = SPDXLicenseMatcher(args.input_excel, args.input_json)
        # matcher.copy_url_column()  # Uncomment if needed
        matcher.match_license_column(args.column)
        matcher.save_to_excel(args.output_excel)
        matcher.print_summary()
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
