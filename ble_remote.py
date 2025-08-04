#!/usr/bin/env python3
"""
BLE蓝牙遥控模块
实现BLE GATT遥控服务器，接收移动端遥控指令
仅支持BLE低功耗蓝牙连接方式
"""

import json
import logging
import time
import threading
from typing import Dict, Any, Optional

import Dot_D1_config as cof

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RemoteControlServer:
    """BLE遥控服务器类 - 仅支持BLE GATT"""
    
    def __init__(self):
        self.is_running = False
        self.last_command_time = 0
        self.heartbeat_timeout = 2.0  # 心跳超时时间（秒）
        
        # 遥控参数
        self.run_speed = getattr(cof.ble, 'speed_limit', 0.2)
        self.center_subtle = getattr(cof.ble, 'center_adjust_step', 0.001)
        
    def setup_server(self):
        """BLE服务器通过ble_gatt_server模块启动，此方法保留兼容性"""
        logger.info("BLE服务器通过ble_gatt_server模块启动")
        return True
    
    def process_command(self, command_data: Dict[str, Any]):
        """处理遥控指令"""
        try:
            cmd_type = command_data.get("cmd", "")
            
            if cmd_type == "move":
                # 运动控制指令
                x_vel = command_data.get("x", 0.0)
                y_vel = command_data.get("y", 0.0)
                z_vel = command_data.get("z", 0.0)
                
                # 限制速度范围
                x_vel = max(-self.run_speed, min(self.run_speed, x_vel))
                y_vel = max(-self.run_speed, min(self.run_speed, y_vel))
                z_vel = max(-2*self.run_speed, min(2*self.run_speed, z_vel))
                
                cof.commands[0] = x_vel  # 前进后退
                cof.commands[1] = y_vel  # 左右移动
                cof.commands[2] = z_vel  # 旋转
                
            elif cmd_type == "button":
                # 按键指令（兼容现有433MHz遥控器功能）
                button = command_data.get("button", 0)
                self.process_button_command(button)
                
            elif cmd_type == "center_adjust":
                # 重心调节
                adjust = command_data.get("adjust", 0.0)
                if adjust > 0:
                    cof.center_x += self.center_subtle
                elif adjust < 0:
                    cof.center_x -= self.center_subtle
                    
            elif cmd_type == "stop":
                # 停止所有运动
                cof.commands[0] = 0.0
                cof.commands[1] = 0.0
                cof.commands[2] = 0.0
                
            elif cmd_type == "ping":
                # 心跳包
                pass
                
        except Exception as e:
            logger.error(f"指令处理错误: {e}")
    
    def process_button_command(self, button: int):
        """处理按键指令（兼容433MHz遥控器）"""
        if button == 1:      # 前进
            cof.commands[0] = self.run_speed
        elif button == 2:    # 后退
            cof.commands[0] = -self.run_speed
        elif button == 3:    # 左移
            cof.commands[1] = self.run_speed
        elif button == 4:    # 右移
            cof.commands[1] = -self.run_speed
        elif button == 7:    # 左转
            cof.commands[2] = -(2*self.run_speed)
        elif button == 9:    # 右转
            cof.commands[2] = (2*self.run_speed)
        elif button == 5:    # 重心微调
            cof.center_x += self.center_subtle
        else:                # 停止
            cof.commands[0] = 0.0
            cof.commands[1] = 0.0
            cof.commands[2] = 0.0
    
    def send_status(self):
        """发送机器人状态信息（由BLE GATT服务器处理）"""
        # BLE GATT通过特征值读取状态，无需主动发送
        pass
    
    def heartbeat_monitor(self):
        """心跳监控线程（由BLE GATT服务器处理）"""
        # BLE GATT服务器有自己的心跳监控机制
        pass
    
    def status_broadcast_loop(self):
        """状态广播循环（由BLE GATT服务器处理）"""
        # BLE GATT通过特征值通知状态变化
        pass
    
    def start_server(self):
        """启动遥控服务器（实际由BLE GATT服务器处理）"""
        logger.info("遥控服务通过BLE GATT服务器启动")
        self.is_running = True
        self.last_command_time = time.time()
        return True
    
    def stop_server(self):
        """停止遥控服务器"""
        logger.info("正在停止遥控服务器...")
        self.is_running = False
        
        # 停止所有运动
        cof.commands[0] = 0.0
        cof.commands[1] = 0.0
        cof.commands[2] = 0.0

# 全局遥控服务器实例
remote_server = RemoteControlServer()

def start_ble_server_thread():
    """在新线程中启动BLE GATT遥控服务器"""
    try:
        import ble_gatt_server
        if ble_gatt_server.BLE_AVAILABLE:
            logger.info("启动BLE GATT服务器...")
            return ble_gatt_server.start_ble_gatt_server_thread()
        else:
            logger.error("BLE GATT服务器不可用，请安装相关依赖库")
            return None
    except ImportError as e:
        logger.error(f"BLE GATT服务器导入失败: {e}")
        logger.error("请安装: pip3 install bluez-peripheral")
        return None

def stop_ble_server():
    """停止遥控服务器"""
    remote_server.stop_server()

# 测试代码
if __name__ == "__main__":
    try:
        print("启动BLE GATT遥控服务器测试...")
        thread = start_ble_server_thread()
        if thread:
            print("BLE GATT服务器已启动，按Ctrl+C退出...")
            while True:
                time.sleep(1)
        else:
            print("BLE GATT服务器启动失败")
    except KeyboardInterrupt:
        print("\n用户中断，正在停止服务器...")
        remote_server.stop_server()
    except Exception as e:
        print(f"测试失败: {e}")