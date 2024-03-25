# 插件化白名单规则说明

## 规则解释
  白名单严格遵循JSON格式。

  ### **init扩展插件检查**
  **[白名单](whitelist.json)** 约束插件依赖。

  - 规则要求
  1. 约束除基础库外的动态库。
  2. 插件不在白名单内。

  - 白名单信息解释
    ```
    {
        "base_library":[
            "libc.so",
            "libc++.so",
            "libinit_module_engine.so"
        ],
        "private_library": {
            "libudidmodule.z.so": {  // 插件模块动态库
                "library_name" : "libudidmodule.z.so",
                "deps" : [
                    "libsec_shared.z.so",
                    "libmbedtls.z.so"
                ]
            }
        }
    }
    ```
    1. base_library: 白名单基础库。
    2. private_library: 插件依赖动态库。
    3. library_name: 插件动态库。
    4. deps: 插件依赖动态库。

  - 解决方法
  1. 排查插件安装目录: system/lib/init、vendor/lib/init、sys_prod/lib/init、chip_prod/lib/init。
  2. 排查插件是否在白名单中配置。
  3. 排查插件依赖动态库是否找白名单中配置。base_library 之外的动态库，添加在private_library列表中。


编译时会提示如下类型的告警：
  ```
  [NOT ALLOWED]: the dependent shared library libmbedtls.z.so of libudidmodule.z.so is not in whitelist
  [NOT ALLOWED]: libinit_eng.z.so is not in whitelists
```

## 违规场景及处理方案建议
  1. 根据 **[规则解释](README.md#规则解释)** 排查修改, 如果需要添加白名单，需要评审。
