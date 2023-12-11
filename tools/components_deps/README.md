# components_deps_analyzer.py

## 功能介绍

基于config.json、编译产物out/{product_name}/build_configs/parts_info/parts_deps.json，分析各必选部件和可选部件间的依赖关系。

结果以json格式进行存储。

## 支持产品

主要是rk3568系列,已测试产品包括rk3568、rk3568_mini_system、pc_mini_system、tablet_mini_system、phone_mini_system

## 实现思路

利用产品部件定义文件config.json和编译构建自动生成的out/{product_name}/build_configs/parts_info/parts_deps.json中已有的信息重新组织，查找相关BUILD.gn文件路径。

## 使用说明

前置条件：

1. 获取整个components_deps目录
1. 对系统进行编译
1. python3及以后

命令介绍：

1. `-h`或`--help`命令查看帮助
   ```shell
   > python3 components_deps_analyzer.py -h
   usage: components_deps_analyzer.py [-h] -c CONFIG_JSON -d PARTS_DEPS_JSON [-s SINGLE_COMPONENT_NAME] [-o OUTPUT_FILE]
   
     -s SINGLE_COMPONENT_NAME, --single_component_name SINGLE_COMPONENT_NAME
                           single component name
     -o OUTPUT_FILE, --output_file OUTPUT_FILE
                           eg: demo/components_deps

   ```
1. 使用示例
   ```shell
   python components_deps_analyzer.py -c vendor/hihope/rk3568/config.json -d out/rk3568/build_configs/parts_info/parts_deps.json -o components_dep -s ability_runtime
   ```

## 输出格式介绍(components_dep.json)

```
{
   必选部件名: {
       无条件依赖的可选部件名1: 
       [BUILD.gn文件路径1，
       BUILD.gn文件路径2，
       ...],
       无条件依赖的可选部件名2: 
       [BUILD.gn文件路径1，
       BUILD.gn文件路径2，
       ...],
       ...
       }
}
```

## 单部件输出格式介绍(ability_runtime.json)

```
{
    无条件依赖的可选部件名1: 
    [BUILD.gn文件路径1，
    BUILD.gn文件路径2，
    ...],
    无条件依赖的可选部件名2: 
    [BUILD.gn文件路径1，
    BUILD.gn文件路径2，
    ...],
    ...
}
```
