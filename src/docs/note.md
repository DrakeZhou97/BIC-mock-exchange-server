# BIC 数据流

## 机器人动作流程
[Mars 框架](https://carbon12.feishu.cn/wiki/OQHbwfVxoiMDc7kkN0jciOX1nhc?from=from_copylink)

### 准备动作

#### 架设柱子

机器人会根据silica_cartridge_location_id和sample_cartridge_location_id所在位置，前往对应站点，完成这两个柱子的获取，然后根据work_station_id的位置，前往对应站点，完成两个柱子的架设，然后在原地回到idle姿态待命。

setup_cartridges
```json Request
{
    "task_id": "xxx", // 调用端定义id
    "task_name": "setup_tubes_to_column_machine", // 调用端定义id
    "params": {
        "silica_cartridge_location_id": "bic_09B_l3_001", // MVP 版本固定id
        "silica_cartridge_type": "sepaflash_40g", // MVP 版本固定type
        "silica_cartridge_id": "sepaflash_40g_001", // 调用端定义id
        "sample_cartridge_location_id": "bic_09B_l3_001", // MVP 版本固定id
        "sample_cartridge_type": "ilok_40g", // MVP 版本固定type
        "sample_cartridge_id": "ilok_40g_001", // 调用端定义id
        "work_station_id": "fh_ccs_001" // MVP 版本固定id
    }
}
```

```json Response
{
    "code": 200,
    "msg": "success",
    "task_id": "xxx",
    "updates": [
        {
            "type": "robot",
            "id": "talos_001",
            "properties": {
                "location": "work_station_id",
                "state": "idle"
            }
        },
        {
            "type": "silica_cartridge", // 硅胶柱
            "id": "sepaflash_40g_001",
            "properties": {
                "location": "work_station_id",
                "state": "mounted"
            } 
        },
        {
            "type": "sample_cartridge", // 拌样柱
            "id": "ilok_40g_001",
            "properties": {
                "location": "work_station_id",
                "state": "mounted"
            } 
        },
        {
            "type": "ccs_ext_module", // 过柱机外置机构
            "id": "ccs_ext_module_001"，
            "properties": {
                "state": "using" // 表示这个外置机构正在被使用
            }
        }
    ]
}
```

##### 疑问
- 状态变更通过log管道发送消息，消息格式如Response，每次更新有一条或多条update，会在状态发生变更时及时发出，不是在整个动作结束后一起发出

#### 架设试管架

机器人会根据location_id所在位置，前往对应站点，双手抓取试管架，然后根据work_station_id的位置，前往对应站点，完成试管架的架设。

setup_tube_rack
```json Request
{
    "task_id": "xxx",
    "task_name": "setup_tube_rack",
    "params": {
        "tube_rack_location_id": "bic_09C_l3_002", // MVP 阶段固定
        "work_station_id": "fh_ccs_001", // MVP 阶段固定
        "end_state": "wait_for_screen_manipulation" // default to idle, 为了顺畅衔接后续动作
    }
}
```

```json Response
{
    "code": 200,
    "task_id": "xxx",
    "msg": "success",
    "updates": [
        {
            "type": "robot",
            "id": "talos_001",
            "properties": {
                "location": "work_station_id",
                "state": "wait_for_screen_manipulation"
            }
        },
        {
            "type": "tube_rack",
            "id": "tube_rack_001",
            "properties": {
                "location": "work_station_id",
                "state": "mounted"
            }
        }
    ]
}
```

##### 疑问
- tube_rack_location_id，work_station_id 类型enum？ #TODO 叶少补充到type声明里，默认值或者comment

#### 拍照

机器人会根据location_id所在位置，前往对应站点（如果已经在这里就不会动），完成设备component的locate，然后完成对component的拍摄。

take_photo
```json Request
// 值守过柱过程中的拍照观察
{
    "task_id": "xxx",
    "task_name": "take_photo",
    "params": {
        "work_station_id": "fh_ccs_001", // 过柱，旋蒸是"fh_evaporate_001"
        "device_id": "isco_combiflash_001",
        "device_type": "isco_combiflash_nextgen_300", // evaporator
        "components": ["screen"],
        "end_state": "watch_column_machine_screen"
    }
}
// 值守旋蒸过程中的拍照观察
{
    "task_id": "xxx",
    "task_name": "take_photo",
    "params": {
        "work_station_id": "fh_evaporate_001",
        "device_id": "evaporator_001",
        "device_type": "evaporator",
        "components": "screen",
        "end_state": "watch_column_machine_screen"
    }
}
```

```json Response
{
    "code": 200,
    "task_id": "xxx",
    "msg": "success",
    "updates": [
        {
            "type": "robot",
            "id": "talos_001",
            "properties": {
                "location": "work_station_id",
                "state": "watch_column_machine_screen"
            }
        },
        {
            "type": "isco_combiflash_nextgen_300",
            "id": "isco_combiflash_001",
            "properties": {
                "state": "terminated",
                "experiment_params": {
                    "silicone_column": "40g",
                    "peak_gathering_mode": "peak", // 峰收集模式: all, peak, none
                    "air_clean_minutes": 3, // 空气吹扫3分钟
                    "run_minutes": 30, // 运行时长30分钟
                    "need_equilibration": true, // 是否需要润柱
                    "left_rack": "16x30mm", // 左试管架规格为16x30mm
                    "right_rack": null, // 不用右试管架
                },
                "start_timestamp": "2025-01-13_01-17-25.312"
            }
        }
    ],
    "images": [
        {
            "work_station_id": "fh_evaporate_001",
            "device_id": "evaporator_001",
            "device_type": "evaporator",
            "component": "screen", // 对准旋蒸机屏幕拍照
            "url": "http://xxxxx.jpg"
        },
        {
            "work_station_id": "fh_evaporate_001",
            "device_id": "evaporator_001",
            "device_type": "evaporator",
            "component": "round_bottom_flask", // 对准茄形瓶拍照
            "url": "http://xxxxx.jpg"
        }
    ]
}
```

##### 疑问
- components 类型 list[Enum] #TODO 叶少补充

### CC流程

#### 开始CC

机器人会根据location_id所在位置，前往对应站点（如果已经在这里就不会动），完成屏幕的locate，然后根据指定参数操作屏幕，开始润柱、过柱，并直到结束，终止过柱，回到end_state。

start_column_chromatography
```json Request
{
    "task_id": "xxx",
    "task_name": "start_column_chromatography",
    "params": {
        "work_station_id": "fh_ccs_001",
        "device_id": "isco_combiflash_001", 
        "device_type": "column_chromatography_system",
        "experiment_params": {
            "silicone_column": "40g",
            "peak_gathering_mode": "peak", // 峰收集模式: all, peak, none
            "air_clean_minutes": 3, // 空气吹扫3分钟
            "run_minutes": 30, // 运行时长30分钟
            "need_equilibration": true, // 是否需要润柱
            "left_rack": "16x30mm", // 左试管架规格为16x30mm
            "right_rack": null, // 不用右试管架
        },
        "end_state": "watch_column_machine_screen"
    }
}
```

```json Response
{
    "code": 200,
    "task_id": "xxx",
    "msg": "success",
    "updates": [
        {
            "type": "robot",
            "id": "talos_001",
            "properties": {
                "location": "work_station_id",
                "state": "watch_column_machine_screen"
            }
        }，
        {
            "type": "isco_combiflash_nextgen_300",
            "id": "isco_combiflash_001",
            "properties": {
                "state": "running",
                "experiment_params": {
                    "silicone_column": "40g",
                    "peak_gathering_mode": "peak", // 峰收集模式: all, peak, none
                    "air_clean_minutes": 3, // 空气吹扫3分钟
                    "run_minutes": 30, // 运行时长30分钟
                    "need_equilibration": true, // 是否需要润柱
                    "left_rack": "16x30mm", // 左试管架规格为16x30mm
                    "right_rack": null, // 不用右试管架
                },
                "start_timestamp": "2025-01-13_01-17-25.312"
            }
        },
        {
            "type": "silica_cartridge",
            "id": "sepaflash_40g_001",
            "properties": {
                "location": "work_station_id",
                "state": "using" // 这个硅胶柱正在被使用
            } 
        },
        {
            "type": "sample_cartridge",
            "id": "ilok_40g_001",
            "properties": {
                "location": "work_station_id",
                "state": "using" // 表示这个拌样柱正在被使用
            } 
        },
        {
            "type": "tube_rack",
            "id": "tube_rack_001",
            "properties": {
                "location": "work_station_id",
                "state": "using" // 表示这个试管架正在被使用
            }
        },
        {
            "type": "ccs_ext_module", // 过柱机外置机构
            "id": "ccs_ext_module_001"，
            "properties": {
                "state": "using" // 表示这个外置机构正在被使用
            }
        },
        {
            "type": "column_chromatography_system", // 过柱机
            "id": "isco_combiflash_001"，
            "properties": {
                "state": "using" // 表示这个过柱机正在被使用
            }
        }
    ]
}
```

##### 疑问
- device_id 固定？or sender 给定？
- device_type enum？
- end_state enum？
- experiment_params 参数类型定义

#### 结束CC

- 机器人会根据location_id所在位置，前往对应站点（如果已经在这里就不会动），完成过柱机屏幕操作，终止正在进行的过柱任务，拍摄过柱结果界面的图片并返回。
- 目前默认情况下，机器人完成这次过柱结果的拍照后，过柱机界面保持在最终终止、呈现过柱结果的界面。机器人下次启动过柱时需要再行判断，是否要关闭当前界面，然后开始新实验。

terminate_column_chromatography
```json Request
{
    "task_id": "xxx",
    "task_name": "terminate_column_chromatography",
    "params": {
        "work_station_id": "fh_cc_001",
        "device_id": "isco_combiflash_001",
        "device_type": "isco_combiflash_nextgen_300",
        "end_state": "idle"
    }
}
```

```json Response
{
    "code": 200,
    "task_id": "xxx",
    "msg": "success",
    "updates": [
        {
            "type": "robot",
            "id": "talos_001",
            "properties": {
                "location": "work_station_id",
                "state": "idle"
            }
        },
        {
            "type": "isco_combiflash_nextgen_300",
            "id": "isco_combiflash_001",
            "properties": {
                "state": "terminated",
                "experiment_params": {
                    "silicone_column": "40g",
                    "peak_gathering_mode": "peak", // 峰收集模式: all, peak, none
                    "air_clean_minutes": 3, // 空气吹扫3分钟
                    "run_minutes": 30, // 运行时长30分钟
                    "need_equilibration": true, // 是否需要润柱
                    "left_rack": "16x30mm", // 左试管架规格为16x30mm
                    "right_rack": null, // 不用右试管架
                },
                "start_timestamp": "2025-01-13_01-17-25.312"
            }
        },
        {
            "type": "silica_cartridge",
            "id": "sepaflash_40g_001",
            "properties": {
                "location": "work_station_id",
                "state": "used"
            } 
        },
        {
            "type": "sample_cartridge",
            "id": "ilok_40g_001",
            "properties": {
                "location": "work_station_id",
                "state": "used"
            } 
        },
        {
            "type": "tube_rack",
            "id": "tube_rack_001",
            "properties": {
                "location": "work_station_id",
                "state": "used"
            }
        },
        {
            "type": "ccs_ext_module", // 过柱机外置机构
            "id": "ccs_ext_module_001"，
            "properties": {
                "state": "used" // 外置机构目前处于被使用状态，意为这一次过柱完成了，柱子还没拆
            }
        },
    ]
}
```

##### 疑问
- [x] 机器人下次启动过柱时需要再行判断， 这个判断现在有做吗，还是需要人为恢复

#### 收集分液
- 包含机器人拉出试管架，收集指定洗脱管中的溶液，倒掉其余溶液，丢弃试管架，合上废液桶盖子，抓取茄形瓶的完整动作序列
- 机器人会根据location_id所在位置，前往对应站点（如果已经在这里就不会动），完成上述的所有动作序列。

fraction_consolidation
```json Request
{
    "task_id": "xxx",
    "task_name": "fraction_consolidation",
    "params": {
        "work_station_id": "fh_cc_001",
        "device_id": "isco_combiflash_001",
        "device_type": "isco_combiflash_nextgen_300",
        "collect_config": [0, 0, 0, 1, 1, 1, 1, 0, 0, 0],
        "end_state": "moving_with_round_bottom_flask"
    }
}
```

```json Response
{
    "code": 200,
    "task_id": "xxx",
    "msg": "success",
    "updates": [
        {
            "type": "robot",
            "id": "talos_001",
            "properties": {
                "location": "work_station_id",
                "state": "moving_with_round_bottom_flask" // 机器人手持茄形瓶，可以移动的姿态
            }
        },
        {
            "type": "tube_rack",
            "id": "tube_rack_001",
            "properties": {
                "location": "work_station_id",
                "state": "used,pulled_out,ready_for_recovery" // 这里我还没想的很清楚，想表达的是，目前试管架已经用过了，拉出来了，已经可以被拿去回收处理了
            }
        },
        {
            "type": "round_bottom_flask",
            "id": "rbf_001",
            "properties": {
                "location": "work_station_id",
                "state": "used,ready_for_evaporate" // 已经收集完，可以用于旋蒸的状态
            }
        },
        {
            "type": "pcc_left_chute",
            "id": "pcc_left_chute_001", // post-column-chromatography
            "properties": {
                "pulled_out_mm": 12, // 被拉出的距离（这里仅做一个状态记录，后续机器人操作不会严格依赖的，会确保重新安全地观察这个抽屉的状态，来自行妥善处理）
                "pulled_out_rate": 0.02, // 被拉出的比例
                "closed": false,
                "front_waste_bin": "close", // open表示已开盖，close表示已关盖，null表示不存在，即未架设
                "back_waste_bin": "full" // 暂时拍的，表示后面的桶满了，后面大概率要重新想想，可能会改
            }
        },
        {
            "type": "pcc_right_chute",
            "id": "pcc_right_chute_001", // post-column-chromatography
            "properties": {
                "pulled_out_mm": 0.464, // 被拉出的距离
                "pulled_out_rate": 0.8, // 被拉出的比例
                "closed": false,
                "front_waste_bin": "full", // 暂时瞎拍的，留个空，用过的试管桶一律认为满了，后面再讨论再改
                "back_waste_bin": "full"
            }
        }
    ]
}
```

- collect_config: 表示过柱机收集试管的顺序下，每个试管是否要收集，1表示要，0表示不要。list长度应当为所有用到的试管的长度，机器人呢也只会处理这些数量的试管。

##### 疑问
- 如何获取/计算collect_config

### RE流程

#### 执行RE
- 包括机器人工作：前往旋蒸通风橱，架设茄形瓶，操作真空泵，设置旋蒸机参数，开始旋蒸
- 机器人会根据location_id所在位置，前往对应站点（如果已经在这里就不会动），完成上述的所有动作序列。
- 机器人自己会对技能做一些最基本的前置条件检查，比如它会确认自己当前是不是拿着一个待旋蒸的茄形瓶，如果不是，那会拒绝这个技能，并返回相应报错信息。

start_evaporation
```json Request
{
  "task_id": "xxx",
  "task_name": "start_evaporation",
  "params": {
    "work_station_id": "fh_evaporate_001",
    "device_id": "evaporator_001",
    "device_type": "evaporator",
    "profiles": {  // 可以设置套的参数，用于不同情况
        "start": { // start为保留键，表示开始时的初始状态，不需要trigger
            "lower_height": 60.5, // 茄形瓶要下降的高度, 单位mm
            "rpm": 60, // 转速, 单位rpm
            "target_temperature": 40, // 水浴加热温度，单位摄氏度
            "target_pressure": 660, // 真空泵压力, 单位mbar，初始参数会再压力到达后才松开茄形瓶
        },
        "stop": { // stop为保留键（可以不提供, 则不预先指定停止动作）, 表示结束的条件, 机器人点击stop一键停止, 不用设置固定参数。这里的stop仅为停止旋蒸机，不涉及取下茄形瓶
            "trigger": {
                "type": "time_from_start",
                "time_in_sec": 3600 // 旋蒸开始后一小时结束
            }
        },
        "lower_pressure": {
            "lower_height": 60.5,
            "rpm": 60, 
            "target_temperature": 40,
            "target_pressure": 240,
            "trigger": {
                "type": "time_from_start", // 延时触发
                "time_in_sec": 600 // 开始旋蒸后10分钟切为这个参数
            }
        },
        "reduce_bumping": { // 爆沸应对参数，不期望发生，作为安全兜底
            "lower_height": 59, // 爆沸时抬高一点茄形瓶，减小水浴接触面积
            "rpm": 60, 
            "target_temperature": 40, // 温度不变
            "target_pressure": 500, // 升高压力，缓解爆沸
            "trigger": {
                "type": "event", // 基于事件触发
                "event_name": "bumping" // 需要机器人具备爆沸检测能力
            }
        }
    },
    "post_run_state": "observe_evaporation" // 如果profiles里只有start，这里是idle，则机器人启动旋蒸后就解放了。如果需要机器人值守，持续观察，则这里要设置为观察state
  }
}
```

```Response
{
    "code": 200,
    "task_id": "xxx",
    "msg": "success",
    "updates": [
        {
            "type": "robot",
            "id": "talos_001",
            "properties": {
                "location": "work_station_id",
                "state": "observe_evaporation"
            }
        },
        {
            "type": "round_bottom_flask",
            "id": "rbf_001",
            "properties": {
                "location": "fh_evaporate_001",
                "state": "used,evaporating" // used表示不干净了，有液体，被使用过，evaporating表示正在旋蒸
            }
        },
        {
            "type": "evaporator",
            "id": "evaporator_001", // post-column-chromatography
            "properties": {
                "running": true, // 表示已启动，启动其实主要是启动水浴加热
                "lower_height": 60.5, // 茄形瓶下降的高度, 单位mm
                "rpm": 60, // 当前转速, 单位rpm
                "target_temperature": 40, // 目标水浴加热温度
                "current_temperature": 36, // 当前水浴加热温度
                "target_pressure": 660,
                "current_pressure": 659
            }
        }
    ]
}
```

## Mind MCP工具

### CC流程

[产品文档](https://carbon12.feishu.cn/wiki/LFxkwHM7liAjuJkXxWVc07DznAg#share-FwUwdUyeoo5jAixjsnNcxW6anXf)

#### input

| 字段          | 解释                                     | 数据类型                               | 限制/要求                                                              | 样例(前端)                           |
| ------------- | ---------------------------------------- | -------------------------------------- | ---------------------------------------------------------------------- | ------------------------------------ |
| TLC结果       | TLC点板的图片                            | -                                      | 实验过程中收集或用户输入，上文中没有则要求用户提供                     | -                                    |
| 结果Rf值      | TLC点板解读                              | float                                  | 实验过程中收集或用户输入，0~1之间，保留2位小数 mvp字段1                | 0.52                                 |
| TLC展开剂体系 | 最终尝试的展开剂比例                     | Enum[PE/EA,DCM/MeOH]                   | 实验过程中收集或用户输入 mvp字段2                                      | PE/EA                                |
| TLC展开剂比例 | 最终尝试的展开剂比例                     | (int):(int), 整数的比例                | 实验过程中收集或用户输入 mvp字段3                                      | 2:1                                  |
| 反应式        | 反应的smiles，后期可能的需求是用画板实现 | string                                 | 如果上文中没有则需要用户提供，校验服务由AI算法团队提供，应该以前是有的 | NC1=CC=C(C(C2=CC=C2NC1=O)OCCOCCO)=C1 |
| 样品量        | 样品的量(g)                              | float optional(目前阶段用户自己装柱子) | 如果上文中没有则需要用户提供，保留2位小数                              | 10.21                                |

#### output

| 字段         | 解释                                 | 数据类型                      | 限制/要求 | 样例(前端) |
| ------------ | ------------------------------------ | ----------------------------- | --------- | ---------- |
| 洗脱剂体系   | 洗脱剂体系                           | 略                            | 略        | 略         |
| 梯度点       | 过柱的梯度点                         | List[{时间, 比例(百分比)}]    | 略        | 略         |
| 柱子规格     | 由样品量计算得出，由于是人装好，可选 | Enum[4,12,25,40,120] optional | 略        | 略         |
| 硅胶量的选择 | 由样品量计算得出，由于是人装好，可选 | float, optional               | 略        | 略         |


### RE流程
[产品文档](https://carbon12.feishu.cn/wiki/LFxkwHM7liAjuJkXxWVc07DznAg#share-Zx8RdDtghoNBrmxtm8VcyQvOnx9)

#### input

| 字段     | 解释               | 数据类型                | 限制/要求                                                                                                 | 样例(前端) |
| -------- | ------------------ | ----------------------- | --------------------------------------------------------------------------------------------------------- | ---------- |
| 溶剂体系 | 过柱对应的溶剂体系 | Enum[PE/EA,DCM/MeOH]    | 过柱中用的体系收集或用户输入                                                                              | PE/EA      |
| 溶剂比例 | 过柱对应的溶剂比例 | {int}:{int}, 整数的比例 | 用户输入或过柱结果识别，用于计算最终每个溶剂的量，由于正向的都很好旋，可以按都是这个溶剂设，所以 optional | 2:1        |
| 溶剂的量 | 溶剂的量           | ml                      | 试管数*单个试管的体积(15ml) 或者用户输入                                                                  | 100ml      |

#### output

| 字段 | 解释           | 数据类型          | 限制/要求 | 样例(前端) |
| ---- | -------------- | ----------------- | --------- | ---------- |
| 温度 | 旋蒸的温度     | int               | 0~90度    | 40         |
| 气压 | 降压的梯度曲线 | List[{时间,气压}] | 略        | 略         |
