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
Generate README.OpenSource files for open source components.

This script provides interactive and command-line modes to create
standardized README.OpenSource files with SPDX license validation.
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Try to import SPDX converter, fallback if not available
try:
    from spdx_converter import SPDXLicenseConverter
    SPDX_AVAILABLE = True
except ImportError:
    SPDX_AVAILABLE = False
    logger.warning("SPDX converter not available, licenses will not be standardized")

# Required fields for README.OpenSource
REQUIRED_FIELDS = [
    "Name",
    "License",
    "License File",
    "Version Number",
    "Owner",
    "Upstream URL",
    "Description",
]


def ask_question(prompt: str, default_value: Optional[str] = None) -> str:
    """Prompt user for input with optional default value."""
    if default_value:
        value = input(f"{prompt} [{default_value}]: ").strip()
        return value or default_value
    return input(f"{prompt}: ").strip()


def ask_for_list(prompt: str) -> List[str]:
    """Prompt user for a list of items separated by commas."""
    value = input(f"{prompt} (多个项请用逗号分隔): ").strip()
    return [item.strip() for item in value.split(",")] if value else []


def process_license_info(
    converter: Optional["SPDXLicenseConverter"] = None
) -> Tuple[List[str], List[str]]:
    """
    Process license information and corresponding file paths.

    Args:
        converter: Optional SPDX license converter for standardization.

    Returns:
        Tuple of (license_list, license_file_list).
    """
    licenses = ask_question("请输入许可证名称（如有多个，用分号分隔）")
    license_files = ask_question("请输入许可证文件路径（如果有多个，请使用分号分隔）")

    license_list = (
        [license.strip() for license in licenses.split(";")] if licenses else []
    )
    license_file_list = (
        [file.strip() for file in license_files.split(";")] if license_files else []
    )

    # Validate input
    if not license_list or not license_file_list:
        raise ValueError("许可证和许可证文件路径不能为空。")

    # Check license and file path matching
    if len(license_list) != len(license_file_list):
        # Allow special cases: one license with multiple files, or multiple licenses with one file
        if not (
            (len(license_list) == 1 and len(license_file_list) > 1)
            or (len(license_list) > 1 and len(license_file_list) == 1)
        ):
            raise ValueError(
                "许可证和许可证文件的数量不匹配，必须是一对一、一对多或多对一的关系。"
            )

    # Convert licenses to SPDX standard if converter is available
    if converter and SPDX_AVAILABLE:
        original_list = license_list.copy()
        license_list = [converter.convert(lic) for lic in license_list]

        # Log conversions
        for orig, new in zip(original_list, license_list):
            if orig != new:
                logger.info(f"许可证转换: '{orig}' -> '{new}'")

    return license_list, license_file_list


def generate_readme_opensource(
    output_dir: str,
    converter: Optional["SPDXLicenseConverter"] = None,
    interactive: bool = True
) -> None:
    """
    Generate README.OpenSource file with support for multiple components.

    Args:
        output_dir: Output directory path.
        converter: Optional SPDX license converter for standardization.
        interactive: Whether to use interactive mode (vs batch mode).
    """
    components = []

    print("请输入开源组件的信息（输入完成后，可选择继续添加另一个组件）：")
    while True:
        component = {}

        # Get basic component information
        component["Name"] = ask_question("Name: ")
        component["Version Number"] = ask_question("Version Number: ")
        component["Owner"] = ask_question("Owner: ")
        component["Upstream URL"] = ask_question("Upstream URL: ")
        component["Description"] = ask_question("Description: ")

        # Get license information with SPDX conversion
        license_list, license_file_list = process_license_info(converter)
        component["License"] = "; ".join(license_list)
        component["License File"] = "; ".join(license_file_list)

        # Get dependencies (optional)
        dependencies = ask_for_list("请输入该软件的依赖项（如果有多个，请用逗号分隔）")
        if dependencies:
            component["Dependencies"] = dependencies

        components.append(component)

        # Ask if user wants to add another component
        if interactive:
            add_more = ask_question("是否添加另一个组件？(y/n): ").lower()
            if add_more != "y":
                break
        else:
            break

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Write README.OpenSource file
    readme_path = os.path.join(output_dir, "README.OpenSource")
    with open(readme_path, "w", encoding="utf-8") as f:
        json.dump(components, f, indent=2, ensure_ascii=False)

    logger.info(f"已生成 {readme_path}")

    # Validate SPDX licenses if converter is available
    if converter and SPDX_AVAILABLE:
        validate_spdx_licenses(components)


def validate_spdx_licenses(components: List[Dict]) -> None:
    """Validate all license identifiers in components."""
    from spdx_converter import SPDXLicenseConverter
    converter = SPDXLicenseConverter()

    all_valid = True
    for component in components:
        license_str = component.get("License", "")
        licenses = [lic.strip() for lic in license_str.split(";")]

        for lic in licenses:
            if not converter.validate_spdx_id(lic):
                logger.warning(
                    f"组件 '{component.get('Name')}' 的许可证可能不是有效的 SPDX 标识符: {lic}"
                )
                all_valid = False

    if all_valid:
        logger.info("所有许可证标识符均符合 SPDX 标准")


def main():
    """Main entry point with command-line argument support."""
    parser = argparse.ArgumentParser(
        description="生成 README.OpenSource 开源部件配置信息文件"
    )
    parser.add_argument(
        "-o", "--output",
        default=".",
        help="输出目录路径（默认：当前目录）"
    )
    parser.add_argument(
        "--no-spdx",
        action="store_true",
        help="禁用 SPDX 许可证标准化"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="启用详细日志"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Initialize SPDX converter if enabled
    converter = None
    if not args.no_spdx and SPDX_AVAILABLE:
        converter = SPDXLicenseConverter()
        logger.info("SPDX 许可证标准化已启用")

    generate_readme_opensource(args.output, converter)


if __name__ == "__main__":
    main()
