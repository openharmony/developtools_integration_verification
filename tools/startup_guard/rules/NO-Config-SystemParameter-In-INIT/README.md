# 系统参数白名单规则说明

  ## **系统参数命名约束**
  - 规则要求
    1. 约束\*.para", \*.para.dac 配置文件中的系统参数。
    2. 系统参数命名由：字母、数字、下划线、'.'、 '-'、 '@'、 ':' 、 '_'。
    3. 不允许出现".."。

  - 解决方法
    1. 根据系统参数的命名规范排查修改。

  ## dac配置内存大小约束
  - 规则要求
    1. dac配置不超过200个。

  - 解决方法
    1. 重新配置dac内存大小, 修改 "startup/init/services/param/include/param_osadp.h" 中PARAM_WORKSPACE_DAC。
    2. 修改 "startup_guard/startup_checker/system_parameter_rules.py" 中CONFIG_DAC_MAX_NUM = 200的大小。

编译时会提示如下类型的告警：

  ```
  [NOT ALLOWED]: Invalid param: distributedsched.continuationmanager..
  [NOT ALLOWED]: DAC overallocated memory

  ```

# 违规场景及处理方案建议

  1. 检查系统参数命名， 根据 **[系统参数命名约束](README.md#系统参数命名约束)** 排查修改。
  2. 排查dac配置是否超出内存申请范围， 根据 **[dac配置内存大小约束](README.md#dac配置内存大小约束)** 排查修改。
