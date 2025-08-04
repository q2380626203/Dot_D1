#!/usr/bin/env python3
"""
真正的BLE GATT服务器
使用Bluetooth Low Energy (BLE) 协议
"""

import asyncio
import json
import logging
import time
import threading
from typing import Dict, Any

try:
    from bluez_peripheral.gatt.service import Service
    from bluez_peripheral.gatt.characteristic import characteristic, CharacteristicFlags as CharFlags
    from bluez_peripheral.advert import Advertisement
    from bluez_peripheral.agent import NoIoAgent
    from bluez_peripheral.util import *
    BLE_AVAILABLE = True
    print("✓ BLE GATT库可用")
except ImportError as e:
    BLE_AVAILABLE = False
    print(f"✗ BLE GATT库不可用: {e}")

import Dot_D1_config as cof

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Dot_D1_BLE_Service(Service):
    """Dot_D1机器人BLE GATT服务"""
    
    def __init__(self):
        # 定义服务UUID
        self.service_uuid = "12345678-1234-1234-1234-123456789abc"
        super().__init__(self.service_uuid, True)
        
        self.last_command_time = time.time()
        self.heartbeat_timeout = 2.0
        
        # 遥控参数
        self.run_speed = getattr(cof.ble, 'speed_limit', 0.2)
        self.center_subtle = getattr(cof.ble, 'center_adjust_step', 0.001)
        
        logger.info("BLE GATT服务初始化完成")
    
    @characteristic("87654321-4321-4321-4321-cba987654321", CharFlags.WRITE)
    def command_char(self, options):
        """接收控制指令的特征值"""
        def write_callback(value, offset):
            try:
                command_str = bytes(value).decode('utf-8')
                command_data = json.loads(command_str)
                self.process_command(command_data)
                self.last_command_time = time.time()
                logger.info(f"收到BLE指令: {command_data}")
            except Exception as e:
                logger.error(f"BLE指令处理错误: {e}")
        
        return write_callback
    
    @characteristic("11111111-2222-3333-4444-555555555555", CharFlags.READ | CharFlags.NOTIFY)
    def status_char(self, options):
        """发送状态信息的特征值"""
        def read_callback(offset):
            try:
                status_data = {
                    "type": "status",
                    "timestamp": time.time(),
                    "commands": cof.commands.copy(),
                    "center_x": getattr(cof, 'center_x', 0.0),
                    "motor_angle_exceed": getattr(cof.real, 'motor_angle_exceed', 0),
                    "imu_angle_exceed": getattr(cof.real, 'imu_angle_exceed', 0),
                    "connection_type": "ble"
                }
                
                status_json = json.dumps(status_data)
                return status_json.encode('utf-8')
            except Exception as e:
                logger.error(f"状态生成错误: {e}")
                return b'{"error":"status_error"}'
        
        return read_callback
    
    def process_command(self, command_data: Dict[str, Any]):
        """处理BLE控制指令"""
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
            logger.error(f"BLE指令处理错误: {e}")
    
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

class BLE_Server:
    """BLE服务器管理类"""
    
    def __init__(self):
        self.service = None
        self.advertisement = None
        self.is_running = False
        
    async def setup_ble_server(self):
        """设置BLE服务器"""
        try:
            if not BLE_AVAILABLE:
                raise ImportError("BLE库不可用")
            
            # 创建服务
            self.service = Dot_D1_BLE_Service()
            
            # 创建广告
            self.advertisement = Advertisement(
                localName="Dot_D1_Robot",
                serviceUUIDs=[self.service.service_uuid],
                appearance=0x0000,  # 通用设备
                timeout=0  # 永不超时
            )
            
            logger.info("BLE服务器设置完成")
            return True
            
        except Exception as e:
            logger.error(f"BLE服务器设置失败: {e}")
            return False
    
    async def start_server(self):
        """启动BLE服务器"""
        try:
            if not await self.setup_ble_server():
                return False
            
            self.is_running = True
            
            print("✓ BLE GATT服务器已启动")
            print(f"  设备名: Dot_D1_Robot")
            print(f"  服务UUID: {self.service.service_uuid}")
            print("  等待BLE客户端连接...")
            
            # 启动代理和服务
            agent = NoIoAgent()
            
            # 获取D-Bus连接
            bus = await get_message_bus()
            
            # 注册服务和广告
            await self.service.register(bus)
            await self.advertisement.register(bus)
            
            logger.info("BLE服务已注册并开始广告")
            
            # 启动心跳监控
            asyncio.create_task(self.heartbeat_monitor())
            
            # 保持服务器运行
            while self.is_running:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"BLE服务器启动失败: {e}")
            return False
        finally:
            await self.stop_server()
        
        return True
    
    async def heartbeat_monitor(self):
        """心跳监控"""
        while self.is_running:
            try:
                # 检查心跳超时
                if (time.time() - self.service.last_command_time > self.service.heartbeat_timeout):
                    # 超时时自动停止运动
                    if any(cmd != 0 for cmd in cof.commands):
                        logger.warning("BLE心跳超时，停止运动")
                        cof.commands[0] = 0.0
                        cof.commands[1] = 0.0
                        cof.commands[2] = 0.0
                
                await asyncio.sleep(0.5)  # 每500ms检查一次
            except Exception as e:
                logger.error(f"BLE心跳监控错误: {e}")
                await asyncio.sleep(1.0)
    
    async def stop_server(self):
        """停止BLE服务器"""
        logger.info("正在停止BLE服务器...")
        self.is_running = False
        
        try:
            if self.advertisement:
                await self.advertisement.unregister()
            if self.service:
                await self.service.unregister()
        except:
            pass
        
        # 停止所有运动
        cof.commands[0] = 0.0
        cof.commands[1] = 0.0
        cof.commands[2] = 0.0

# 全局BLE服务器实例
ble_server = BLE_Server()

def start_ble_gatt_server_thread():
    """在新线程中启动BLE GATT服务器"""
    def run_server():
        try:
            # 创建新的事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # 运行BLE服务器
            loop.run_until_complete(ble_server.start_server())
        except Exception as e:
            logger.error(f"BLE服务器线程错误: {e}")
    
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    logger.info("BLE GATT服务器线程已启动")
    return thread

def stop_ble_gatt_server():
    """停止BLE GATT服务器"""
    asyncio.create_task(ble_server.stop_server())

# 测试代码
if __name__ == "__main__":
    async def main():
        try:
            print("启动BLE GATT服务器测试...")
            await ble_server.start_server()
        except KeyboardInterrupt:
            print("\n用户中断，正在停止服务器...")
            await ble_server.stop_server()
        except Exception as e:
            print(f"测试失败: {e}")
    
    # 运行测试
    if BLE_AVAILABLE:
        asyncio.run(main())
    else:
        print("BLE库不可用，无法启动GATT服务器")
        print("请安装: pip3 install bluez-peripheral")