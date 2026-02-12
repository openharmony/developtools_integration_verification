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
Generate reference_data.json from OpenHarmony README.OpenSource files.

This script scans the OpenHarmony repository for README.OpenSource files,
extracts relevant metadata (Name, License, Version Number, Upstream URL),
and generates a reference data JSON file for validation purposes.
"""

import argparse
import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

# Import SPDX license converter
from spdx_converter import SPDXLicenseConverter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Required fields for reference data
REQUIRED_FIELDS = {"Name", "License", "Version Number", "Upstream URL"}


def find_readme_files(root_dir: str) -> List[str]:
    """
    Find all README.OpenSource files recursively.

    Args:
        root_dir: Root directory to search for README.OpenSource files.

    Returns:
        List of absolute paths to README.OpenSource files.
    """
    readme_files = []
    root_path = Path(root_dir)

    if not root_path.exists():
        logger.error(f"Root directory does not exist: {root_dir}")
        return readme_files

    if not root_path.is_dir():
        logger.error(f"Root path is not a directory: {root_dir}")
        return readme_files

    for file_path in root_path.rglob("README.OpenSource"):
        readme_files.append(str(file_path))

    logger.info(f"Found {len(readme_files)} README.OpenSource files")
    return readme_files


def extract_reference_data(
    readme_path: str,
    converter: Optional[SPDXLicenseConverter] = None
) -> Optional[Dict[str, str]]:
    """
    Extract Name, License, Version Number, Upstream URL from README.OpenSource.

    Args:
        readme_path: Path to the README.OpenSource file.
        converter: Optional SPDX license converter for standardizing license names.

    Returns:
        Dictionary with extracted fields, or None if extraction fails.
    """
    try:
        with open(readme_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Malformed JSON in {readme_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error reading {readme_path}: {e}")
        return None

    # Handle non-list JSON (skip)
    if not isinstance(data, list):
        logger.error(f"Expected JSON list in {readme_path}, got {type(data).__name__}")
        return None

    # Handle empty list
    if len(data) == 0:
        logger.warning(f"Empty list in {readme_path}")
        return None

    # Extract first component from the list
    component = data[0]

    # Validate required fields exist
    missing_fields = REQUIRED_FIELDS - set(component.keys())
    if missing_fields:
        logger.warning(
            f"Missing required fields {missing_fields} in {readme_path}"
        )
        return None

    # Extract only the required fields
    license_value = component["License"]

    # Convert license to SPDX standard if converter is provided
    if converter:
        original_license = license_value
        license_value = converter.convert(license_value)
        if original_license != license_value:
            logger.debug(
                f"License converted: '{original_license}' -> '{license_value}' "
                f"in {readme_path}"
            )

    return {
        "Name": component["Name"],
        "License": license_value,
        "Version Number": component["Version Number"],
        "Upstream URL": component["Upstream URL"],
    }


def generate_reference_data(
    ohos_root: str,
    output_path: str,
    deduplicate: bool = True,
    spdx_json_path: Optional[str] = None,
    convert_spdx: bool = True
) -> None:
    """
    Main function to generate reference data JSON file.

    Args:
        ohos_root: Path to OpenHarmony repository root.
        output_path: Output path for reference_data.json.
        deduplicate: If True, keep first occurrence of duplicate names.
        spdx_json_path: Path to SPDX license mapping JSON file.
        convert_spdx: If True, convert license names to SPDX standard.
    """
    # Initialize SPDX converter if enabled
    converter = None
    if convert_spdx:
        try:
            converter = SPDXLicenseConverter(spdx_json_path)
            logger.info("SPDX license conversion enabled")
        except Exception as e:
            logger.warning(f"Failed to initialize SPDX converter: {e}")
            logger.warning("Continuing without SPDX conversion")
    # Find all README.OpenSource files
    readme_files = find_readme_files(ohos_root)

    if not readme_files:
        logger.error("No README.OpenSource files found")
        return

    # Extract reference data from each file
    reference_data = []
    seen_names = set()

    for readme_path in readme_files:
        data = extract_reference_data(readme_path, converter)

        if data is None:
            continue

        name = data["Name"]

        # Handle duplicate names
        if deduplicate:
            if name in seen_names:
                logger.warning(f"Duplicate name '{name}' found in {readme_path}, skipping")
                continue
            seen_names.add(name)

        reference_data.append(data)

    # Sort by Name alphabetically
    reference_data.sort(key=lambda x: x["Name"])

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Write to output file
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(reference_data, f, indent=2, ensure_ascii=False)

    logger.info(f"Generated {output_path} with {len(reference_data)} entries")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate reference_data.json from OpenHarmony repo"
    )
    parser.add_argument(
        "--ohos-root",
        default="/home/jinguang/opensource/ohos",
        help="Path to OpenHarmony repository root"
    )
    parser.add_argument(
        "--output",
        default="test/reference_data.json",
        help="Output path for reference_data.json"
    )
    parser.add_argument(
        "--keep-duplicates",
        action="store_true",
        help="Keep all entries including duplicate names (default: remove duplicates)"
    )
    parser.add_argument(
        "--spdx-json",
        default=None,
        help="Path to SPDX license mapping JSON file (default: data/spdx.json)"
    )
    parser.add_argument(
        "--no-spdx-convert",
        action="store_true",
        help="Disable SPDX license standardization (default: enabled)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    generate_reference_data(
        args.ohos_root,
        args.output,
        deduplicate=not args.keep_duplicates,
        spdx_json_path=args.spdx_json,
        convert_spdx=not args.no_spdx_convert
    )


if __name__ == "__main__":
    main()
