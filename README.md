# Dot_D1 双足机器人控制系统

## 项目概述

Dot_D1是一个基于强化学习的双足机器人实时控制系统，实现了从仿真训练到实体机器人部署的完整解决方案。系统通过PyTorch深度学习模型进行步态控制，支持多种运动模式和实时遥控操作。

## 核心特性

- 🤖 **双足步态控制**：基于强化学习训练的步态生成算法
- 🎮 **多种控制方式**：支持433MHz遥控器、PS2手柄等多种输入设备
- 📡 **CAN总线通信**：高可靠性的电机控制和状态反馈
- 🧭 **IMU姿态检测**：实时姿态监测和安全保护
- 🔄 **在线自适应**：动态切换运动模式和异常恢复
- ⚡ **实时性能**：10ms控制周期，确保平稳运动

## 系统架构

### 硬件架构
- **主控制器**：支持双CAN总线的嵌入式控制板
- **执行器**：8个智能伺服电机（每条腿4个关节）
- **传感器**：IMU惯性测量单元、电机编码器
- **通信接口**：CAN0/CAN1双总线、串口（IMU）、GPIO（遥控器）

### 软件架构
```
Dot_D1/
├── Dot_D1_config.py      # 系统配置参数
├── Dot_D1_run.py         # 主控制程序
├── Dot_D1_launch.sh      # 启动脚本
├── mi_motor_drive.py     # 电机驱动模块
├── synch_run.py          # 多线程同步模块
├── fixed_action.py       # 固定动作序列
├── 433M_demo.py          # 433MHz遥控器接口
├── imu_demo.py           # IMU数据接口
├── ps2_demo.py           # PS2手柄接口
└── rl_model/             # 强化学习模型
    ├── policy_yd.pt      # 运动策略模型
    └── policy_jz.pt      # 静止策略模型
```

## 主要功能模块

### 1. 强化学习控制器 (Dot_D1_run.py)
- **模型推理**：使用PyTorch JIT优化的策略网络
- **状态估计**：融合关节位置、速度、IMU数据
- **双模式切换**：运动模式(policy_yd)和静止模式(policy_jz)
- **安全监控**：实时检测关节超限和IMU异常

### 2. 电机控制系统 (mi_motor_drive.py)
- **CAN通信**：支持扩展帧格式的高速通信
- **运动控制**：位置-速度-扭矩复合控制模式
- **参数配置**：支持PD参数、限位、零点校准
- **状态反馈**：实时获取位置、速度、扭矩、温度

### 3. 传感器接口
- **IMU模块** (imu_demo.py)：获取加速度、角速度、欧拉角、四元数
- **遥控接口** (433M_demo.py)：433MHz无线遥控器按键处理
- **手柄支持** (ps2_demo.py)：PlayStation 2手柄兼容

### 4. 多线程架构 (synch_run.py)
- **CAN读写线程**：左右腿独立的CAN总线管理
- **传感器线程**：IMU数据采集和遥控器状态监测
- **主控线程**：策略推理和运动控制协调

## 配置参数

### 关节角度范围 (弧度)
```python
# 左腿关节限位
l_h_p_j: [-1.5, 0.5]    # 左髋俯仰
l_h_r_j: [-1.3, 0.35]   # 左髋翻滚  
l_k_j:   [-2.0, 0.2]    # 左膝关节
l_jz_j:  [-1.0, 0.4]    # 左脚踝

# 右腿关节限位
r_h_p_j: [-0.5, 1.5]    # 右髋俯仰
r_h_r_j: [-0.35, 1.3]   # 右髋翻滚
r_k_j:   [-0.2, 2.0]    # 右膝关节  
r_jz_j:  [-0.4, 1.0]    # 右脚踝
```

### 控制参数
```python
# 仿真参数
dt = 0.001              # 仿真时间步长
decimation = 10         # 控制降采样率
action_scale = 0.25     # 动作缩放系数
frame_stack = 15        # 历史帧堆叠

# 电机PD参数
KP = [9.0, 9.0, 9.0, 4.0]  # 刚度系数
KD = [0.5, 0.5, 0.5, 0.2]  # 阻尼系数
```

