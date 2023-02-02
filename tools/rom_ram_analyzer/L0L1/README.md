# rom_ram_analyzer

## 目的

分析各部件的rom占用,结果以xls和json格式进行保存

## 支持产品

目标是支持所有的产品,但是目前由于配置文件没设计好,只支持:ipcamera_hispark_taurus ipcamera_hispark_taurus_linux wifiiot_hispark_pegasus

## 代码思路

1. 扫描BUILD.gn文件,收集各个target的编译产物及其对应的component_name, subsystem_name信息,并存储到config.yaml中的gn_info_file字段指定的json文件中
2. 根据配置文件config.yaml扫描产品的编译产物目录,得到真实的编译产物信息(主要是大小)
3. 用真实的编译产物与从BUILD.gn中收集的信息进行匹配,从而得到编译产物-大小-所属部件的对应信息
4. 如果匹配失败,会直接利用grep到项目路径下进行搜索
5. 如果还搜索失败,则将其归属到others


## 使用

前置条件：

1. 获取整个L0L1目录
1. 对系统进行编译
1. linux平台
1. python3.8及以后
1. 安装requirements
    ```txt
    xlwt==1.3.0
    ```

1. `python3 rom_analysis.py --product_name {your_product_name} --oh_path {root_path_of_oh} [--recollect_gn bool]`运行代码,其中recollect_gn表示是需要重新扫描BUILD.gn还是直接使用已有结果.eg: `python3 rom_analysis.py --product_name ipcamera_hispark_taurus`
3. 运行完毕会产生4个json文件及一个xls文件,如果是默认配置,各文件描述如下:
   - gn_info.json:BUILD.gn的分析结果
   - sub_com_info.json:从bundle.json中进行分析获得的各部件及其对应根目录的信息
   - {product_name}_product.json:该产品实际的编译产物信息,根据config.yaml进行收集
   - {product_name}_result.json:各部件的rom大小分析结果
   - {product_name}_result.xls:各部件的rom大小分析结果

## 新增template

主要是在config.py中配置Processor,并在config.yaml中添加相应内容

## 后续工作

1. 部分log的输出有待优化
1. hap_pack需要对hap_name进行处理