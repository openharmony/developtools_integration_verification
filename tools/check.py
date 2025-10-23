import os
import json
import xml.etree.ElementTree as ET

pr_list = os.environ.get("PR_FILE_PATHS")
data = json.loads(pr_list)

tree = ET.parse(".repo/manifests/ohos/ohos.xml")
root = tree.getroot()

matched_paths = []

for project in root.findall("project"):
    name = project.get("name")
    path = project.get("path")
    if name in data:
        for file_path in data[name]:
            matched_path = f"{path}/{file_path}"
            matched_paths.append(matched_path)

def check_paths_in_files(file_paths):
    result = 0
    for file_path in file_paths:
        with open(file_path, 'r',encoding='utf-8',errors='ignore') as file:
            for line in file:
                if 'system/app/ArkWebCore' in line:
                    print(f"文件 {file_path} 中含有 'system/app/ArkWebCore'，该路径违规，请修改")
                    result = 1
                    break
    return result

result = check_paths_in_files(matched_paths)
print(f"检查结果: {result}")
exit(1 if result else 0)
    
