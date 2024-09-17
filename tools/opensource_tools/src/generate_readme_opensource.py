import os
import json

def ask_question(prompt):
    return input(prompt).strip()

def generate_readme_opensource(output_dir):
    """
    生成 README.OpenSource 文件，支持多个开源组件的信息输入。
    """
    components = []
    fields = [
        "Name",
        "License",
        "License File",
        "Version Number",
        "Owner",
        "Upstream URL",
        "Description"
    ]

    print("请输入开源组件的信息（输入完成后，可选择继续添加另一个组件）：")
    while True:
        component = {}
        for field in fields:
            value = ask_question(f"{field}: ")
            component[field] = value
        components.append(component)

        add_more = ask_question("是否添加另一个组件？(y/n): ").lower()
        if add_more != 'y':
            break

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    readme_path = os.path.join(output_dir, 'README.OpenSource')
    with open(readme_path, 'w', encoding='utf-8') as f:
        json.dump(components, f, indent=2, ensure_ascii=False)
    print(f"已生成 {readme_path}")

def main():
    output_dir = ask_question("请输入输出目录（默认当前目录）：") or '.'
    generate_readme_opensource(output_dir)

if __name__ == '__main__':
    main()

