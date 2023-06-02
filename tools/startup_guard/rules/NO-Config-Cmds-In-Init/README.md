# 耗时命令白名单规则说明

## 1. 耗时命令说明
  命令执行超过200ms的命令行。

## 2. 规则解释

  1. **耗时命令约束**：**[白名单](whitelist.json)** 约束*.cfg文件中的耗时命令。
  2. **condition服务约束**：白名单中约束service启动方式是："start-mode" : "condition" 且"ondemand" : false ， 且服务通过start命令启动。
  3. **boot服务约束**：白名单约束service启动方式是："start-mode" : "boot"。
  4. **selinux约束**：selinux未打开， 或服务的"secon"没有配置。
      
编译时会提示如下类型的告警：

  ```
  [NOT ALLOWED]: 'mount_fstab' is invalid, in /system/etc/init.cfg<br>
  [NOT ALLOWED]: 'load_access_token_id' is invalid, in /system/etc/init/access_token.cfg<br>
  [NOT ALLOWED]: 'init_global_key' is invalid, in /system/etc/init.cfg<br>
  [NOT ALLOWED]: 'storage_daemon' cannot be started in boot mode<br>
  [NOT ALLOWED]: 'hilogd' cannot be started in conditional mode<br> 
  [WARNING]: selinux status is xxx
  [WARNING]: xxx 'secon' is empty
```

## 3. 违规场景及处理方案建议

  1. 检查违规项是否是耗时命令，其次该命令存在文件路径是否包含白名单中， 如果不在，根据要求添加命令到白名单

  2. 检查服务启动类型， 根据 **[规则解释](README.md#2-规则解释)** 排查修改