## 安装部署

### 环境要求
```bash
# Python依赖
pip install torch numpy can-python wiringpi pygame serial

# 系统配置
sudo apt-get install can-utils
```

### 硬件配置
```bash
# CAN总线设置
sudo ip link set down can0
sudo ip link set can0 type can bitrate 1000000 loopback off  
sudo ip link set up can0

sudo ip link set down can1
sudo ip link set can1 type can bitrate 1000000 loopback off
sudo ip link set up can1

# 串口权限
sudo chmod 777 /dev/ttyUSB0

# CPU性能模式
sudo cpufreq-set -c 0 -g performance
sudo cpufreq-set -c 1 -g performance
sudo cpufreq-set -c 2 -g performance  
sudo cpufreq-set -c 3 -g performance
```

### 运行步骤
1. **系统启动**
```bash
cd Dot_D1/
chmod +x Dot_D1_launch.sh
./Dot_D1_launch.sh
```

2. **初始化检查**
- 确认所有电机已上电并脱离支架
- 按遥控器左1键启动电机初始化

3. **姿态校准**  
- 机器人执行微蹲姿态初始化
- 确认姿态正确后按左1键开始运动

4. **运动控制**
```bash
# 遥控器按键功能
前进: 按键1    后退: 按键2
左移: 按键3    右移: 按键4  
左转: 按键7    右转: 按键9
重心调节: 长按按键5
```

## 安全机制

### 异常检测
- **关节超限保护**：实时监测关节角度范围
- **IMU异常检测**：检测倾倒和传感器故障
- **通信超时检测**：CAN总线和串口通信监控

### 自动恢复
- **垂直腿姿态**：检测到异常时自动切换到安全姿态
- **重新初始化**：5秒延迟后恢复到微蹲姿态
- **手动重启**：支持遥控器手动重启控制

### 运行监控
```python
# 关键监控指标
motor_angle_exceed    # 关节超限标志
imu_angle_exceed     # IMU异常标志  
imu_abnormal         # IMU通信异常
```

## 性能指标

- **控制频率**：100Hz (10ms周期)
- **模型推理**：~2-5ms (降采样执行)
- **CAN通信延迟**：<1ms
- **关节精度**：±0.01弧度
- **连续运行时间**：>2小时

## 开发扩展

### 添加新传感器
1. 在`synch_run.py`中添加传感器读取线程
2. 在`Dot_D1_config.py`中定义数据结构
3. 在`read_obs()`中整合传感器数据

### 自定义控制模式
1. 训练新的强化学习模型
2. 将模型保存为`.pt`格式放入`rl_model/`
3. 在主程序中加载和切换模型

### 扩展通信接口
- 支持WiFi/蓝牙遥控
- 添加视觉传感器接口
- 集成语音控制模块

## 故障排除

### 常见问题

**1. 电机无响应**
```bash
# 检查CAN总线状态
ip link show can0
ip link show can1

# 测试CAN通信
cansend can0 123#DEADBEEF
candump can0
```

**2. IMU数据异常**
```bash
# 检查串口连接
ls /dev/ttyUSB*
sudo chmod 777 /dev/ttyUSB0

# 测试串口通信  
python imu_demo.py
```

**3. 模型加载失败**
- 检查PyTorch版本兼容性
- 确认模型文件路径正确
- 验证CUDA/CPU设备配置

**4. 实时性问题**
- 设置CPU为性能模式
- 关闭不必要的系统服务
- 调整线程优先级

## 技术支持

- **文档更新**：定期更新配置参数和API说明
- **示例代码**：提供完整的使用示例
- **调试工具**：内置日志和状态监控

## 许可证

本项目采用MIT许可证，详见LICENSE文件。

---

*最后更新：2024年*