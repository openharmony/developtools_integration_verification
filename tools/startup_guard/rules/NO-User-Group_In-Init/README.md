# DAC用户群组合法性规则说明

## 规则解释

  - 规则要求
    1. 检查用户名、uid的唯一性。
    2. 检查passwd 文件中，同一用户定义的uid和所属的组是否一致。

  - 解决方法
    1. 按照uid 设置规则，重新设置用户名、uid。
    2. 同一用户的uid和gid值一致。

  - uid设置规则：
    1. uid具有唯一性，不同用户/组的 uid，gid不可以相同。
    2. 用户名/组名具有唯一性，不同用户的用户名/组名不可以相同。

编译时会提示如下类型的告警：
  ```
  [NOT ALLOWED]: repeat uid name list:  ['nwebspawn', 'nwebspawn']
  [NOT ALLOWED]: repeat uid value list:  [3081, 3081]
  [NOT ALLOWED]: xxx has different passwd and group values
```

## 违规场景及处理方案建议
  1. 根据 **[规则解释](README.md#规则解释)** 排查修改。
