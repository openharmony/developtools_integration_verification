# cfg文件白名单规则说明

## 规则解释
  白名单严格遵循JSON格式。

  ### **耗时命令约束**
  **[白名单](whitelist.json)** 约束*.cfg文件中的耗时命令。

  - 耗时命令

    命令执行超过200ms的命令行。

  - 规则要求

    1. 命令行执行时间超过200ms。
    2. 耗时命令在白名单中配置。
    3. 耗时命令文件路径在白名单中配置。

  - 白名单信息解释
    ```
    {
        "cmd":"init_global_key",
            "location":[
                "/system/etc/init.cfg",
                ...
            ]
    }
    ```
    1. cmd: 命令行
    2. location:  耗时命令文件路径

  - 解决方法
    1. 检查违规项是否是耗时命令。
    2. 检查该命令是否包含白名单中。
    3. 检查该命令存在的文件路径是否包含在白名单中。
    3. 根据评审结果添加命令到白名单。

### **condition服务约束**
   **[白名单](whitelist.json)** 约束*.cfg文件中的service的启动方式：condition。

   - condition

      condition 条件启动，对服务的启动方式配置condition，通过start命令拉起服务。

   - 规则要求
      1. 服务不是按需启动，即"ondemand" : false。
      2. 服务是条件启动， 即"start-mode" : "condition"， 并且通过start命令拉起服务。
      3. 服务在白名单中。

   - 白名单信息解释
        ```
        {
            "start-modes": [
                {
                "start-mode":"condition",
                "service": [
                        "hilogd",
                        ...
                    ]
                }
            ]
        }
        ```
        1. start-mode:"condition", 服务启动方式。
        2. service：通过"start-mode" : "condition" 启动的服务。

  - 解决方法
    1. 检查服务否是按需启动。
    2. 检查服务是否配置条件启动， 且通过start命令拉起服务。
    3. 检查服务是否在白名单中。
    4. 根据评审结果添加服务到白名单。

### **boot服务约束**
   **[白名单](whitelist.json)** 约束*.cfg文件中的service的启动方式：boot。

   - boot

      在init job阶段启动，其服务的启动方式配置 boot。

  - 规则要求
      1. 服务是boot启动， 即"start-mode" : "boot"的服务。
      2. 服务在白名单中。

   - 白名单信息解释
        ```
        {
            "start-modes": [
                {
                "start-mode":"boot",
                "service": [
                        "hiview",
                        ...
                    ]
                }
            ]
        }
        ```
        1. start-mode:"boot",服务启动方式。
        2. service：通过"start-mode" : "boot" 启动的服务。

  - 解决方法
    1. 检查服务是否是boot启动。
    2. 检查服务是否在白名单中。
    3. 根据评审结果添加服务到白名单。

### **start命令约束**
   **[白名单](whitelist.json)** 约束*.cfg文件中的通过start执行的命令。

   - start

      通过start拉起的服务。

   - 规则要求
      1. 通过start命令执行的命令行。
      2. 命令行在白名单中。

   - 白名单信息解释
        ```
        {
            "start-cmd": [
                "ueventd",
                ...
            ]
        }
        ```
        start-cmd: 执行start命令行。

  - 解决方法
    1. 检查命令是否是start命令。
    2. 检查命令行是否在白名单中。
    3. 根据评审结果添加命令到白名单。

  ### **selinux约束**
  - secon

    服务的selinux标签

  - 规则要求
    1. 服务配置没有配置"secon"。
    2. 配置配置的"secon"为空。

  - 解决方法
    1. 检查服务是否配置"secon"， 且"secon"的配置不为空。
    2. 根据要求修改服务"secon"配置

编译时会提示如下类型的告警：
  ```
  [NOT ALLOWED]: 'init_global_key' is timeout command, in /system/etc/init.cfg
  [NOT ALLOWED]: xxx 'secon' is empty
  [WARNING]: 'storage_daemon' cannot be started in boot mode
  [WARNING]: 'hilogd' cannot be started in conditional mode
  [WARNING]: selinux status is xxx
  [WARNING]: multimodalinput is not in start cmd list.  path:/system/etc/init/multimodalinput.cfg
```

## 违规场景及处理方案建议
  1. 服务默认按照并行启动配置，如果需要添加白名单，需要评审。
  2. 根据 **[规则解释](README.md#规则解释)** 排查修改。
