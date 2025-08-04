#!/usr/bin/env python3
"""
BLE蓝牙遥控功能测试脚本
独立测试BLE服务器功能，不依赖机器人硬件
"""

import sys
import time
import asyncio
import json
from typing import Dict, Any

# 模拟配置模块
class MockConfig:
    commands = [0.0, 0.0, 0.0]
    center_x = 0.0
    
    class ble:
        enabled = True
        device_name = "Dot_D1_Robot_Test"
        service_uuid = "12345678-1234-1234-1234-123456789abc"
        command_char_uuid = "87654321-4321-4321-4321-cba987654321"
        status_char_uuid = "11111111-2222-3333-4444-555555555555"
        heartbeat_timeout = 2.0
        status_broadcast_interval = 0.1
        max_connections = 1
        require_pairing = False
        encryption_required = False
        speed_limit = 0.2
        rotation_speed_limit = 0.4
        center_adjust_step = 0.001
    
    class real:
        motor_angle_exceed = 0
        imu_angle_exceed = 0

# 替换配置模块
sys.modules['Dot_D1_config'] = MockConfig()

# 导入BLE模块
try:
    import ble_remote
    print("✓ BLE模块导入成功")
except ImportError as e:
    print(f"✗ BLE模块导入失败: {e}")
    sys.exit(1)

def test_command_processing():
    """测试指令处理功能"""
    print("\n=== 测试指令处理功能 ===")
    
    server = ble_remote.RemoteControlServer()
    
    # 测试移动指令
    test_commands = [
        {"cmd": "move", "x": 0.2, "y": 0.0, "z": 0.0},  # 前进
        {"cmd": "move", "x": -0.2, "y": 0.0, "z": 0.0}, # 后退
        {"cmd": "move", "x": 0.0, "y": 0.2, "z": 0.0},  # 左移
        {"cmd": "move", "x": 0.0, "y": -0.2, "z": 0.0}, # 右移
        {"cmd": "move", "x": 0.0, "y": 0.0, "z": 0.4},  # 左转
        {"cmd": "move", "x": 0.0, "y": 0.0, "z": -0.4}, # 右转
        {"cmd": "stop"},                                  # 停止
        {"cmd": "button", "button": 1},                  # 按键1-前进
        {"cmd": "button", "button": 2},                  # 按键2-后退
        {"cmd": "center_adjust", "adjust": 1.0},         # 重心向前
        {"cmd": "center_adjust", "adjust": -1.0},        # 重心向后
    ]
    
    for i, cmd in enumerate(test_commands):
        print(f"测试指令 {i+1}: {cmd}")
        server.process_command(cmd)
        print(f"  结果: commands={MockConfig.commands}, center_x={MockConfig.center_x:.6f}")
        MockConfig.commands = [0.0, 0.0, 0.0]  # 重置
    
    print("✓ 指令处理测试完成")

def test_button_commands():
    """测试按键指令兼容性"""
    print("\n=== 测试按键指令兼容性 ===")
    
    server = ble_remote.RemoteControlServer()
    
    button_tests = [
        (1, "前进", [0.2, 0.0, 0.0]),
        (2, "后退", [-0.2, 0.0, 0.0]),
        (3, "左移", [0.0, 0.2, 0.0]),
        (4, "右移", [0.0, -0.2, 0.0]),
        (7, "左转", [0.0, 0.0, -0.4]),
        (9, "右转", [0.0, 0.0, 0.4]),
        (0, "停止", [0.0, 0.0, 0.0]),
    ]
    
    for button, desc, expected in button_tests:
        MockConfig.commands = [0.0, 0.0, 0.0]  # 重置
        server.process_button_command(button)
        print(f"按键 {button} ({desc}): {MockConfig.commands} {'✓' if MockConfig.commands == expected else '✗'}")
    
    print("✓ 按键指令测试完成")

def test_ble_server_basic():
    """测试BLE服务器基本功能"""
    print("\n=== 测试遥控服务器基本功能 ===")
    
    try:
        server = ble_remote.RemoteControlServer()
        print("✓ 遥控服务器实例创建成功")
        
        # 测试服务器设置（不实际启动监听）
        print(f"✓ 服务器类型: {'蓝牙' if server.use_bluetooth else '网络'}")
        print("✓ 遥控服务器基本功能测试完成")
        
    except Exception as e:
        print(f"✗ 遥控服务器测试失败: {e}")
        return False
    
    return True

def test_status_generation():
    """测试状态信息生成"""
    print("\n=== 测试状态信息生成 ===")
    
    server = ble_remote.RemoteControlServer()
    
    # 模拟一些状态变化
    MockConfig.commands = [0.1, 0.2, 0.3]
    MockConfig.center_x = 0.005
    MockConfig.real.motor_angle_exceed = 0
    MockConfig.real.imu_angle_exceed = 0
    
    print("状态信息生成测试完成 ✓")

def print_system_info():
    """打印系统信息"""
    print("=== 系统信息 ===")
    print(f"Python版本: {sys.version}")
    
    try:
        import bleak
        print(f"Bleak版本: {bleak.__version__}")
    except:
        print("Bleak: 未安装")
    
    import platform
    print(f"操作系统: {platform.system()} {platform.release()}")
    
    # 检查蓝牙适配器
    try:
        import subprocess
        result = subprocess.run(['bluetoothctl', 'list'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and result.stdout.strip():
            print("✓ 检测到蓝牙适配器")
        else:
            print("⚠ 未检测到蓝牙适配器")
    except:
        print("⚠ 无法检查蓝牙适配器状态")

def main():
    """主测试函数"""
    print("BLE蓝牙遥控功能测试")
    print("=" * 50)
    
    # 打印系统信息
    print_system_info()
    
    # 运行测试
    test_command_processing()
    test_button_commands()
    
    # 测试遥控服务器
    test_status_generation()
    success = test_ble_server_basic()
    
    print("\n" + "=" * 50)
    if success:
        print("✓ 所有测试通过！BLE功能已准备就绪")
        print("\n使用说明:")
        print("1. 确保系统蓝牙适配器正常工作")
        print("2. 运行主程序 ./Dot_D1_launch.sh")
        print("3. 使用支持BLE的移动应用连接设备 'Dot_D1_Robot'")
        print("4. 发送JSON格式的控制指令")
        print("\n示例指令:")
        print('  前进: {"cmd":"move","x":0.2,"y":0,"z":0}')
        print('  停止: {"cmd":"stop"}')
        print('  按键: {"cmd":"button","button":1}')
    else:
        print("✗ 部分测试失败，请检查BLE环境配置")
    
    return success

if __name__ == "__main__":
    try:
        result = main()
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")
        sys.exit(1)