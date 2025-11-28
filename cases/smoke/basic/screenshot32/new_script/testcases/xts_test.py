import os

def run_xts(target_folder):
    target_folder_path = os.path.join(target_folder, "reports")
    os.system("rmdir /s /q" + target_folder_path)
    oos.chdir(target_folder)
    os.system("python -m xdevice run acts")
    if not os.path.exists(target_folder_path):
        print(f"未生成reports报告")
        return "fail"
    found_files = []
    target_file = "failures_report.html"
    for dirpath, _, filenames in os.walk(target_folder_path):
        if target_file in filenames:
            file_path = os.path.join(dirpath, target_file)
            found_files.append(file_path)
    
    if not found_files:
        return "pass"
    else:
        return "fail"

if __name__ == "__main__":
    target_folder = ""
    run_xts(target_folder)