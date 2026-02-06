#!/usr/bin/env python
#coding=utf-8

#
# Copyright (c) 2025 Huawei Device Co., Ltd.
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
#

import os
import shlex
from .base_rule import BaseRule


class SADirectoryRule(BaseRule):
    RULE_NAME = "NO-Illegal-SA-Directory-Creation"
    # Allowed base directories for SA directory creation
    ALLOWED_BASE_DIRECTORIES = ["/data/service", "/data/app", "/data/chipset"] # noqa: rule5.1.3.1

    def __init__(self, mgr, args):
        super().__init__(mgr, args)
        self._mkdir_cmd_whitelist = []
        self._parse_whitelist()
        self._file_id_to_name_cache = {}  # Cache to map fileId to file name for faster lookup
        self._file_id_cache_built = False  # Flag to indicate if cache is fully built

    def __check__(self):
        passed = True
        cfg_parser = self.get_mgr().get_parser_by_name('config_parser')

        if cfg_parser:
            passed = self._check_mkdir_commands(cfg_parser)

        if not passed:
            self.error("SA directory creation check failed")
            raise Exception("SA directory creation check failed")

        return passed

    def _parse_whitelist(self):
        """Parse whitelist configuration and normalize paths"""
        white_lists = self.get_white_lists()
        if white_lists:
            # Normalize all whitelist paths during initialization to avoid repeated processing
            self._mkdir_cmd_whitelist = [os.path.normpath(path) for path in white_lists]

    def _safe_get(self, obj, key, default=None):
        """Safely get attribute from object or dict without using ItemParser.get()"""
        # First check if it's a dictionary type
        if isinstance(obj, dict):
            try:
                return obj[key]
            except (KeyError, TypeError):
                return default
        # For non-dict types, try getattr
        try:
            return getattr(obj, key, default)
        except (AttributeError, TypeError):
            return default

    def _check_mkdir_commands(self, cfg_parser):
        """Check all mkdir commands according to the new flow"""
        passed = True

        # Get commands using get method to avoid KeyError
        cmds = getattr(cfg_parser, '_cmds', [])
        for cmd in cmds:
            # Use a safe method to get attributes from both dict and object-like cmd
            cmd_name = self._safe_get(cmd, 'name')
            if cmd_name != 'mkdir':
                continue

            content = self._safe_get(cmd, 'content', '')
            file_id = self._safe_get(cmd, 'fileId', '')

            # Parse mkdir command parameters
            mkdir_params = self._parse_mkdir_params(content)
            if not mkdir_params:
                self.error(f"Invalid mkdir command: {content} in file {self._get_file_name(cfg_parser, file_id)}")
                passed = False
                continue

            # Check all directory paths in the command
            dir_paths = mkdir_params.get('dir_paths', [])
            for dir_path in dir_paths:
                # Create a new params dict for each path to check
                path_params = {
                    'dir_path': dir_path,
                    'options': mkdir_params.get('options', [])
                }
                if not self._check_single_mkdir_command(path_params, content, cfg_parser, file_id):
                    passed = False

        return passed

    def _check_single_mkdir_command(self, mkdir_params, content, cfg_parser, file_id):
        """Check a single mkdir command according to the new rules"""
        # Get the directory path - caller ensures 'dir_path' is provided
        dir_path = mkdir_params.get('dir_path')
        if not dir_path:
            return True

        # Rule 1: Only check /data directory, others pass directly
        if not dir_path.startswith('/data'):
            return True

        # Special case: /data directory itself passes directly
        if dir_path == '/data' or dir_path == '/data/':
            return True

        normalized_dir_path = os.path.normpath(dir_path)

        # Rule 2: Check if directory is under allowed base directories
        in_allowed_base = False
        for base_dir in self.ALLOWED_BASE_DIRECTORIES:
            if normalized_dir_path == base_dir or normalized_dir_path.startswith(f'{base_dir}/'):
                in_allowed_base = True
                break

        # Rule 3: Check for directories with exact name '100', '101', '102', '103', '104', or '105'
        has_illegal_dir = False
        illegal_component = None
        # Only check normalized path components to avoid false positives
        path_components = normalized_dir_path.split('/')
        # Define illegal directory names
        illegal_dir_names = {'100', '101', '102', '103', '104', '105'}
        for component in path_components:
            if component in illegal_dir_names:
                has_illegal_dir = True
                illegal_component = component
                break

        # Check whitelist with different logic based on whether there are illegal directory names
        in_whitelist = False
        if has_illegal_dir:
            # If path contains 100-105 directories, check if truncated path is in whitelist
            in_whitelist = self._check_illegal_dir_whitelist(normalized_dir_path)
        else:
            # If path doesn't contain 100-105 directories, prefix matching is allowed
            for white_path in self._mkdir_cmd_whitelist:
                if normalized_dir_path == white_path or normalized_dir_path.startswith(f'{white_path}/'):
                    in_whitelist = True
                    break

        # If in whitelist, allow it
        if in_whitelist:
            return True

        # If directory is illegal (not in allowed base or has 10xx directory), report error
        if not in_allowed_base or has_illegal_dir:

            # If not in whitelist, report error
            if not in_allowed_base:
                self.error(
                    f"mkdir directory must be a subdirectory of {self.ALLOWED_BASE_DIRECTORIES} "
                    f"or be in whitelist: {content} in file {self._get_file_name(cfg_parser, file_id)}"
                )
                return False
            elif has_illegal_dir:
                self.error(
                    f"mkdir directory path contains illegal directory name '{illegal_component}': "
                    f"{content} in file {self._get_file_name(cfg_parser, file_id)}"
                )
                return False

        # All checks passed
        return True

    def _check_illegal_dir_whitelist(self, normalized_dir_path):
        """
        Check if a path containing 100-105 directories is allowed based on whitelist rules.
        If path has illegal numeric directories, the last one must be in the whitelist.

        Args:
            normalized_dir_path (str): The normalized directory path to check.

        Returns:
            bool: True if the last illegal directory path is in the whitelist, False otherwise.
        """
        # If path contains 100-105 directories:
        # 1. Find all illegal directory components
        # 2. Get the last illegal directory component
        # 3. Check if the full path up to the last illegal directory is in the whitelist
        path_components = normalized_dir_path.split('/')
        illegal_dir_names = {'100', '101', '102', '103', '104', '105'}

        # Find all indices of illegal directory components
        illegal_indices = []
        for i, component in enumerate(path_components):
            if component in illegal_dir_names:
                illegal_indices.append(i)

        # If no illegal directories found, return True (but this should have been handled earlier)
        if not illegal_indices:
            return True

        # Check only the last illegal directory path
        last_illegal_index = illegal_indices[-1]
        path_up_to_last_illegal = '/'.join(path_components[:last_illegal_index+1])
        for white_path in self._mkdir_cmd_whitelist:
            if path_up_to_last_illegal == white_path or normalized_dir_path == white_path:
                return True

        # Last illegal directory path is not in the whitelist
        return False

    def _parse_mkdir_params(self, content):
        """Parse mkdir command parameters"""
        # Parse the command content
        parts = self._safe_parse_shlex(content)
        if not parts:
            return None

        # Process optional parameters (starting with '-')
        options_with_values = ['-m', '--mode', '--context']
        processed_parts = self._split_combined_options(parts)

        # Process the processed parts
        options, paths = self._process_parts(processed_parts, options_with_values, content)

        # At least one path is required
        if not paths:
            self.error(f"mkdir command missing directory path: {content}")
            return None

        return {
            'dir_paths': paths,  # Return all identified paths
            'options': options
        }

    def _safe_parse_shlex(self, content):
        """Safely parse content using shlex.split"""
        try:
            parts = shlex.split(content)
            if not parts:
                return None
            return parts
        except ValueError:
            self.error(f"Invalid command syntax: {content}")
            return None

    def _split_combined_options(self, parts):
        """Split combined options like '-m755' into separate parts"""
        processed_parts = []

        for part in parts:
            # Check if it's a combined option (starts with '-' and has no '=' but contains non-hyphen characters)
            if part.startswith('-') and len(part) > 1 and '=' not in part:
                # Check if it's a short option with value (e.g., '-m755')
                split_parts = self._split_single_option(part)
                processed_parts.extend(split_parts)
            else:
                # Regular part, add to processed parts
                processed_parts.append(part)

        return processed_parts

    def _split_single_option(self, part):
        """Split a single combined option like '-m755' into separate parts"""
        for i in range(1, len(part)):
            if not part[i].isalpha() and part[i] != '-':
                # Found the split point
                option_name = part[:i]
                option_value = part[i:]
                return [option_name, option_value]

        # No split point found, it's a regular option (e.g., '-p')
        return [part]

    def _process_parts(self, processed_parts, options_with_values, content):
        """Process the parts to extract options and paths"""
        options = []
        paths = []
        i = 0
        found_first_path = False

        while i < len(processed_parts):
            part = processed_parts[i]

            # Process non-option part
            if not part.startswith('-'):
                if not found_first_path or part.startswith('/'):
                    paths.append(part)
                    found_first_path = True
                i += 1
                continue

            # Process option
            options.append(part)

            # Handle option with attached value
            if '=' in part:
                i += 1
                continue

            # Handle option that requires separate value
            option_name = part
            if option_name in options_with_values:
                if not self._process_option_with_value(option_name, processed_parts, i, options, content):
                    return [], []
                i += 2
            else:
                i += 1

        return options, paths

    def _process_option_with_value(self, option_name, processed_parts, index, options, content):
        """Process an option that requires a separate value"""
        # Check if next part exists
        if index + 1 >= len(processed_parts):
            self.error(f"Option {option_name} in mkdir command requires a value: {content}")
            return False

        # Check if next part is also an option
        next_part = processed_parts[index + 1]
        if next_part.startswith('-'):
            self.error(f"Option {option_name} in mkdir command requires a value: {content}")
            return False

        # Option has a separate value, add it
        options.append(next_part)
        return True

    def _get_file_name(self, cfg_parser, file_id):
        """Get file name based on file_id"""
        # Check if file_id is already in cache
        if file_id in self._file_id_to_name_cache:
            return self._file_id_to_name_cache[file_id]

        # Get files using getattr to avoid accessing protected member directly
        files_dict = getattr(cfg_parser, '_files', {})

        # Build cache if not fully built yet
        if not self._file_id_cache_built:
            for file_name, file_info in files_dict.items():
                current_file_id = self._safe_get(file_info, 'fileId')
                self._file_id_to_name_cache[current_file_id] = file_name
            self._file_id_cache_built = True

        # Return from cache or 'unknown_file'
        return self._file_id_to_name_cache.get(file_id, 'unknown_file')
