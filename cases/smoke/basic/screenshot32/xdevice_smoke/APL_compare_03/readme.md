## 版本
python版本：3.8.10
pip版本:22.1.2
python依赖：

```
pip install pandas
pip install openpyxl
pip install subprocess
```
## 使用
`python compare.py`

## 目录
```
APL_compare
├── apl_config.py                  # 整个目录中的常量定义
├── read_device.py             # 从设备中下载db并解析表和字段的函数   
├── read_excel.py              # 从excel中解析表和字段的函数            
├── compare.py                 # 脚本运行入口
└── common.py                  # 公共需要用到的函数       
```
## apl_config.py
常量定义
`PATH`：当前目录的地址
### read_excel.py
`SHEET_NAME`：excel中的表名
`COLS`：excel中的列名，下标从0开始
`SVN`：SVN的安装目录下的bin目录
`SVN_URL`：excel文件在SVN上对应的url
`USER`：svn的用户名
`PWD`：svn的密码
`FILE_PATH`：本地下载文件的路径
`SQL_SRC`：设备上的数据库路径
`SQL_DES`：本地下载文件路径
`DOWNLOAD_DB`：从设备下载的hdc命令
`QUERY_HAP_APL`：查询HAP APL的sql语句（查询多列可以依次添加字段，添加字段的顺序为比较时的字段优先级）
`QUERY_NATIVE_APL`：查Native APL的sql语句
`APL_LOG_FILE`：执行脚本的日志路径
`APL_RECORD_PATH`：APL对比记录的日志路径
`IS_OVERWRITE`：是否覆盖之前的APL日志，w表示覆盖，a表示追加

## read_device.py
用于从设备上导出数据库，并解析表和字段
### 数据库导出
函数：`download_from_device(cmd,sql_src,sql_des)`
hdc命令：`cmd`
设备中数据库路径：`sql_src`
本地数据库路径：`sql_des`
执行命令：`hdc file recv sql_src sql_des`
### 连接数据库
相关函数：`sql_connect(db)`
传入参数：`db`--db文件存放路径
返回结果：`conn`--数据库的连接
### sql语句查询
相关函数：`query_records(db,sql)`
传入参数：`db`--需要连接的数据库；`sql`：sql查询语句
返回结果：`results`--查询结果
### 查hap_token_info_table中的bundle_name和apl 
sql语句：`QUERY_HAP_APL="select bundle_name,apl from hap_token_info_table"`
相关函数：`query_hap_apl(db,sql)`
传入参数：`db`--需要连接的数据库；`sql`：sql查询语句
返回结果：`res_map`--查询结果转化为的字典（map，key是bundle_name，value是apl）
### 查询native_token_info_table中的process_name和apl
sql语句：`QUERY_NATIVE_APL="select process_name,apl from native_token_info_table"`
相关函数：`query_native_apl(db,sql)`
传入参数：`db`--需要连接的数据库；`sql`--sql查询语句
返回结果：`res_map`--查询结果转化为的字典（map，key是process_name，value是apl）

## read_excel.py
### 从svn上下载excel
相关函数：`syn_checkout(settings)`
传入参数：`settings`--包含svn上文件路径，本地路径，用户名，密码
返回结果：`settings['dir']`--本地下载路径
### url编码
相关函数：`url_encode(url)`
传入参数：`url`
返回结果：`encode_url`

### 解析excel
相关函数：`read_excel(file,sheet,cols)`
传入参数：`file`--excel文件，`sheet`--表名，`cols`--列名
返回结果：`apl_map`----查询结果转化为的字典（map，key是bundle/process_name，value是apl）

## common.py
### 脚本执行过程中的错误日志
相关函数：`log(msg)`
相关参数：`msg`--错误信息
### 设置脚本执行过程中的日志信息
相关函数：`apl_set_log_content(msg)`
相关参数：`msg`--日志信息，`is_error`--用于判断是执行失败、成功
返回结果：带时间戳的日志信息

### 设置apl记录的格式
相关函数：set_error_record(name,error)
相关参数：`name`--bundle name或者native name，`error`--错误原因
返回结果：带时间戳的记录

### 将查询结果转化成map的结构
相关函数：`set_map(results)`
传入参数：`results`--查询结果的列表
返回结果：`res_map`
### 转换查询结果map的value格式
相关函数：`set_value(result)`
传入参数：`result`--查询到的每一行结果
返回结果：`value`--包含查询到的字段的列表
### 时间戳
相关函数：`timestamp()`
返回结果：时间戳

### 错误类型
`ErrorType`：枚举类

### 自定义异常
`AplCompareException`

### 自定义线程
`AplCompareThread`

### 日志格式设置
`logging.basicConfig`