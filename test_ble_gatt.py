#!/usr/bin/env python3
"""
BLE GATT功能测试脚本
测试真正的Bluetooth Low Energy连接
"""

import sys
import time
import json
from typing import Dict, Any

# 模拟配置模块
class MockConfig:
    commands = [0.0, 0.0, 0.0]
    center_x = 0.0
    
    class ble:
        enabled = True
        device_name = "Dot_D1_Robot"
        service_uuid = "12345678-1234-1234-1234-123456789abc"
        command_char_uuid = "87654321-4321-4321-4321-cba987654321"
        status_char_uuid = "11111111-2222-3333-4444-555555555555"
        heartbeat_timeout = 2.0
        status_broadcast_interval = 0.1
        speed_limit = 0.2
        rotation_speed_limit = 0.4
        center_adjust_step = 0.001
    
    class real:
        motor_angle_exceed = 0
        imu_angle_exceed = 0

# 替换配置模块
sys.modules['Dot_D1_config'] = MockConfig()

def test_ble_gatt_functionality():
    """测试BLE GATT功能"""
    print("BLE GATT功能测试")
    print("=" * 50)
    
    # 测试导入
    try:
        import ble_gatt_server
        print("✓ BLE GATT模块导入成功")
        
        if not ble_gatt_server.BLE_AVAILABLE:
            print("✗ BLE GATT库不可用")
            return False
            
        print("✓ BLE GATT库可用")
    except ImportError as e:
        print(f"✗ BLE GATT模块导入失败: {e}")
        return False
    
    # 测试服务创建
    try:
        service = ble_gatt_server.Dot_D1_BLE_Service()
        print("✓ BLE GATT服务创建成功")
        print(f"  服务UUID: {service.service_uuid}")
    except Exception as e:
        print(f"✗ BLE GATT服务创建失败: {e}")
        return False
    
    # 测试指令处理
    print("\n=== 测试指令处理 ===")
    test_commands = [
        {"cmd": "move", "x": 0.2, "y": 0.0, "z": 0.0},
        {"cmd": "button", "button": 1},
        {"cmd": "stop"},
        {"cmd": "ping"}
    ]
    
    for i, cmd in enumerate(test_commands):
        print(f"测试指令 {i+1}: {cmd}")
        service.process_command(cmd)
        print(f"  结果: commands={MockConfig.commands}")
        MockConfig.commands = [0.0, 0.0, 0.0]  # 重置
    
    print("✓ 指令处理测试完成")
    
    # 测试服务器创建
    try:
        server = ble_gatt_server.BLE_Server()
        print("✓ BLE服务器实例创建成功")
    except Exception as e:
        print(f"✗ BLE服务器创建失败: {e}")
        return False
    
    print("\n=== BLE连接信息 ===")
    print("设备名称: Dot_D1_Robot")
    print("服务UUID: 12345678-1234-1234-1234-123456789abc")
    print("指令特征值UUID: 87654321-4321-4321-4321-cba987654321")
    print("状态特征值UUID: 11111111-2222-3333-4444-555555555555")
    
    print("\n=== 连接指南 ===")
    print("1. 在移动设备上打开BLE扫描APP（如nRF Connect）")
    print("2. 搜索名为 'Dot_D1_Robot' 的BLE设备")
    print("3. 连接设备并查看GATT服务")
    print("4. 找到自定义服务 (12345678-...)")
    print("5. 向指令特征值写入JSON格式指令")
    print("6. 从状态特征值读取机器人状态")
    
    print("\n=== 指令格式 ===")
    print('前进: {"cmd":"move","x":0.2,"y":0,"z":0}')
    print('停止: {"cmd":"stop"}')
    print('按键: {"cmd":"button","button":1}')
    print('心跳: {"cmd":"ping"}')
    
    return True

def test_integration():
    """测试与主系统的集成"""
    print("\n=== 测试系统集成 ===")
    
    try:
        import ble_remote
        print("✓ 主BLE模块导入成功")
        
        # 测试启动函数
        print("启动BLE服务器线程...")
        thread = ble_remote.start_ble_server_thread()
        
        if thread:
            print("✓ BLE服务器线程启动成功")
            print("等待5秒让服务器完全启动...")
            time.sleep(5)
            print("✓ BLE服务器应该已经就绪")
        else:
            print("✗ BLE服务器线程启动失败")
            return False
            
    except Exception as e:
        print(f"✗ 系统集成测试失败: {e}")
        return False
    
    return True

def main():
    """主测试函数"""
    success = True
    
    # 基础功能测试
    if not test_ble_gatt_functionality():
        success = False
    
    # 集成测试
    if not test_integration():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("✅ 所有BLE GATT测试通过！")
        print("\n现在您可以使用真正的BLE连接:")
        print("- 设备名: Dot_D1_Robot")
        print("- 协议: Bluetooth Low Energy (GATT)")
        print("- 推荐APP: nRF Connect, LightBlue等")
    else:
        print("❌ 部分测试失败，请检查BLE环境")
    
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