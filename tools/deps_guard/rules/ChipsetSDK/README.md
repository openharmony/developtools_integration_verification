# ChipsetSDK白名单规则说明



## 1. Chipset SDK的定义

系统组件模块：安装到system.img中的模块，与芯片和硬件无关。

芯片组件模块：安装到chipset.img中的模块，与芯片或硬件强相关。



Chipset SDK是指允许被芯片组件模块依赖的系统组件动态库模块集合。

Chipset SDK集合中的单个模块称之为ChipsetSDK模块。

## 2. 规则解释

Chipset SDK白名单规则有几个方面的含义：

### 2.1 Chipset SDK模块需要在编译模板中标识

如下图所示，每个Chipset SDK模块需要在对应的BUILD.gn中通过innerapi_tags增加chipsetsdk标签来标识其类型：

```go
ohos_shared_library(sample_sa_module) {
    ...
    innerapi_tags = [ "chipsetsdk" ]
    ...
}
```

如果没有此标记，编译时会提示如下类型的告警：

```shell
[WARNING]: Chipset SDK module libinit_stub_empty.so has no innerapi_tags with "chipsetsdk" or "csdk", add it in //base/startup/init/interfaces/innerkits/init_module_engine:libinit_stub_empty
```

同样，非Chipset SDK不要增加此标记。

### 2.2 芯片组件模块不允许依赖Chipset SDK集合之外的模块

违法此规则时，会产生如下格式的NOT ALLOWED错误：

```
[NOT ALLOWED]: chipset module libNNN.z.so depends on non Chipset SDK module libsystemMMM.z.so in //NNNpath:libNNN
```

该错误的含义是：芯片组件的libNNN.z.so模块依赖了libsystemMMM.z.so，而libsystemMMM.z.so并不是被认可（白名单中）的模块。

违法此规则时，参考下一章节的处理方案进行消除：

## 3. 违规场景及处理方案建议

### 3.1 检查违规模块的安装组件是否正确

首先确认libNNN.z.so是否应该是芯片组件产物，只有与硬件相关的HDI实现模块才需要安装到芯片组件。

如下所示，每个模块是通过install_images选项来决定安装到系统组件还是芯片组件；如果系统组件模块错误的安装到芯片组件，可能会因为该模块依赖了Chipset SDK之外的系统组件模块而违反此规则。

```go
ohos_shared_library(libNNN) {
    ...
    install_images = [ chipset_base_dir ]
    ...
}
```

因此，首先需要检查违规模块是否安装到了错误的组件；如果libNNN.z.so不是芯片组件的产物，则install_images里不能填chipset_base_dir；删除install_images后，默认就是安装到系统组件。

### 3.2 申请新的Chipset SDK模块

如果经过分析，芯片组件的libNNN.z.so确实需要引入新的Chipset SDK模块，可向架构SIG申请加入Chipset SDK白名单。
