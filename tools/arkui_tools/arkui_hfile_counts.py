#!/usr/bin/env python3
import subprocess
import re
from collections import defaultdict

def run_ninja_command():
    try:
        # Execute the ninja command
        cmd = '../../prebuilts/build-tools/linux-x86/bin/ninja -w dupbuild=warn -t deps > ninja_deps.txt'
        subprocess.run(cmd, shell=True, check=True)
        print("Successfully generated ninja_deps.txt")
    except subprocess.CalledProcessError as e:
        print(f"Error running ninja command: {e}")
        exit(1)

def analyze_deps_file():
    pattern = re.compile(r'.*\.h$')  # Match .h files
    keywords = ['arkui/ace_engine', 'arkui/framework/core']
    count_dict = defaultdict(int)

    try:
        with open('ninja_deps.txt', 'r') as f:
            for line in f:
                line = line.strip()
                if pattern.search(line):
                    if any(keyword in line for keyword in keywords):
                        count_dict[line] += 1
    except FileNotFoundError:
        print("Error: ninja_deps.txt not found")
        exit(1)

    return count_dict

def write_results(count_dict, output_file='arkui_hfile_counts.txt'):
    with open(output_file, 'w') as f:
        for filename, count in sorted(count_dict.items(), key=lambda x: x[1], reverse=True):
            f.write(f"{filename}: {count}\n")
    print(f"Results written to {output_file}")

def main():
    # Step 1: Run the ninja command
    run_ninja_command()
    
    # Step 2: Analyze the generated file
    counts = analyze_deps_file()
    
    # Step 3: Write results to output file
    write_results(counts)
    
    # Print summary
    print(f"Found {len(counts)} matching .h files")

if __name__ == "__main__":
    main()