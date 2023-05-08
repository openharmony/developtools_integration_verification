# 系统参数白名单规则说明

## 1. 规则解释
  1. **[白名单](whitelist.json)** 约束系统参数配置文件(\*.para", \*.para.dac)中的名称。
  2. **[白名单](whitelist.json)** 约束系统参数命名合法性。系统参数命名由：字母、数字、下划线、'.'、 '-'、 '@'、 ':' 、 '_'。 例外：不允许出现".."
  3. 系统参数名未添加在 **[白名单](whitelist.json)**。

编译时会提示如下类型的告警：

  ```
  [NOT ALLOWED]: Invalid param: distributedsched.continuationmanager..
  [NOT ALLOWED]: persist.resourceschedule.memmgr.eswap.swapOutKBFromBirth is not found in the whitelist
  ```

## 2. 违规场景及处理方案建议

  1. 检查白名单和系统参数命名， 根据 **[规则解释](README.md#2-规则解释)** 排查修改
