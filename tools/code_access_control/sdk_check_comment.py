#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
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
#

import os
import sys
import subprocess
import re
from typing import List, Tuple, Dict, Set
import argparse
from pathlib import Path
import tempfile
import shutil

class GitDiffAnalyzer:
    """Git diff analyzer to check if modifications are comments only"""
    def __init__(self, repo_path: str = None, commit_ref: str = "HEAD"):
        """
        Initialize the analyzer
        
        Args:
            repo_path: Git repository path, None means current directory
            commit_ref: Commit reference to check, defaults to HEAD
        """
        self.repo_path = repo_path or os.getcwd()
        self.commit_ref = commit_ref
        self.diff_content = ""
        self.modified_files: List[str] = []
        self.comment_patterns = {
            'c': [r'^\s*//', r'^\s*/\*', r'\*/', r'^\s*///', r'^\s*//!'],
            'cpp': [r'^\s*//', r'^\s*/\*', r'\*/', r'^\s*///', r'^\s*//!'],
            'h': [r'^\s*//', r'^\s*/\*', r'\*/', r'^\s*///', r'^\s*//!'],
            'hpp': [r'^\s*//', r'^\s*/\*', r'\*/', r'^\s*///', r'^\s*//!'],
            'java': [r'^\s*//', r'^\s*/\*', r'\*/', r'^\s*/\*\*', r'\*/'],
            'js': [r'^\s*//', r'^\s*/\*', r'\*/', r'^\s*///', r'^\s*//!'],
            'ts': [r'^\s*//', r'^\s*/\*', r'\*/', r'^\s*///', r'^\s*//!'],
            'go': [r'^\s*//', r'^\s*/\*', r'\*/'],
            'rs': [r'^\s*//', r'^\s*/\*', r'\*/', r'^\s*///', r'^\s*//!'],
            'swift': [r'^\s*//', r'^\s*/\*', r'\*/'],
            'cs': [r'^\s*//', r'^\s*/\*', r'\*/', r'^\s*///', r'^\s*//!'],
            'py': [r'^\s*#', r'^\s*"""', r'^\s*\'\'\''],
            'sh': [r'^\s*#'],
            'bash': [r'^\s*#'],
            'zsh': [r'^\s*#'],
            'html': [r'^\s*<!--', r'-->'],
            'htm': [r'^\s*<!--', r'-->'],
            'xml': [r'^\s*<!--', r'-->'],
            'vue': [r'^\s*<!--', r'-->', r'^\s*//', r'^\s*/\*'],
            'css': [r'^\s*/\*', r'\*/'],
            'scss': [r'^\s*//', r'^\s*/\*', r'\*/'],
            'less': [r'^\s*//', r'^\s*/\*', r'\*/'],
            'rb': [r'^\s*#', r'^\s*=begin', r'^\s*=end'],           
            'php': [r'^\s*//', r'^\s*#', r'^\s*/\*', r'\*/'],
            'sql': [r'^\s*--', r'^\s*/\*', r'\*/'],
            'md': [r'^\s*<!--', r'-->'],
            'yaml': [r'^\s*#'],
            'yml': [r'^\s*#'],
            'json': [],
            'ini': [r'^\s*;', r'^\s*#'],
            'toml': [r'^\s*#'],
            'cfg': [r'^\s*#'],
            'conf': [r'^\s*#'],
            'mk': [r'^\s*#'],
            'makefile': [r'^\s*#'],
            'dockerfile': [r'^\s*#'],
            'txt': [],
        }        
        self.extension_map = {}
        for ext, patterns in self.comment_patterns.items():
            self.extension_map[ext] = patterns
    
    def run_git_command(self, cmd: List[str]) -> Tuple[bool, str]:
        """
        Execute Git command
        
        Args:
            cmd: Git command list
            
        Returns:
            (success flag, output content)
        """
        try:
            result = subprocess.run(
                ['git'] + cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            return False, f"Git error: {e.stderr}"
        except FileNotFoundError:
            return False, "Git not install"
    
    def generate_diff_file(self, output_path: str = None) -> Tuple[bool, str]:
        """
        Generate diff file
        
        Args:
            output_path: Diff file output path, None means use temporary file
            
        Returns:
            (success flag, diff file path or error message)
        """
        success, output = self.run_git_command(["log", "--oneline", "-2", "--format=%H"])
        if not success:
            return False, output
        
        commits = output.strip().split('\n')
        if len(commits) < 2:
            return False, "need two pf"       
        current_commit = commits[0].strip()
        prev_commit = commits[1].strip()
        success, diff_output = self.run_git_command([
            "diff", 
            f"{prev_commit}..{current_commit}",
            "--no-ext-diff"
        ])       
        if not success:
            return False, diff_output
        
        self.diff_content = diff_output
        if output_path:
            diff_path = output_path
            try:
                with open(diff_path, 'w', encoding='utf-8') as f:
                    f.write(diff_output)
            except IOError as e:
                return False, f"write: {e}"
        else:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.diff', delete=False, encoding='utf-8') as f:
                f.write(diff_output)
                diff_path = f.name
        self._extract_modified_files(diff_output)       
        return True, diff_path
    
    def _extract_modified_files(self, diff_content: str):
        """Extract modified files from diff content"""
        files = []
        lines = diff_content.split('\n')
        
        for line in lines:
            if line.startswith('diff --git'):
                parts = line.split()
                if len(parts) >= 3:
                    file_path = parts[2][2:]
                    files.append(file_path)       
        self.modified_files = files
    
    def parse_diff_content(self, diff_content: str = None) -> List[Dict]:
        """
        Parse diff content
        
        Args:
            diff_content: Diff content, None means use self.diff_content
            
        Returns:
            List of parsed diff hunks
        """
        if diff_content is None:
            diff_content = self.diff_content        
        if not diff_content:
            return []       
        lines = diff_content.split('\n')
        hunks = []
        current_hunk = None
        current_file = None       
        i = 0
        while i < len(lines):
            line = lines[i]
            if line.startswith('diff --git'):
                if current_hunk and current_file:
                    hunks.append(current_hunk)               
                parts = line.split()
                file_path = parts[2][2:] 
                current_file = file_path               
                current_hunk = {
                    'file': file_path,
                    'old_start': 0,
                    'old_lines': 0,
                    'new_start': 0,
                    'new_lines': 0,
                    'changes': []
                }
                i += 1
                while i < len(lines) and not lines[i].startswith('@@'):
                    i += 1
            elif line.startswith('@@'):
                if current_hunk:
                    match = re.match(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@', line)
                    if match:
                        current_hunk['old_start'] = int(match.group(1))
                        current_hunk['old_lines'] = int(match.group(2) or 1)
                        current_hunk['new_start'] = int(match.group(3))
                        current_hunk['new_lines'] = int(match.group(4) or 1)               
                i += 1
            elif current_hunk and (line.startswith('+') or line.startswith('-') or line.startswith(' ')):
                change_type = line[0]
                content = line[1:] if line else ''
                
                current_hunk['changes'].append((change_type, content))
                i += 1           
            else:
                i += 1
        if current_hunk and current_file:
            hunks.append(current_hunk)
        
        return hunks
    
    def get_file_extension(self, file_path: str) -> str:
        """
        Get file extension (without dot)
        
        Args:
            file_path: File path
            
        Returns:
            Extension (lowercase)
        """
        filename = os.path.basename(file_path).lower()
        if filename == 'dockerfile':
            return 'dockerfile'
        elif filename == 'makefile':
            return 'makefile'
        ext = os.path.splitext(file_path)[1]
        if ext:
            return ext[1:].lower()
        return ''
    
    def is_comment_line(self, line: str, file_extension: str) -> bool:
        """
        Determine if a line is a comment
        
        Args:
            line: Code line
            file_extension: File extension
            
        Returns:
            Whether it's a comment
        """
        stripped_line = line.strip()
        if not stripped_line:
            return True
        patterns = self.comment_patterns.get(file_extension, [])
        for pattern in patterns:
            if re.search(pattern, line):
                return True
        if file_extension in ['c', 'cpp', 'java', 'js', 'ts', 'go', 'rs', 'cs']:
            if '/*' in line and '*/' in line:
                comment_start = line.find('/*')
                comment_end = line.find('*/') + 2
                code_before = line[:comment_start].strip()
                code_after = line[comment_end:].strip()
                if not code_before and not code_after:
                    return True
            if stripped_line.startswith('*/'):
                return True
        if file_extension == 'py':
            if stripped_line.startswith('"""') or stripped_line.startswith("'''"):
                return True
        if file_extension in ['html', 'htm', 'xml', 'vue']:
            if '<!--' in line and '-->' in line:
                return True       
        return False
    
    def analyze_hunk(self, hunk: Dict) -> Tuple[bool, List[str]]:
        """
        Analyze whether a diff hunk only contains comment modifications
        
        Args:
            hunk: Diff hunk dictionary
            
        Returns:
            (whether only comments modified, non-comment change list)
        """
        file_path = hunk['file']
        file_ext = self.get_file_extension(file_path)       
        non_comment_changes = []       
        for change_type, content in hunk['changes']:
            if change_type in ('+', '-'):
                if not self.is_comment_line(content, file_ext):
                    non_comment_changes.append(content)       
        return len(non_comment_changes) == 0, non_comment_changes
    
    def check_commit_is_comment_only(self, diff_path: str = None) -> Tuple[bool, Dict]:
        """
        Check if commit only modifies comments
        
        Args:
            diff_path: Diff file path, None means generate automatically
            
        Returns:
            (whether only comments modified, detailed analysis result)
        """
        if diff_path:
            try:
                with open(diff_path, 'r', encoding='utf-8') as f:
                    diff_content = f.read()
                self.diff_content = diff_content
                self._extract_modified_files(diff_content)
            except IOError as e:
                return False, {'error': f'no read diff file: {e}'}
        else:
            success, result = self.generate_diff_file()
            if not success:
                return False, {'error': result}
            diff_path = result
        hunks = self.parse_diff_content()       
        if not hunks:
            return True, {
                'message': 'not change',
                'modified_files': self.modified_files,
                'hunks': []
            }
        all_comment_only = True
        analysis_results = []
        all_non_comment_changes = []       
        for hunk in hunks:
            is_comment_only, non_comment_changes = self.analyze_hunk(hunk)
            
            analysis_results.append({
                'file': hunk['file'],
                'is_comment_only': is_comment_only,
                'non_comment_changes': non_comment_changes,
                'hunk_info': {
                    'old_start': hunk['old_start'],
                    'new_start': hunk['new_start']
                }
            })           
            if not is_comment_only:
                all_comment_only = False
                all_non_comment_changes.extend(non_comment_changes)       
        result = {
            'is_comment_only': all_comment_only,
            'modified_files': self.modified_files,
            'analysis_results': analysis_results,
            'non_comment_changes': all_non_comment_changes,
            'diff_file': diff_path
        }       
        return all_comment_only, result


def print_analysis_report(result: Dict, verbose: bool = False):
    print("\n" + "="*60)
    print("Git")
    print("="*60)   
    if 'error' in result:
        print(f"error: {result['error']}")
        return    
    if result['modified_files']:
        for file in result['modified_files']:
            print(f"  - {file}")   
    if verbose and result['analysis_results']:
        for analysis in result['analysis_results']:
            status = "true" if analysis['is_comment_only'] else "false"
            print(f"\n: {analysis['file']} ({status})")         
            if not analysis['is_comment_only'] and analysis['non_comment_changes']:
                for change in analysis['non_comment_changes'][:5]:
                    print(f"  - {change[:80]}{'...' if len(change) > 80 else ''}")   
    if not result['is_comment_only'] and result['non_comment_changes']:
        print(f"\n {len(result['non_comment_changes'])} ")   
    if 'diff_file' in result and os.path.exists(result['diff_file']):
        print(f"\nDiff: {result['diff_file']}")   
    print("\n" + "="*60)


@dataclass
class DiffChange:
    file_path: str  
    start_line_old: int
    lines_old: int   
    start_line_new: int
    lines_new: int   
    deleted_lines: List[str]
    added_lines: List[str]
    context_lines: List[str]


class DiffParser:
    def __init__(self, diff_file_path: str):
        self.diff_file_path = diff_file_path
        self.diff_git_pattern = re.compile(r'diff --git a/(.*) b/(.*)')
        self.hunk_header_pattern = re.compile(r'@@ -(\d+)(,(\d+))? \+(\d+)(,(\d+))? @@')


    def parse(self) -> List[DiffChange]:
        changes = []
        current_change: Optional[DiffChange] = None       
        with open(self.diff_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip('\n') 
                diff_git_match = self.diff_git_pattern.match(line)
                if diff_git_match:
                    file_path = diff_git_match.group(1) 
                    current_change = None 
                    continue
                hunk_match = self.hunk_header_pattern.match(line)
                if hunk_match and file_path:
                    start_old = int(hunk_match.group(1))
                    lines_old = int(hunk_match.group(3)) if hunk_match.group(3) else 1
                    start_new = int(hunk_match.group(4))
                    lines_new = int(hunk_match.group(6)) if hunk_match.group(6) else 1
                    current_change = DiffChange(
                        file_path=file_path,
                        start_line_old=start_old,
                        lines_old=lines_old,
                        start_line_new=start_new,
                        lines_new=lines_new,
                        deleted_lines=[],
                        added_lines=[],
                        context_lines=[]
                    )
                    changes.append(current_change)
                    continue
                if current_change:
                    if line.startswith('-'):
                        current_change.deleted_lines.append(line[1:].lstrip())
                    elif line.startswith('+'):
                        current_change.added_lines.append(line[1:].lstrip())
                    elif line.startswith('\\'):  
                        continue
                    else:
                        current_change.context_lines.append(line.lstrip())        
        return changes


    def print_changes(self, changes: List[DiffChange]):
        if not changes:
            return       
        for idx, change in enumerate(changes, 1):
            print(f"\n===  {idx}  ===")
            print(f"{change.file_path}")
            print(f"{change.start_line_old} , {change.lines_old} ")
            print(f" {change.start_new} , {change.lines_new} ")           
            if change.deleted_lines:
                print("\n del:")
                for line in change.deleted_lines:
                    print(f"  - {line}")           
            if change.added_lines:
                print("\n add:")
                for line in change.added_lines:
                    print(f"  + {line}")           
            if change.context_lines:
                print("\n change:")
                for line in change.context_lines:
                    print(f"    {line}")


def main():
    parser = argparse.ArgumentParser(
        description='comment',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
  %(prog)s                         
  %(prog)s --diff my.diff          
  %(prog)s --repo /path/to/repo    
  %(prog)s --commit HEAD~2         
  %(prog)s --verbose               
  %(prog)s --output result.json    
        """
    ) 
    parser.add_argument('--repo', '-r')
    parser.add_argument('--commit', '-c', default='HEAD')
    parser.add_argument('--diff', '-d')
    parser.add_argument('--verbose', '-v', action='store_true')
    parser.add_argument('--output', '-o')
    parser.add_argument('--keep-diff', action='store_true')
    parser.add_argument('--no-color', action='store_true')   
    args = parser.parse_args()
    analyzer = GitDiffAnalyzer(args.repo, args.commit)
    if not args.diff:
        success, _ = analyzer.run_git_command(["rev-parse", "--git-dir"])
        if not success:
            sys.exit(1)
    is_comment_only, result = analyzer.check_commit_is_comment_only(args.diff)
    print_analysis_report(result, args.verbose)
    if args.output:
        import json
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"\n: {args.output}")
        except IOError as e:
            print(f"\nerror: {e}")
    if not args.keep_diff and 'diff_file' in result:
        diff_path = result['diff_file']
        if os.path.exists(diff_path) and not args.diff:
            try:
                os.unlink(diff_path)
            except:
                pass
    sys.exit(0 if is_comment_only else 1)


if __name__ == "__main__":
    main()